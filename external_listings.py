#!/usr/bin/env python3
"""Indexa páginas públicas de perfumaria/Droper com dados JSON-LD e condições de acesso."""
import hashlib
import html as html_module
import json
import os
import re
import time
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from monitor import Parser, objects, permitted as old_permitted, price, read, write

ROOT=Path(__file__).resolve().parent
USER_AGENT="MaisonPrive-Radar/2.0 (personal comparison; respects robots.txt)"
APPROVED={
 "droper.app":("https://droper.app",),
 "www.dlimport.com.br":("https://www.dlimport.com.br", "https://dlimport.com.br"),
 "dlimport.com.br":("https://dlimport.com.br", "https://www.dlimport.com.br"),
}
PHOTO_HOSTS={
 "us-southeast-1.linodeobjects.com","droper-lapse.us-southeast-1.linodeobjects.com",
 "acdn-us.mitiendanube.com","cdn.shopify.com"
}
MAX_PER_RUN=4
MAX_PARTNER_ITEMS=9000
NICHES=[
 "Parfums de Marly","Maison Francis Kurkdjian","Maison Crivelli","Fragrance Du Bois",
 "Stephane Humbert Lucas","Boadicea the Victorious","Clive Christian","Ormonde Jayne",
 "BDK Parfums","Matiere Premiere","Montale","Mancera","Nishane","Xerjoff",
 "Amouage","Initio","Sospiro","Creed","Byredo","Kilian","Memo Paris",
 "Tiziana Terenzi","Roja","Casamorati","Bond No.9","Frederic Malle",
 "Maison Margiela","Tom Ford","Vilhelm Parfumerie","Gritti"
]
ARABIC=[
 "Maison Alhambra","Al Wataniah","French Avenue","Fragrance World",
 "Lattafa","Armaf","Afnan","Rasasi","Orientica","Al Haramain",
 "Ard Al Zaafaran","Khadlaj","Ajmal","Swiss Arabian"
]
DESIGNER=[
 "Carolina Herrera","Jean Paul Gaultier","Dolce & Gabbana","Giorgio Armani",
 "Yves Saint Laurent","Paco Rabanne","Calvin Klein","Issey Miyake",
 "Hugo Boss","Valentino","Givenchy","Lancôme","Lancome","Prada",
 "Versace","Burberry","Chanel","Dior","Gucci","Hermès","Hermes",
 "Jimmy Choo","Jo Malone","Montblanc","Bvlgari","Loewe","Moschino"
]
def first_image(v):
    if isinstance(v,list):
        for item in v:
            u=first_image(item)
            if u:return u
    if isinstance(v,dict):return first_image(v.get("url") or v.get("contentUrl"))
    if isinstance(v,str):
        try:
            p=urllib.parse.urlsplit(v)
            if p.scheme=="https" and p.hostname in PHOTO_HOSTS:return v
        except ValueError:pass
    return None
def brand_name(obj,name):
    brand=obj.get("brand")
    if isinstance(brand,dict):brand=brand.get("name")
    if isinstance(brand,str) and brand.strip():return html_module.unescape(brand.strip())[:110]
    check=re.sub(r"\s+"," ",html_module.unescape(str(name))).casefold()
    for candidate in sorted(NICHES+ARABIC+DESIGNER,key=len,reverse=True):
        if check.startswith(candidate.casefold()+" ") or check.startswith("perfume "+candidate.casefold()+" "):
            return candidate
    return "Marca não identificada"
def classification(name,brand,listed_category):
    if listed_category not in ("Perfumes","Perfumes de nicho","Perfumes árabes"):
        return listed_category
    b=brand.casefold()
    if b in {v.casefold() for v in NICHES}:return "Perfumes de nicho"
    if b in {v.casefold() for v in ARABIC}:return "Perfumes árabes"
    if b in {v.casefold() for v in DESIGNER}:return "Perfumes designer"
    return listed_category
def fragrance_meta(name):
    n=html_module.unescape(name)
    match=re.search(r"\b(\d{1,3}(?:[.,]\d+)?)\s*(?:ml|mL)\b",n,re.I)
    volume=float(match.group(1).replace(",",".")) if match else None
    norm=n.casefold()
    concentration=None
    for pattern,label in [
        (r"\bextrait\b|\bextract\b", "Extrait"),
        (r"\belixir\b", "Elixir"),
        (r"\beau\s+de\s+parfum\b|\bedp\b","EDP"),
        (r"\beau\s+de\s+toilette\b|\bedt\b","EDT"),
        (r"\beau\s+de\s+cologne\b|\bedc\b|\bcologne\b","Cologne"),
        (r"\bparfum\b","Parfum")
    ]:
        if re.search(pattern,norm,re.I):concentration=label;break
    return volume,concentration
def robot_policy(url):
    """Falha fechada e cache por host durante cada execução."""
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.hostname not in APPROVED or p.username or p.password:return False,"host"
    if p.hostname not in robot_policy.cache:
        import urllib.robotparser, urllib.request
        rp=urllib.robotparser.RobotFileParser()
        try:
            req=urllib.request.Request("https://"+p.hostname+"/robots.txt",headers={"User-Agent":USER_AGENT})
            with urllib.request.urlopen(req,timeout=15) as r:
                if r.status!=200:return False,"robots HTTP "+str(r.status)
                rp.parse(r.read(300000).decode("utf-8","replace").splitlines())
            robot_policy.cache[p.hostname]=rp
        except Exception as exc:return False,"robots "+type(exc).__name__
    rp=robot_policy.cache[p.hostname]
    allowed=rp.can_fetch(USER_AGENT,url)
    return allowed,"robots" if allowed else "robots disallow"
robot_policy.cache={}
class StayOnApprovedHost(__import__("urllib.request",fromlist=["HTTPRedirectHandler"]).HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,url):
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or p.hostname not in APPROVED:raise ValueError("redirect out of approved hosts")
        return super().redirect_request(req,fp,code,msg,headers,url)
def download(url):
    import urllib.request
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.hostname not in APPROVED:raise ValueError("unapproved store")
    opener=urllib.request.build_opener(StayOnApprovedHost())
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"text/html"})
    with opener.open(req,timeout=23) as r:
        if "text/html" not in r.headers.get("Content-Type",""):raise ValueError("non HTML")
        raw=r.read(1900001)
        if len(raw)>1900000:raise ValueError("page too big")
        return raw.decode("utf-8","replace")
def parse_html(markup,source,when):
    parser=Parser();parser.feed(markup)
    out={}
    for obj in objects(parser.ld):
        typ=obj.get("@type")
        if not (typ=="Product" or isinstance(typ,list) and "Product" in typ):continue
        raw_name=obj.get("name")
        if not isinstance(raw_name,str) or not raw_name.strip():continue
        name=html_module.unescape(raw_name.strip())[:210]
        image=first_image(obj.get("image"))
        if not image:continue
        offers=obj.get("offers",{})
        if isinstance(offers,list):offers=next((o for o in offers if isinstance(o,dict) and str(o.get("priceCurrency","")).upper()=="BRL"),{})
        if not isinstance(offers,dict) or str(offers.get("priceCurrency","")).upper()!="BRL":continue
        if str(offers.get("availability","")).lower().endswith("outofstock"):continue
        offer_type=str(offers.get("@type","")).lower()
        basis="from" if "aggregateoffer" in offer_type else "listed"
        amount=price(offers.get("lowPrice") if basis=="from" else offers.get("price"))
        if amount is None:continue
        url=obj.get("url") or offers.get("url")
        if not isinstance(url,str):continue
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or p.hostname not in source["product_hosts"] or p.username or p.password:continue
        key=hashlib.sha256((source["id"]+"|"+p.netloc+p.path).encode()).hexdigest()[:20]
        pid="ext-"+key
        brand=brand_name(obj,name)
        volume,concentration=fragrance_meta(name) if source["category"].startswith("Perfumes") else (None,None)
        category=classification(name,brand,source["category"])
        record={
          "id":pid,"name":name,"brand":brand,"shop":source["name"],
          "category":category,"price":amount,"currency":"BRL",
          "url":url,"image":image,"priceBasis":basis,
          "volumeMl":volume,"concentration":concentration,
          "source":"Public store structured Product data",
          "checkedAt":when,"firstSeenAt":when,
          "sourceId":source["id"]
        }
        out[pid]=record
    return list(out.values())
def run():
    cfg=read("external_sources.json",{"sources":[]})
    sources=cfg.get("sources",[])
    state=read("data/external-progress.json",{"cursor":0})
    old=read("data/catalog.json",{"products":[]})
    catalog={p["id"]:p for p in old.get("products",[]) if isinstance(p,dict) and p.get("id")}
    cursor=int(state.get("cursor",0))%len(sources) if sources else 0
    when=datetime.now(timezone.utc).isoformat()
    statuses=[];confirmed=0;added=0;processed=0
    for offset in range(min(MAX_PER_RUN,len(sources))):
        item=sources[(cursor+offset)%len(sources)]
        url=item.get("url","")
        permitted,why=robot_policy(url)
        processed+=1
        if not permitted:
            statuses.append({"source":item.get("id"),"status":why});continue
        try:
            time.sleep(2)
            found=parse_html(download(url),item,when)
            for p in found:
                previous=catalog.get(p["id"])
                if previous:
                    hist=previous.get("history",[])
                    if not isinstance(hist,list):hist=[]
                    if not hist or previous.get("price")!=p["price"]:
                        hist=(hist+[{"at":when,"price":p["price"]}])[-65:]
                    p["history"]=hist
                    p["firstSeenAt"]=previous.get("firstSeenAt",when)
                    if p["brand"]=="Marca não identificada" and previous.get("brand") not in (None,"Marca não identificada"):
                        p["brand"]=previous["brand"]
                else:
                    added+=1;p["history"]=[{"at":when,"price":p["price"]}]
                catalog[p["id"]]=p
            confirmed+=len(found)
            statuses.append({"source":item["id"],"status":"ok","verified":len(found)})
        except urllib.error.HTTPError as e:
            statuses.append({"source":item["id"],"status":"HTTP "+str(e.code)})
        except Exception as e:
            statuses.append({"source":item["id"],"status":type(e).__name__})
    now=datetime.now(timezone.utc)
    threshold=now-timedelta(days=45)
    rows=[]
    for p in catalog.values():
        try:
            checked=datetime.fromisoformat(p.get("checkedAt",""))
            if checked.tzinfo is None:continue
            if checked<threshold:continue
        except (ValueError,TypeError):continue
        rows.append(p)
    rows.sort(key=lambda p:(p.get("checkedAt",""),p.get("id","")),reverse=True)
    rows=rows[:MAX_PARTNER_ITEMS]
    write("data/catalog.json",{
       "updatedAt":when,"source":"Original shop photographs; verified BRL product listings",
       "verifiedThisRun":confirmed,"catalogSize":len(rows),"products":rows
    })
    write("data/external-progress.json",{
       "cursor":(cursor+processed)%len(sources) if sources else 0,
       "lastRunAt":when,"verifiedThisRun":confirmed,"addedThisRun":added,"catalogSize":len(rows),
       "status":statuses
    })
    print("External sources:",confirmed,"verified, new",added,"catalog",len(rows))
    for s in statuses:print("External source",json.dumps(s,ensure_ascii=False))
    if confirmed==0:print("::warning title=No additional offers::No new external prices confirmed in this run")
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f:
            f.write("\n## Outras lojas: perfumes, streetwear e sneakers\n")
            f.write("- Produtos verificados nesta execução: **"+str(confirmed)+"**\n")
            f.write("- Produtos novos: **"+str(added)+"**\n")
            for record in statuses:f.write("- "+record["source"]+": "+record["status"]+"\n")
if __name__=="__main__":run()
