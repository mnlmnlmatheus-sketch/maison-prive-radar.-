#!/usr/bin/env python3
"""Ampliação gradual do catálogo pessoal a partir de coleções Shopify públicas e permitidas."""
import hashlib
import json
import os
import re
import time
import urllib.error
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from shopify_radar import fetch, robots_for, money, read, write, UA

ROOT=Path(__file__).resolve().parent
HOST="gringa.com.br"
CONFIG="catalog_sources.json"
LIMIT_PER_RUN=6
PRODUCTS_PER_PAGE=24
MAX_CATALOG=2500

def extract_products(payload, category, collection, when, shop="Gringa"):
    if not isinstance(payload, dict) or not isinstance(payload.get("products"),list):
        raise ValueError("not a Shopify product collection")
    items=[]
    for product in payload["products"]:
        if not isinstance(product,dict):
            continue
        handle=str(product.get("handle",""))
        if not re.fullmatch(r"[\w-]{2,150}",handle,flags=re.ASCII):
            continue
        variants=product.get("variants",[])
        if not isinstance(variants,list):continue
        v_prices=[]
        for variant in variants:
            if not isinstance(variant,dict) or variant.get("available") is False:continue
            amount=money(variant.get("price"))
            vid=str(variant.get("id",""))
            if amount is not None and vid.isdigit():
                v_prices.append((amount,vid,variant))
        if not v_prices:continue
        price,vid,variant=min(v_prices,key=lambda v:v[0])
        title=str(product.get("title","")).strip()[:190]
        if not title:continue
        image=None
        images=product.get("images") or []
        if isinstance(images,list):
            for el in images:
                if isinstance(el,dict):
                    url=str(el.get("src",""))
                    if url.startswith("https://") and (".shopify.com/" in url or ".shopifycdn.net/" in url):
                        image=url;break
        if not image:
            candidate=product.get("image",{})
            if isinstance(candidate,dict):
                url=str(candidate.get("src",""))
                if url.startswith("https://"):image=url
        if not image:
            continue  # a edição definitiva não usa fotografias sintéticas
        pid="shopify-"+hashlib.sha256((HOST+":"+vid).encode()).hexdigest()[:18]
        oldprice=money(variant.get("compare_at_price"))
        items.append({
            "id":pid,"name":title,"brand":str(product.get("vendor","")).strip()[:100] or "Outras marcas",
            "shop":shop,"category":category,"price":price,"currency":"BRL",
            "url":f"https://{HOST}/products/{handle}?variant={vid}",
            "image":image,"checkedAt":when,"firstSeenAt":when,"collection":collection,
            "source":"Shopify public catalog","originalPrice":oldprice if oldprice and oldprice>price else None,
            "tags":str(product.get("tags",""))[:250],"variantId":vid
        })
    return items

def main():
    now=datetime.now(timezone.utc)
    when=now.isoformat()
    config=read(CONFIG,{})
    sections=config.get("collections",[])
    if not isinstance(sections,list) or not sections:
        print("Catalog: no collection configuration");return
    db=read("data/catalog.json",{"products":[]})
    old={}
    for product in db.get("products",[]):
        if isinstance(product,dict) and product.get("id"):
            old[product["id"]]=product
    state=read("data/catalog-progress.json",{"cursor":0})
    cursor=int(state.get("cursor",0))%len(sections)
    statuses=[];seen=0;new_count=0;successful=0
    robots,why=robots_for(HOST)
    if not robots:
        print("::warning title=Catalog unavailable::robots.txt not accessible: "+why)
    else:
        currency=None
        for endpoint in ("meta.json","cart.js"):
            url=f"https://{HOST}/{endpoint}"
            if not robots.can_fetch(UA,url):continue
            try:
                details=json.loads(fetch(url,HOST))
                currency=str(details.get("currency","")).upper()
                if currency:break
            except urllib.error.HTTPError as exc:
                statuses.append(endpoint+": HTTP "+str(exc.code))
            except (ValueError,OSError) as exc:
                statuses.append(endpoint+": "+type(exc).__name__)
        if currency!="BRL":
            print("::warning title=Catalog currency not confirmed::Skip crawl and preserve prior catalog")
        else:
            for step in range(min(LIMIT_PER_RUN,len(sections))):
                entry=sections[(cursor+step)%len(sections)]
                slug=str(entry.get("slug",""))
                page=int(entry.get("page",1))
                cat=str(entry.get("category","Acessórios"))
                if not re.fullmatch(r"[a-z0-9-]{3,90}",slug) or not 1<=page<=12:
                    continue
                url=f"https://{HOST}/collections/{slug}/products.json?limit={PRODUCTS_PER_PAGE}&page={page}"
                if not robots.can_fetch(UA,url):
                    statuses.append(slug+" page "+str(page)+": forbidden by robots");continue
                try:
                    time.sleep(2.5)
                    products=extract_products(json.loads(fetch(url,HOST)),cat,slug,when)
                    successful+=1;seen+=len(products)
                    for p in products:
                        previous=old.get(p["id"])
                        if previous:
                            hist=previous.get("history",[])
                            if not isinstance(hist,list):hist=[]
                            if not hist or previous.get("price")!=p["price"]:
                                hist=(hist+[{"price":p["price"],"at":when}])[-50:]
                            p["history"]=hist
                            p["firstSeenAt"]=previous.get("firstSeenAt",when)
                            if len(str(previous.get("category","")))>0 and previous["category"]!="Acessórios":
                                p["category"]=previous["category"]
                        else:
                            new_count+=1
                            p["history"]=[{"price":p["price"],"at":when}]
                        old[p["id"]]=p
                    statuses.append(slug+" page "+str(page)+": "+str(len(products))+" items")
                except urllib.error.HTTPError as exc:
                    statuses.append(slug+" page "+str(page)+": HTTP "+str(exc.code))
                    if exc.code in (403,429):
                        break  # bloquear repetidas tentativas quando a loja limita acesso
                except Exception as exc:
                    statuses.append(slug+" page "+str(page)+": "+type(exc).__name__)
            if successful>0:
                state["cursor"]=(cursor+successful)%len(sections)
    # Retain only 30 days since last real observation and never claim old records are fresh
    threshold=now-timedelta(days=30)
    items=[]
    for p in old.values():
        try:
            if datetime.fromisoformat(p.get("checkedAt",""))<threshold:continue
        except (ValueError,TypeError):continue
        items.append(p)
    items.sort(key=lambda x:(x.get("checkedAt",""),x.get("id","")),reverse=True)
    items=items[:MAX_CATALOG]
    write("data/catalog.json",{
        "updatedAt":when,"source":"Store product photographs and public BRL prices",
        "verifiedThisRun":seen,"catalogSize":len(items),"successfulPages":successful,
        "products":items
    })
    write("data/catalog-progress.json",{
        "cursor":state.get("cursor",cursor),"lastRunAt":when,
        "successfulPages":successful,"verifiedThisRun":seen,"addedThisRun":new_count,
        "catalogSize":len(items),"status":statuses
    })
    print("Catalog: "+str(len(items))+" real-photo products; "+str(new_count)+" new; "+str(seen)+" seen; "+str(successful)+" pages")
    for item in statuses:print("Catalog source:",item)
    summary_path=os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path,"a",encoding="utf-8") as f:
            f.write("\n## Catálogo ampliado (fotografias reais)\n")
            f.write("- Produtos acumulados com fotos de origem: **"+str(len(items))+"**\n")
            f.write("- Adicionados nesta execução: **"+str(new_count)+"**\n")
            f.write("- Páginas públicas consultadas com sucesso: **"+str(successful)+"**\n")
    if successful==0:
        print("::warning title=Catalog preserved::No new public pages were accessible; stored products keep original verification timestamps")

if __name__=="__main__":main()
