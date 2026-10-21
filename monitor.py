#!/usr/bin/env python3
"""Monitor horário conservador: somente HTTPS permitido, robots.txt e preços BRL estruturados."""
import json, os, re, time, urllib.request, urllib.parse, urllib.robotparser, urllib.error
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "MaisonPrive-Radar/1.0 (respects robots.txt)"
HOSTS = {"www.farfetch.com","www.sephora.com.br","www.oqvestir.com.br","www.birkenstock.com.br"}
ROBOTS_CACHE = {}
def read(path, default):
    try: return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, ValueError): return default
def write(path, value):
    dest=ROOT/path; dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.meta={}; self.ld=[]; self.capture=False; self.buf=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="meta":
            name=(a.get("property") or a.get("name") or "").lower()
            if name and a.get("content"): self.meta[name]=a["content"]
        if tag=="script" and "ld+json" in (a.get("type") or "").lower():
            self.capture=True; self.buf=[]
    def handle_data(self,data):
        if self.capture:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=="script" and self.capture:
            self.capture=False
            try:self.ld.append(json.loads("".join(self.buf)))
            except ValueError:pass
def price(v):
    if v is None or isinstance(v,(dict,list,bool)):return None
    s=str(v).replace("R$","").strip().replace(" ","")
    if not re.fullmatch(r"[0-9.,]+",s):return None
    if "," in s and "." in s:s=s.replace(".","").replace(",",".") if s.rfind(",")>s.rfind(".") else s.replace(",","")
    elif "," in s:s=s.replace(",",".") if len(s.split(",")[-1])<=2 else s.replace(",","")
    elif "." in s and len(s.split(".")[-1])==3:s=s.replace(".","")
    try:
        v=Decimal(s)
        return float(v) if Decimal("5")<=v<=Decimal("100000") else None
    except InvalidOperation:return None
def objects(o):
    if isinstance(o,list):
        for v in o:yield from objects(v)
    elif isinstance(o,dict):
        yield o
        for v in o.values():
            if isinstance(v,(dict,list)):yield from objects(v)
def extract(html):
    p=Parser();p.feed(html)
    for n in objects(p.ld):
        t=n.get("@type")
        if (isinstance(t,str) and t.lower()=="product") or (isinstance(t,list) and "Product" in t):
            offers=n.get("offers",[])
            for o in offers if isinstance(offers,list) else [offers]:
                if isinstance(o,dict) and str(o.get("priceCurrency","")).upper()=="BRL":
                    v=price(o.get("price") or o.get("lowPrice"))
                    if v is not None:return v
    currency=p.meta.get("product:price:currency",p.meta.get("og:price:currency",""))
    value=p.meta.get("product:price:amount",p.meta.get("og:price:amount"))
    return price(value) if currency.upper()=="BRL" else None
def permitted(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.hostname not in HOSTS or p.username or p.password:return False,"host"
    if p.hostname not in ROBOTS_CACHE:
        robots=urllib.robotparser.RobotFileParser()
        try:
            req=urllib.request.Request(f"https://{p.hostname}/robots.txt",headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=12) as r:
                if r.status!=200:return False,"robots"
                robots.parse(r.read(250000).decode("utf-8","replace").splitlines())
            ROBOTS_CACHE[p.hostname]=robots
        except Exception:return False,"robots_unavailable"
    return ROBOTS_CACHE[p.hostname].can_fetch(UA,url),"robots"
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"})
    with urllib.request.urlopen(req,timeout=18) as r:
        if urllib.parse.urlsplit(r.geturl()).hostname not in HOSTS:raise ValueError("redirect")
        if "html" not in r.headers.get("Content-Type","").lower():raise ValueError("not html")
        raw=r.read(2000001)
        if len(raw)>2000000:raise ValueError("too large")
        return raw.decode("utf-8","replace")
def main():
    watch=read("watchlist.json",[])
    db=read("data/prices.json",{"products":{}})
    if not isinstance(db,dict) or not isinstance(db.get("products"),dict):db={"products":{}}
    events=read("data/events.json",[])
    if not isinstance(events,list):events=[]
    checked=0;drops=0;now=datetime.now(timezone.utc).isoformat()
    for item in watch:
        url=item.get("url","");pid=item.get("id","")
        if not pid or not url:continue
        ok,why=permitted(url)
        if not ok:print(pid,"not checked:",why);continue
        try:
            page_html=fetch(url)
            v=extract(page_html)
        except urllib.error.HTTPError as e:
            print(pid, "fetch blocked/error HTTP", e.code);continue
        except Exception as e:
            print(pid,"fetch unavailable:",type(e).__name__);continue
        if v is None:print(pid,"BRL price not found");continue
        old=db["products"].get(pid,{})
        previous=old.get("price")
        history=old.get("history",[])
        if not history or previous!=v:history=(history+[{"price":v,"at":now}])[-120:]
        # Somente imagens declaradas pela própria página do produto; nunca gerar substitutas.
        photo=None
        try:
            # Reaproveita metadados da resposta validada de preço.
            page=Parser()
            page.feed(page_html)
            candidate=page.meta.get("og:image") or page.meta.get("twitter:image")
            if isinstance(candidate,str) and candidate.startswith("https://"):
                photo=candidate
        except Exception:
            pass
        record={**old,**item,"price":v,"checkedAt":now,"history":history,"source":"jsonld-or-meta"}
        if photo:
            record["image"]=photo
        db["products"][pid]=record
        checked+=1
        if isinstance(previous,(int,float)) and v<previous:
            drops+=1;events.append({"id":pid,"previous":previous,"current":v,"at":now,"percent":round(100*(previous-v)/previous,2)})
            print(pid,"confirmed price drop",previous,"->",v)
        else:print(pid,"verified BRL",v)
        time.sleep(2)
    db["lastRunAt"]=now;db["successfulChecks"]=checked;db["dropsDetected"]=drops
    write("data/prices.json",db);write("data/events.json",events[-200:])
    print(f"Completed: {checked} verified, {drops} drops")
    summary_path=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path,"a",encoding="utf-8") as fp:
            fp.write("## Maison Privé · Resultado do Radar\\n\\n")
            fp.write(f"- Produtos verificados com preço em BRL: **{checked}**\\n")
            fp.write(f"- Quedas confirmadas: **{drops}**\\n")
            fp.write(f"- Produtos na lista: **{len(watch)}**\\n")
            if checked==0:fp.write("\\n**Atenção:** nenhum preço pôde ser confirmado. A loja pode estar bloqueando consultas automáticas; não houve atualização de preços.\\n")
    if checked==0:print("::warning title=Sem preços confirmados::O robô executou, mas nenhuma loja forneceu um preço verificável. Não há queda confirmada.")
if __name__=="__main__":main()
