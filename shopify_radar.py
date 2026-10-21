#!/usr/bin/env python3
"""Curadoria pessoal com preços públicos Shopify; respeita robots.txt e bloqueios."""
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "MaisonPrive-Radar/1.1 (public prices; respects robots.txt)"
MAX_BYTES = 750_000

def read(path, default):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default

def write(path, obj):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed):
        super().__init__()
        self.allowed = allowed
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        p = urllib.parse.urlsplit(newurl)
        if p.scheme != "https" or p.hostname not in self.allowed:
            raise ValueError("redirect to unapproved host")
        return super().redirect_request(request, fp, code, msg, headers, newurl)

def fetch(url, host, size=MAX_BYTES):
    allowed = {host, ("www." + host if not host.startswith("www.") else host[4:])}
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or p.hostname not in allowed or p.username or p.password:
        raise ValueError("unapproved URL")
    opener = urllib.request.build_opener(RestrictedRedirect(allowed))
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/plain;q=0.9"})
    with opener.open(request, timeout=18) as response:
        raw = response.read(size + 1)
        if len(raw) > size:
            raise ValueError("response exceeded size limit")
        return raw.decode("utf-8-sig", "replace")

def robots_for(host):
    url = "https://" + host + "/robots.txt"
    try:
        text = fetch(url, host, size=250_000)
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(text.splitlines())
        return rp, "ok"
    except Exception as exc:
        return None, "robots unavailable (" + type(exc).__name__ + ")"

def money(value):
    if value is None or isinstance(value,(dict,list,bool)):
        return None
    s = str(value).strip()
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?",s):
        return None
    try:
        d = Decimal(s)
        if Decimal("1") <= d <= Decimal("200000"):
            return float(d)
    except InvalidOperation:
        pass
    return None

def parse_products(payload, host, shop, limit):
    if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
        raise ValueError("invalid Shopify feed")
    result = []
    for product in payload["products"]:
        if not isinstance(product, dict):
            continue
        handle = product.get("handle")
        if not isinstance(handle, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{2,130}",handle):
            continue
        variants = product.get("variants",[])
        if not isinstance(variants,list):
            continue
        usable = []
        for v in variants:
            if not isinstance(v,dict) or v.get("available") is False:
                continue
            amount = money(v.get("price"))
            if amount is not None:
                usable.append((v,amount))
        if not usable:
            continue
        variant,amount = min(usable, key=lambda pair: pair[1])
        variant_id = str(variant.get("id",""))
        if not variant_id.isdigit():
            continue
        title = str(product.get("title","")).strip()[:180]
        if not title:
            continue
        key = hashlib.sha256(f"{host}:{variant_id}".encode()).hexdigest()[:18]
        images=product.get("images") or []
        image=None
        if isinstance(images,list) and images and isinstance(images[0],dict):
            candidate=images[0].get("src")
            if isinstance(candidate,str) and candidate.startswith("https://"):
                image=candidate
        result.append({
            "id":"shopify-"+key,
            "brand":str(product.get("vendor","")).strip()[:100],
            "name":title,
            "shop":shop,
            "url":f"https://{host}/products/{handle}?variant={variant_id}",
            "currency":"BRL",
            "price":amount,
            "image":image,
            "source":"Shopify public catalog",
            "variantId":variant_id,
        })
        if len(result)>=limit:
            break
    return result

def collect(config, opener=fetch):
    now = datetime.now(timezone.utc).isoformat()
    db = read("data/prices.json",{"products":{}})
    if not isinstance(db,dict) or not isinstance(db.get("products"),dict):
        db={"products":{}}
    events=read("data/events.json",[])
    if not isinstance(events,list):
        events=[]
    statuses=[]
    count=0
    drops=0
    for src in config.get("shops",[]):
        host=str(src.get("host",""))
        if host not in {"gringa.com.br"}:
            statuses.append({"shop":host,"status":"host not approved"});continue
        robots, reason=robots_for(host)
        if not robots:
            statuses.append({"shop":host,"status":reason});continue
        meta_url=f"https://{host}/meta.json"
        if not robots.can_fetch(UA,meta_url):
            statuses.append({"shop":host,"status":"meta disallowed by robots.txt"});continue
        try:
            meta=json.loads(opener(meta_url,host))
            currency=str(meta.get("currency","")).upper()
        except Exception as exc:
            statuses.append({"shop":host,"status":"currency unavailable: "+type(exc).__name__});continue
        if currency!="BRL":
            statuses.append({"shop":host,"status":"unsupported currency: "+currency});continue
        for collection in src.get("collections",[])[:2]:
            if not isinstance(collection,str) or not re.fullmatch(r"[a-z0-9-]{3,80}",collection):
                continue
            url=f"https://{host}/collections/{collection}/products.json?limit=20&page=1"
            if not robots.can_fetch(UA,url):
                statuses.append({"shop":host,"collection":collection,"status":"blocked by robots.txt"});continue
            try:
                payload=json.loads(opener(url,host))
                products=parse_products(payload,host,src.get("name",host),int(src.get("limit_per_collection",8)))
            except Exception as exc:
                statuses.append({"shop":host,"collection":collection,"status":"read failed: "+type(exc).__name__});continue
            statuses.append({"shop":host,"collection":collection,"status":"ok","verified":len(products)})
            for p in products:
                pid=p["id"];old=db["products"].get(pid,{})
                previous=old.get("price")
                history=old.get("history",[])
                if not isinstance(history,list):history=[]
                if not history or previous!=p["price"]:
                    history=(history+[{"price":p["price"],"at":now}])[-120:]
                db["products"][pid]={**p,"checkedAt":now,"history":history}
                count+=1
                if isinstance(previous,(int,float)) and previous>p["price"]:
                    drops+=1
                    events.append({"id":pid,"previous":previous,"current":p["price"],"at":now,"percent":round(100*(previous-p["price"])/previous,2)})
    db["shopifyLastRunAt"]=now
    db["shopifyVerifiedChecks"]=count
    db["shopifyDropsDetected"]=drops
    write("data/prices.json",db)
    write("data/events.json",events[-200:])
    write("data/shopify-status.json",{"lastRunAt":now,"verified":count,"status":statuses})
    print(f"Shopify: {count} confirmed BRL product prices, {drops} real drops")
    for s in statuses:
        print("Source:",json.dumps(s,ensure_ascii=False))
    summary_path=os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path,"a",encoding="utf-8") as f:
            f.write(f"\n## Shopify · Gringa\n- Preços BRL confirmados: **{count}**\n- Quedas reais: **{drops}**\n")
            for s in statuses:
                f.write(f"- {s.get('shop')} / {s.get('collection','meta')}: {s['status']}\n")
    if count==0:
        print("::warning title=Shopify sem confirmação::Fonte de preços indisponível ou bloqueada; os registros anteriores foram preservados.")

if __name__=="__main__":
    collect(read("shopify_sources.json",{"shops":[]}))
