from monitor import Parser,objects,fetch,permitted
import json,re
URL="https://www.oqvestir.com.br/tenis-unissex-samba-og-preto-241956"
CATEGORY="https://www.oqvestir.com.br/feminino/roupas/casacos-e-jaquetas/jaquetas"
for url in (URL,CATEGORY):
 allowed,why=permitted(url)
 print("DIAG URL",url,"robots",allowed,why)
 if not allowed:continue
 try:
  html=fetch(url)
  parsed=Parser();parsed.feed(html)
  meta={k:v[:130] for k,v in parsed.meta.items() if "image" in k or "title" in k}
  print("DIAG LEN",len(html),"image_meta",json.dumps(meta,ensure_ascii=False))
  for x in objects(parsed.ld):
   if x.get("@type") in ("Product","ItemList"):
    print("DIAG LD",str(x.get("@type")),"image",str(x.get("image"))[:180],"keys",list(x)[:18])
    if x.get("@type")=="ItemList":
     elements=x.get("itemListElement",[])
     print("DIAG ELEMENTS",len(elements),"first",json.dumps(elements[:2],ensure_ascii=False)[:3400])
    break
  print("DIAG LINKS PRODUCT",re.findall(r'href="([^"]+-\\d{5,8}(?:\\?[^"]*)?)"',html,re.I)[:6])
  print("DIAG SAMPLE IMG",re.findall(r'<img[^>]{0,600}>',html,re.I)[:2])
  match=re.search(r'href="[^"]+-\\d{5,8}"',html,re.I)
  if match:print("DIAG PRODUCT ANCHOR",html[max(0,match.start()-200):match.start()+450].replace("\n"," ")[:650])
 except Exception as e:print("DIAG ERROR",type(e).__name__,str(e)[:120])
