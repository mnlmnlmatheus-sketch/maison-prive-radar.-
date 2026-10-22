#!/usr/bin/env python3
"""Publica estatísticas e ofertas com desconto demonstrável, jamais percentual inventado."""
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from monitor import read,write
ROOT=Path(__file__).resolve().parents[1]
def eligible(now,p):
    if not isinstance(p,dict) or p.get("currency")!="BRL":return False
    try:
        at=datetime.fromisoformat(p["checkedAt"])
        return at.tzinfo is not None and now-at<=timedelta(days=14)
    except (ValueError,TypeError,KeyError):return False
def build():
    catalog=read("data/catalog.json",{"products":[]})
    prices=read("data/prices.json",{"products":{}})
    raw=[*catalog.get("products",[]),*prices.get("products",{}).values()]
    now=datetime.now(timezone.utc)
    products={}
    for p in raw:
        if not isinstance(p,dict) or not p.get("id"):continue
        previous=products.get(p["id"])
        if not previous or str(p.get("checkedAt",""))>str(previous.get("checkedAt","")):products[p["id"]]=p
    current=[p for p in products.values() if eligible(now,p)]
    brands={p.get("brand") for p in products.values() if p.get("brand") and p["brand"]!="Marca não identificada"}
    shops={p.get("shop") for p in products.values() if p.get("shop")}
    cats={}
    for p in products.values():
        cat=p.get("category") or "Outros"
        cats[cat]=cats.get(cat,0)+1
    deals=[]
    for p in current:
        try:
            current_price=float(p.get("price",0))
            original=float(p.get("originalPrice") or 0)
            if not (current_price>=5 and original>current_price and original<1_000_000):continue
        except (TypeError,ValueError):continue
        if not p.get("image") or not str(p.get("url","")).startswith("https://"):continue
        percentage=round((original-current_price)/original*100,1)
        if percentage<5:continue
        deals.append({
            "id":p["id"],"name":p.get("name"),"brand":p.get("brand"),"shop":p.get("shop"),
            "price":current_price,"originalPrice":original,"discountPercent":percentage,
            "image":p.get("image"),"url":p.get("url"),"category":p.get("category"),
            "volumeMl":p.get("volumeMl"),"concentration":p.get("concentration"),
            "checkedAt":p.get("checkedAt"),"basis":"store-listed-reference"
        })
    deals.sort(key=lambda p:(p["discountPercent"],p["originalPrice"]-p["price"]),reverse=True)
    write("data/deals.json",{"updatedAt":now.isoformat(),"basis":"Desconto anunciado pela própria loja; não comparar com preço histórico","totalVerifiedDeals":len(deals),"products":deals[:100]})
    write("data/catalog-stats.json",{
        "updatedAt":now.isoformat(),"catalogTotal":len(products),"verifiedLast14Days":len(current),
        "brandsIdentified":len(brands),"shops":sorted(shops),"categories":cats,
        "perfumeCount":sum(1 for p in products.values() if str(p.get("category","")).startswith("Perfumes")),
        "verifiedDeals":len(deals),
        "limitations":"Catálogo público em crescimento. Produtos podem estar indisponíveis e os preços no checkout podem diferir."
    })
    print("Catalog summary:",len(products),"products,",len(brands),"brands,",len(deals),"verified retail offers")
    summary=__import__("os").environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f:
            f.write("\n## Melhores achados verificados\n")
            f.write("- Catálogo: **"+str(len(products))+"**\n")
            f.write("- Perfumes: **"+str(sum(1 for p in products.values() if str(p.get("category","")).startswith("Perfumes")))+"**\n")
            f.write("- Descontos anunciados com preço anterior verificável: **"+str(len(deals))+"**\n")
if __name__=="__main__":build()
