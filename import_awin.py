#!/usr/bin/env python3
"""Importa CSV autorizado da Awin; não usa scraping, bypass ou credenciais públicas."""
import csv
import gzip
import hashlib
import io
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
FEED_HOSTS = {"datafeed.api.productserve.com", "productdata.awin.com", "www.productdata.awin.com"}
MAX_BYTES = 12_000_000
MAX_PRODUCTS = 120

def field(row, *names):
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""

def amount(value):
    s = str(value or "").strip().replace("R$", "").replace(" ", "")
    if not s or not all(c.isdigit() or c in ",." for c in s):
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if len(s.rsplit(",", 1)[1]) <= 2 else s.replace(",", "")
    elif "." in s and len(s.rsplit(".", 1)[1]) == 3:
        s = s.replace(".", "")
    try:
        value = Decimal(s)
        return float(value) if Decimal("5") <= value <= Decimal("200000") else None
    except InvalidOperation:
        return None

def valid_link(link):
    try:
        p = urlsplit(link)
        return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False

def load_feed(url):
    p = urlsplit(url)
    if not valid_link(url) or p.hostname not in FEED_HOSTS:
        raise ValueError("Domínio de feed não permitido; use o link oficial Awin.")
    class Redirects:
        pass
    from urllib.request import HTTPRedirectHandler, build_opener
    class SafeRedirect(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            destination = urlsplit(newurl)
            if destination.scheme != "https" or destination.hostname not in FEED_HOSTS:
                raise ValueError("Redirecionamento do feed fora da Awin")
            return super().redirect_request(request, fp, code, msg, headers, newurl)
    opener = build_opener(SafeRedirect())
    with opener.open(Request(url, headers={"User-Agent": "MaisonPriveFeedImporter/1.0"}), timeout=45) as resp:
        binary = resp.read(MAX_BYTES + 1)
    if len(binary) > MAX_BYTES:
        raise ValueError("Feed ultrapassou limite de tamanho")
    if binary[:2] == b"\x1f\x8b":
        with gzip.GzipFile(fileobj=io.BytesIO(binary)) as file:
            binary = file.read(MAX_BYTES + 1)
    if len(binary) > MAX_BYTES:
        raise ValueError("Feed descomprimido ultrapassou limite")
    return binary.decode("utf-8-sig", "replace")

def parse_csv(content):
    sample = content[:4096]
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        delimiter = ","
    rows = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    output = {}
    for row in rows:
        row = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
        currency = field(row, "currency", "currency_code").upper()
        if currency != "BRL":
            continue
        value = amount(field(row, "search_price", "price", "store_price"))
        label = field(row, "product_name", "name", "title")
        product_id = field(row, "aw_product_id", "merchant_product_id", "product_id")
        merchant_id = field(row, "merchant_id", "merchant_name")
        target = field(row, "aw_deep_link", "merchant_deep_link", "deep_link")
        if not value or not label or not product_id or not valid_link(target):
            continue
        image = field(row, "aw_image_url", "merchant_image_url", "large_image")
        key = hashlib.sha256((merchant_id + "|" + product_id).encode()).hexdigest()[:20]
        product = {
            "id": "awin-" + key,
            "name": label[:220],
            "brand": field(row, "brand_name", "brand")[:100],
            "store": field(row, "merchant_name")[:120],
            "price": value,
            "currency": "BRL",
            "url": target,
            "source": "Awin authorized feed",
            "image": image if valid_link(image) else None,
            "productId": product_id[:85]
        }
        previous = amount(field(row, "product_price_old", "rrp_price"))
        if previous and previous > value:
            product["originalPrice"] = previous
            product["declaredDiscountPercent"] = round(100 * (previous - value) / previous, 1)
        output[product["id"]] = product
        if len(output) >= MAX_PRODUCTS:
            break
    return list(output.values())

def run():
    url = os.getenv("AWIN_FEED_URL", "").strip()
    if not url:
        print("Awin não configurada: cadastre-se e adicione AWIN_FEED_URL nos Secrets do GitHub.")
        return
    products = parse_csv(load_feed(url))
    if not products:
        print("::warning title=Feed sem produtos BRL::Não alteramos o catálogo existente.")
        return
    path = ROOT / "data/affiliate-catalog.json"
    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    old = {p["id"]: p for p in previous.get("products", [])}
    now = datetime.now(timezone.utc).isoformat()
    events = []
    for p in products:
        old_price = old.get(p["id"], {}).get("price")
        if isinstance(old_price, (float, int)) and old_price > p["price"]:
            events.append({"id": p["id"], "before": old_price, "after": p["price"], "at": now})
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"updatedAt":now,"source":"Awin authorized feed","products":products}, ensure_ascii=False, indent=2) + "\n",encoding="utf-8")
    history = ROOT / "data/affiliate-events.json"
    older = json.loads(history.read_text(encoding="utf-8")) if history.exists() else []
    history.write_text(json.dumps((older + events)[-300:], ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(f"Awin: {len(products)} produtos BRL importados; {len(events)} quedas observadas. Fonte autorizada.")
if __name__ == "__main__":
    run()
