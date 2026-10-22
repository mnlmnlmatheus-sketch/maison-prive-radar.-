#!/usr/bin/env python3
"""Curadoria pessoal The King: variantes com BRL, descontos declarados e fotos oficiais."""
import html as html_module
import json
import os
import re
import time
import urllib.error
import urllib.parse
from datetime import datetime,timezone,timedelta
from html.parser import HTMLParser
from external_listings import robot_policy,download,classification,fragrance_meta,read,write,price,NICHES,ARABIC,DESIGNER

HOST="www.thekingofparfums.com.br"
PER_RUN=3
LIMIT_TOTAL=18000
class KingParser(HTMLParser):
 def __init__(self):
  super().__init__();self.cards=[];self.card=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="div" and "js-item-product" in (a.get("class") or "") and a.get("data-product-id"):
   self.card={"productId":str(a["data-product-id"]),"variants":[],"url":None,"alt":None}
   self.cards.append(self.card)
  if not self.card:return
  if "data-variants" in a and not self.card["variants"]:
   raw=a["data-variants"]
   if len(raw)<280000:
    try:
     parsed=json.loads(raw)
     if isinstance(parsed,list):self.card["variants"]=parsed[:45]
    except (ValueError,TypeError):pass
  if tag=="a" and "/produtos/" in (a.get("href") or "") and not self.card["url"]:
   self.card["url"]=a["href"]
  if tag=="img" and a.get("alt") and not self.card["alt"]:
   alt=html_module.unescape(a["alt"].strip())
   if len(alt)>4:self.card["alt"]=alt
def parse_king(markup,category,when):
 parser=KingParser();parser.feed(markup)
 out={}
 for card in parser.cards:
  url=card.get("url")
  if not isinstance(url,str):continue
  p=urllib.parse.urlsplit(url)
  if p.scheme!="https" or p.hostname not in (HOST,"thekingofparfums.com.br") or not p.path.startswith("/produtos/"):continue
  alt=str(card.get("alt") or "").strip()[:180]
  if not alt:continue
  if " - " in alt:
   candidate=alt.split(" - ",1)[0].strip()
  else:candidate=""
  brand=candidate if 2<len(candidate)<80 else "Marca não identificada"
  for v in card["variants"]:
   if not isinstance(v,dict) or v.get("available") is not True:continue
   amount=price(v.get("price_number"))
   if amount is None:continue
   price_str=str(v.get("price_short","")).replace(" ","")
   if "R$" not in price_str:continue
   variant_id=str(v.get("id",""))
   if not variant_id.isdigit():continue
   photo=v.get("image_url")
   if not isinstance(photo,str):continue
   if photo.startswith("//"):photo="https:"+photo
   if re.search(r"imagemgerada|image-generated|generated[-_]by[-_]ai",photo,re.I):continue
   try:
    pic=urllib.parse.urlsplit(photo)
    if pic.scheme!="https" or pic.hostname!="acdn-us.mitiendanube.com":continue
   except ValueError:continue
   option=str(v.get("option0") or "").strip()[:72]
   volume,concentration=fragrance_meta(alt+" "+option)
   name=alt+" · "+option if option else alt
   pcat=classification(name,brand,category)
   old=price(v.get("compare_at_price_number"))
   originalPrice=old if old and old>amount else None
   key="king-"+variant_id
   if key in out:continue
   out[key]={
     "id":key,"name":name[:220],"brand":brand,"shop":"The King of Parfums",
     "category":pcat,"price":amount,"currency":"BRL",
     "url":url,"image":photo,"priceBasis":"listed",
     "originalPrice":originalPrice,"discountDeclared": bool(originalPrice),
     "volumeMl":volume,"concentration":concentration,
     "condition":"Sem caixa" if "s/ caixa" in option.casefold() or "sem caixa" in option.casefold() else None,
     "checkedAt":when,"firstSeenAt":when,
     "source":"Public Nuvemshop product variant pricing"
   }
 return list(out.values())
def run():
 cfg=read("king_sources.json",{"sources":[]})
 sources=cfg.get("sources",[])
 if not sources:return
 state=read("data/king-progress.json",{"cursor":0,"pages":{}})
 cursor=int(state.get("cursor",0))%len(sources)
 pages=state.get("pages",{})
 if not isinstance(pages,dict):pages={}
 db=read("data/catalog.json",{"products":[]})
 existing={item["id"]:item for item in db.get("products",[]) if isinstance(item,dict) and item.get("id")}
 now=datetime.now(timezone.utc)
 when=now.isoformat()
 status=[];added=0;checked=0;processed=0
 for offset in range(min(PER_RUN,len(sources))):
  source=sources[(cursor+offset)%len(sources)]
  slug=source.get("id","")
  base=source.get("url","")
  if not base.startswith("https://"+HOST+"/"):continue
  max_page=min(180,max(1,int(source.get("maxPages",35))))
  page_number=min(max_page,max(1,int(pages.get(slug,1))))
  separator="&" if "?" in base else "?"
  url=base+(separator+"page="+str(page_number) if page_number>1 else "")
  processed+=1
  allowed,reason=robot_policy(url)
  if not allowed:
   status.append({"source":slug,"page":page_number,"status":reason});continue
  try:
   time.sleep(2)
   results=parse_king(download(url),source.get("category","Perfumes"),when)
   count=0
   for item in results:
    old=existing.get(item["id"])
    if old:
     hist=old.get("history",[])
     if not isinstance(hist,list):hist=[]
     if not hist or old.get("price")!=item["price"]:
      hist=(hist+[{"at":when,"price":item["price"]}])[-90:]
     item["history"]=hist
     item["firstSeenAt"]=old.get("firstSeenAt",when)
    else:
     added+=1;item["history"]=[{"at":when,"price":item["price"]}]
    existing[item["id"]]=item
    count+=1
   checked+=count
   status.append({"source":slug,"page":page_number,"status":"ok","variants":count})
   pages[slug]=1 if page_number>=max_page or count==0 else page_number+1
  except urllib.error.HTTPError as e:
   status.append({"source":slug,"page":page_number,"status":"HTTP "+str(e.code)})
   if e.code in (403,429):break
  except Exception as e:
   status.append({"source":slug,"page":page_number,"status":type(e).__name__})
 items=[]
 threshold=now-timedelta(days=45)
 for item in existing.values():
  try:
   if datetime.fromisoformat(item.get("checkedAt",""))<threshold:continue
  except (TypeError,ValueError):continue
  items.append(item)
 items.sort(key=lambda p:(p.get("checkedAt",""),p.get("id","")),reverse=True)
 items=items[:LIMIT_TOTAL]
 write("data/catalog.json",{"updatedAt":when,"source":"Store structured product and variant prices",
  "verifiedThisRun":checked,"catalogSize":len(items),"products":items})
 write("data/king-progress.json",{
  "cursor":(cursor+processed)%len(sources),"pages":pages,
  "lastRunAt":when,"verifiedThisRun":checked,"addedThisRun":added,
  "catalogSize":len(items),"status":status
 })
 print("King perfume variants:",checked,"verified,",added,"new; total catalog",len(items))
 for s in status:print("King source",json.dumps(s,ensure_ascii=False))
 if checked==0:print("::warning title=King catalog preserved::No valid variants fetched; keeping historical prices")
 summary=os.environ.get("GITHUB_STEP_SUMMARY")
 if summary:
  with open(summary,"a",encoding="utf-8") as f:
   f.write("\n## The King of Parfums · Descontos por variante\n")
   f.write("- Variantes verificadas: **"+str(checked)+"**\n")
   f.write("- Novos produtos: **"+str(added)+"**\n")
   for s in status:f.write("- "+s["source"]+" página "+str(s["page"])+": "+s["status"]+"\n")
if __name__=="__main__":run()
