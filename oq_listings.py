#!/usr/bin/env python3
"""Importa produtos reais de listagens públicas com JSON-LD ItemList da OQVestir."""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
from datetime import datetime,timezone,timedelta
from pathlib import Path
from monitor import Parser,objects,permitted,fetch,price,read,write

ROOT=Path(__file__).resolve().parent
DOMAIN="www.oqvestir.com.br"
MAX_PRODUCTS=3500
PER_RUN=5
BRANDS=(
"Adidas Originals X Jennie","Adidas Originals","New Balance","The North Face",
"Tommy Hilfiger","Tommy Jeans","Armani Exchange","Calvin Klein Jeans",
"On Running","Levi's","Nike","BOSS","HUGO","Vans","Veja","Puma",
"Columbia","Lacoste","Diesel","Schutz","Arezzo","Converse","Hoka",
"Fila","Osklen","Animale","Farm Rio","Farm","John John","Reserva",
"Ralph Lauren","Coach","Luiza Barcelos","Vicenza","Capodarte",
"Ellus","Lança Perfume","Sergio K","Market 33","Basiq",
"Le Lis","New Balance","My Favorite","Michael Kors"
)
def brand_for(p):
    b=p.get("brand")
    if isinstance(b,dict):b=b.get("name")
    if isinstance(b,str) and b.strip():return b.strip()[:90]
    name=str(p.get("name","")).casefold()
    for brand in BRANDS:
        if brand.casefold() in name:return brand
    return "Marca não identificada"

def brand_map_from_html(html):
    """Une item_id e item_brand declarados na camada pública de produtos, sem adivinhar marca."""
    result={}
    expression=r'item_id:(\d{5,8})(?:(?!item_id:).){0,900}?item_brand:"([^"]{1,95})"'
    for match in re.finditer(expression,html,re.DOTALL):
        brand=match.group(2).strip()
        if brand and brand.lower() not in ("undefined","null"):
            result[match.group(1)]=brand
    return result

def parse_itemlist(html,category,when):
    parser=Parser();parser.feed(html)
    brands=brand_map_from_html(html)
    output=[]
    seen=set()
    for element in objects(parser.ld):
        if str(element.get("@type","")).lower()!="itemlist":
            continue
        entries=element.get("itemListElement",[])
        if not isinstance(entries,list):continue
        for item in entries:
            if isinstance(item,dict) and item.get("@type")=="ListItem":
                item=item.get("item",{})
            if not isinstance(item,dict):continue
            if str(item.get("@type","")).lower()!="product":continue
            name=str(item.get("name","")).strip()[:190]
            photo=item.get("image")
            if isinstance(photo,list):photo=photo[0] if photo else None
            if isinstance(photo,dict):photo=photo.get("url")
            if not isinstance(photo,str) or not photo.startswith("https://oqvestir.fbitsstatic.net/"):
                continue
            target=str(item.get("url",""))
            try:
                u=urllib.parse.urlsplit(target)
                if u.scheme!="https" or u.hostname!=DOMAIN or u.username or u.password or not name:
                    continue
            except ValueError:continue
            offers=item.get("offers",{})
            if isinstance(offers,list):offers=next((x for x in offers if isinstance(x,dict) and x.get("priceCurrency")=="BRL"),{})
            if not isinstance(offers,dict) or str(offers.get("priceCurrency","")).upper()!="BRL":
                continue
            amount=price(offers.get("price"))
            if amount is None:continue
            match=re.search(r"-(\d{5,8})$",u.path)
            key=match.group(1) if match else hashlib.sha256(u.path.encode()).hexdigest()[:13]
            pid="oqvestir-"+key
            if pid in seen:continue
            seen.add(pid)
            output.append({
                "id":pid,"name":name,"brand":brands.get(key) or brand_for(item),"shop":"OQVestir","category":category,
                "price":amount,"currency":"BRL","url":target,"image":photo,
                "checkedAt":when,"firstSeenAt":when,"source":"OQVestir category structured data"
            })
    return output

def run():
    now=datetime.now(timezone.utc);when=now.isoformat()
    cats=read("oq_categories.json",{}).get("categories",[])
    if not isinstance(cats,list) or not cats:return
    progress=read("data/oq-progress.json",{"cursor":0})
    cursor=int(progress.get("cursor",0))%len(cats)
    db=read("data/catalog.json",{"products":[]})
    existing={}
    for item in db.get("products",[]):
        if isinstance(item,dict) and item.get("id"):existing[item["id"]]=item
    status=[];saved=0;added=0;processed=0
    for offset in range(min(PER_RUN,len(cats))):
        position=(cursor+offset)%len(cats)
        category=cats[position]
        url=category.get("url","")
        cat=category.get("category","Acessórios")
        ok,reason=permitted(url)
        processed+=1
        if not ok:
            status.append({"category":cat,"url":url,"status":reason+"; not accessible"});continue
        try:
            # Uma leitura por categoria; sem automatizar paginação agressiva.
            time.sleep(1.6)
            found=parse_itemlist(fetch(url),cat,when)
            status.append({"category":cat,"url":url,"status":"ok","verified":len(found)})
            saved+=len(found)
            for item in found:
                old=existing.get(item["id"])
                if old:
                    hist=old.get("history",[])
                    if not isinstance(hist,list):hist=[]
                    if not hist or old.get("price")!=item["price"]:
                        hist=(hist+[{"at":when,"price":item["price"]}])[-60:]
                    item["history"]=hist
                    item["firstSeenAt"]=old.get("firstSeenAt",when)
                    # Preserve original brand attribution from individually verified product pages.
                    if old.get("brand") and old.get("brand")!="Marca não identificada":
                        item["brand"]=old["brand"]
                    if old.get("category") and old["category"]!="Acessórios" and cat=="Acessórios":
                        item["category"]=old["category"]
                else:
                    added+=1
                    item["history"]=[{"at":when,"price":item["price"]}]
                existing[item["id"]]=item
        except urllib.error.HTTPError as e:
            status.append({"category":cat,"url":url,"status":"HTTP "+str(e.code)})
            if e.code in (403,429):break
        except Exception as e:
            status.append({"category":cat,"url":url,"status":type(e).__name__})
    if processed:
        cursor=(cursor+processed)%len(cats)
    threshold=now-timedelta(days=30)
    items=[]
    for item in existing.values():
        try:
            if datetime.fromisoformat(item.get("checkedAt",""))<threshold:continue
        except (ValueError,TypeError):continue
        items.append(item)
    items.sort(key=lambda p:(p.get("checkedAt",""),p.get("id","")),reverse=True)
    items=items[:MAX_PRODUCTS]
    write("data/catalog.json",{"updatedAt":when,"source":"Public store structured data; original product photographs",
      "verifiedThisRun":saved,"catalogSize":len(items),"products":items})
    write("data/oq-progress.json",{"lastRunAt":when,"cursor":cursor,"verifiedThisRun":saved,
      "addedThisRun":added,"catalogSize":len(items),"status":status})
    print("OQ Catalog:",len(items),"products saved,",added,"new,",saved,"checked this run")
    for record in status:print("OQ source",json.dumps(record,ensure_ascii=False))
    summary=os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f:
            f.write("\n## OQVestir · Coleções com fotografias reais\n")
            f.write("- Produtos no catálogo: **"+str(len(items))+"**\n")
            f.write("- Com preço BRL confirmado nesta execução: **"+str(saved)+"**\n")
            f.write("- Produtos novos nesta execução: **"+str(added)+"**\n")
    if saved==0:
        print("::warning title=OQVestir category unavailable::Nenhuma categoria pública disponível; manter catálogo anterior")

if __name__=="__main__":run()
