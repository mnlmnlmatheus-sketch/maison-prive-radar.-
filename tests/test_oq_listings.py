import unittest
import json
from oq_listings import parse_itemlist,brand_for

class TestOQListing(unittest.TestCase):
 def setUp(self):
  self.items=[{
   "@type":"Product","name":"Jaqueta Feminina Oversized em Modal - Bege",
   "image":"https://oqvestir.fbitsstatic.net/img/p/jaqueta-feminina-261774/image.jpg?w=486",
   "url":"https://www.oqvestir.com.br/jaqueta-feminina-modal-bege-261774",
   "offers":{"@type":"Offer","priceCurrency":"BRL","price":279.99}},
   {"@type":"Product","name":"Tênis Feminino Adidas Originals Samba OG",
   "image":"https://oqvestir.fbitsstatic.net/img/p/samba-261777/im.jpg",
   "url":"https://www.oqvestir.com.br/tenis-feminino-samba-261777",
   "offers":{"priceCurrency":"BRL","price":"799.99"}}]
 def html(self,items):
  return '<script type="application/ld+json">'+json.dumps({"@context":"https://schema.org","@type":"ItemList","numberOfItems":len(items),"itemListElement":items},ensure_ascii=False)+'</script>'
 def test_many_items_with_original_photos(self):
  out=parse_itemlist(self.html(self.items),"Roupas","2026-10-21T22:00:00+00:00")
  self.assertEqual(len(out),2)
  self.assertEqual(out[0]["price"],279.99)
  self.assertEqual(out[0]["category"],"Roupas")
  self.assertEqual(out[1]["brand"],"Adidas Originals")
 def test_reject_non_brl(self):
  item=json.loads(json.dumps(self.items[0]))
  item["offers"]["priceCurrency"]="USD"
  self.assertEqual(parse_itemlist(self.html([item]),"Roupas","2026-10-21T22:00:00+00:00"),[])
 def test_reject_untrusted_photo(self):
  item=json.loads(json.dumps(self.items[0]))
  item["image"]="https://example.com/fake.jpg"
  self.assertEqual(parse_itemlist(self.html([item]),"Roupas","2026-10-21T22:00:00+00:00"),[])
 def test_deduplicate_url(self):
  self.assertEqual(len(parse_itemlist(self.html([self.items[0],self.items[0]]),"Roupas","2026-10-21T22:00:00+00:00")),1)
if __name__=="__main__":unittest.main()
