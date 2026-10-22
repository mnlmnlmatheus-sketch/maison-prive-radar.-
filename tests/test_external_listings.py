import unittest,json
from external_listings import parse_html,fragrance_meta,classification,brand_name
class ExternalListingTest(unittest.TestCase):
 def as_html(self,p):
  return '<script type="application/ld+json">'+json.dumps(p)+'</script>'
 def test_droper_niche_from_price(self):
  p={"@type":"ItemList","itemListElement":[{"@type":"Product","name":"Perfume Parfums De Marly Herod 125 ml",
   "url":"https://droper.app/d/123/perfume_marly","image":["https://us-southeast-1.linodeobjects.com/droper-media/a.webp"],
   "brand":{"name":"Parfums de Marly"},"offers":{"@type":"AggregateOffer","priceCurrency":"BRL","lowPrice":"1,800.00","availability":"https://schema.org/InStock"}}]}
  # Simular o formato de moeda realmente publicado pela Droper, sem milhares
  p["itemListElement"][0]["offers"]["lowPrice"]="1800.00"
  r=parse_html(self.as_html(p),{"id":"droper-perf","name":"Droper","category":"Perfumes","product_hosts":["droper.app"]},"2026-10-21T22:00:00+00:00")
  self.assertEqual(len(r),1)
  self.assertEqual(r[0]["priceBasis"],"from")
  self.assertEqual(r[0]["price"],1800.)
  self.assertEqual(r[0]["category"],"Perfumes de nicho")
  self.assertEqual(r[0]["volumeMl"],125.)
 def test_dl_import_sale_price(self):
  p={"@type":"Product","name":"Lattafa Asad EDP 100ml","image":"https://acdn-us.mitiendanube.com/stores/123/product.webp","offers":{"@type":"Offer","url":"https://dlimport.com.br/produtos/asad/","priceCurrency":"BRL","price":"209.99","availability":"https://schema.org/InStock"}}
  r=parse_html(self.as_html(p),{"id":"dl","name":"DL Imports","category":"Perfumes","product_hosts":["dlimport.com.br"]},"2026-10-21T22:00:00+00:00")
  self.assertEqual(len(r),1)
  self.assertEqual(r[0]["brand"],"Lattafa")
  self.assertEqual(r[0]["category"],"Perfumes árabes")
  self.assertEqual(r[0]["concentration"],"EDP")
  self.assertEqual(r[0]["priceBasis"],"listed")
 def test_no_false_discount(self):
  p={"@type":"Product","name":"Xerjoff Naxos EDP 100ml","image":"https://acdn-us.mitiendanube.com/stores/123/img.jpg","offers":{"@type":"Offer","url":"https://dlimport.com.br/produtos/naxos/","priceCurrency":"BRL","price":"1349.99"}}
  r=parse_html(self.as_html(p),{"id":"dl","name":"DL Imports","category":"Perfumes de nicho","product_hosts":["dlimport.com.br"]},"2026-10-21T22:00:00+00:00")
  self.assertNotIn("originalPrice",r[0])
 def test_ignore_out_of_stock_and_usd(self):
  p={"@type":"Product","name":"Perfume Tom Ford Tobacco Vanille 100ml","image":"https://acdn-us.mitiendanube.com/stores/123/img.jpg","offers":{"@type":"Offer","url":"https://dlimport.com.br/produtos/vanille/","priceCurrency":"BRL","price":"500","availability":"https://schema.org/OutOfStock"}}
  params={"id":"dl","name":"DL Imports","category":"Perfumes","product_hosts":["dlimport.com.br"]}
  self.assertEqual(parse_html(self.as_html(p),params,"2026-10-21T22:00:00+00:00"),[])
  p["offers"]["availability"]="https://schema.org/InStock"
  p["offers"]["priceCurrency"]="USD"
  self.assertEqual(parse_html(self.as_html(p),params,"2026-10-21T22:00:00+00:00"),[])
 def test_fragrance(self):
  self.assertEqual(fragrance_meta("Creed Aventus EDP 100ml"),(100.,"EDP"))
  self.assertEqual(fragrance_meta("Amouage Interlude 53 Extrait de Parfum 100ml"),(100.,"Extrait"))
if __name__=="__main__":unittest.main()
