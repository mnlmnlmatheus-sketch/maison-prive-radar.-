#!/usr/bin/env python3
"""Diagnóstico respeitoso de fontes de perfume e marketplace. Não contorna bloqueios."""
import json,re,urllib.request,urllib.parse,urllib.robotparser,urllib.error,time
from html.parser import HTMLParser
SITES=[
 ("King niche","https://www.thekingofparfums.com.br/nicho-exclusivo/"),
]
UA="MaisonPrive-Radar/1.2 (personal product research; respects robots.txt)"
class Inspector(HTMLParser):
 def __init__(self):
  super().__init__();self.scripts=[];self.script=False;self.b=[];self.links=[];self.meta={};self.cards=[];self.card=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="script" and "ld+json" in (a.get("type") or "").lower():self.script=True;self.b=[]
  if tag=="a" and a.get("href"):self.links.append(a["href"])
  if tag=="meta":
   key=a.get("property") or a.get("name")
   if key and a.get("content"):self.meta[key.lower()]=a["content"]
  if tag=="div" and "js-item-product" in (a.get("class") or "") and a.get("data-product-id"):
   self.card={"id":a["data-product-id"],"variants":[],"links":[],"images":[],"names":[]}
   self.cards.append(self.card)
  elif self.card and a.get("data-variants"):
   try:
    vv=json.loads(a["data-variants"])
    self.card["variants"]=[{k:v.get(k) for k in ("price_number","compare_at_price_number","promotional_price_number","available","option0","image_url","product_id","id")} for v in vv[:2]]
   except Exception as e:self.card["error"]=str(e)[:80]
  if self.card and tag=="a" and "/produtos/" in (a.get("href") or ""):
   if len(self.card["links"])<4:self.card["links"].append(a["href"])
  if self.card and tag=="img":
   if len(self.card["images"])<4:self.card["images"].append({"alt":a.get("alt"),"src":str(a.get("src") or a.get("data-src"))[:120]})

 def handle_data(self,x):
  if self.script:self.b.append(x)
  if self.card and x.strip() and len(self.card["names"])<8:self.card["names"].append(x.strip()[:110])
 def handle_endtag(self,tag):
  if tag=="script" and self.script:
   self.script=False
   try:self.scripts.append(json.loads("".join(self.b)))
   except Exception:pass
def objects(x):
 if isinstance(x,list):
  for y in x:yield from objects(y)
 elif isinstance(x,dict):
  yield x
  for v in x.values():
   if isinstance(v,(dict,list)):yield from objects(v)
def main():
 for name,url in SITES:
  try:
   parts=urllib.parse.urlsplit(url);host=parts.hostname
   roboturl="https://"+host+"/robots.txt"
   req=urllib.request.Request(roboturl,headers={"User-Agent":UA})
   with urllib.request.urlopen(req,timeout=15) as r:
    if r.status!=200:print("SRC",name,"robots",r.status);continue
    rules=r.read(250000).decode("utf-8","replace")
   rp=urllib.robotparser.RobotFileParser()
   rp.parse(rules.splitlines())
   if not rp.can_fetch(UA,url):
    print("SRC",name,"disallowed by robots.txt");continue
   time.sleep(1)
   req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"})
   with urllib.request.urlopen(req,timeout=19) as r:
    raw=r.read(1600000)
    final=urllib.parse.urlsplit(r.geturl()).hostname
    if final not in (host,host.removeprefix("www."),"www."+host):
     print("SRC",name,"unexpected redirect",final);continue
    html=raw.decode("utf-8","replace")
   p=Inspector();p.feed(html)
   found=[]
   for obj in objects(p.scripts):
    typ=obj.get("@type")
    if typ in ("ItemList","Product") or (isinstance(typ,list) and "Product" in typ):
     found.append({"type":typ,"count":len(obj.get("itemListElement",[])) if isinstance(obj.get("itemListElement"),list) else None,
                  "name":str(obj.get("name",""))[:55],"price":obj.get("offers",{}).get("price") if isinstance(obj.get("offers"),dict) else None,
                  "images":str(obj.get("image",""))[:90]})
   for x in objects(p.scripts):
    if str(x.get("@type","")).lower()=="product":
     print("DETAILED",name,json.dumps({k:v for k,v in x.items() if k in ("name","url","brand","offers","image","sku")},ensure_ascii=False)[:1950]);break
   print("SRC",name,"STATUS OK","chars",len(html),"links",len(p.links),"structured",json.dumps(found[:4],ensure_ascii=False))
   print("SAMPLE LINKS",name,json.dumps(p.links[:8],ensure_ascii=False))
   print("KING CARDS",json.dumps(p.cards[:3],ensure_ascii=False)[:6500])
   print("META",name,json.dumps({k:v[:110] for k,v in p.meta.items() if "image" in k or "title" in k},ensure_ascii=False)[:500])
   print("PRODUCT LINKS",name,json.dumps([a for a in p.links if '/produtos/' in a][:8],ensure_ascii=False)[:1700])

   import html as html_module
   m=re.search(r'<div[^>]*class="js-item-product\b[^"]*"[^>]*data-product-id="\d+"',html)
   if m:
    seg=html[m.start():m.start()+11500]
    v=re.search(r'data-variants="([^"]{10,15000})"',seg)
    if v:
     try:
      variants=json.loads(html_module.unescape(v.group(1)))
      print("KING VARIANTS",json.dumps(variants[:2],ensure_ascii=False)[:3800])
     except Exception as e:print("KING VARIANTS ERROR",str(e))
    print("KING LINKS",json.dumps(re.findall(r'<a[^>]+href="([^"]+)"[^>]*>',seg)[:8],ensure_ascii=False)[:1500])
    print("KING IMAGES",json.dumps(re.findall(r'<img[^>]{0,1200}>',seg)[:3],ensure_ascii=False)[:3000])
    print("KING NAMES",json.dumps(re.findall(r'<(?:h[1-6]|span|div|p)[^>]*class="[^"]*(?:name|title|brand)[^"]*"[^>]*>[^<]{1,130}',seg)[:9],ensure_ascii=False)[:1800])
    print("KING ATTR",seg[:1500].replace("\n"," "))

   for needle in ('data-product','js-item-product','data-store="product','<a href="/produtos/','price-compare','product-price'):
    pos=html.find(needle)
    if pos>=0:
     print("STRUCTURE",name,needle,"AT",pos,re.sub(r'\s+',' ',html[max(0,pos-140):pos+700])[:800])

  except urllib.error.HTTPError as e:print("SRC",name,"HTTP",e.code)
  except Exception as e:print("SRC",name,type(e).__name__,str(e)[:120])
if __name__=="__main__":main()
