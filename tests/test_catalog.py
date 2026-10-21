import unittest
from catalog_expand import extract_products
class ExpandCatalogTest(unittest.TestCase):
 def setUp(self):
  self.product={"title":"Neverfull GM","handle":"neverfull-gm","vendor":"Louis Vuitton",
   "variants":[{"id":2345,"price":"5800.00","available":True,"compare_at_price":"6400.00"},
               {"id":2346,"price":"5400.00","available":False}],
   "images":[{"src":"https://cdn.shopify.com/s/files/1/original.jpg"}]}
 def test_real_photo(self):
  items=extract_products({"products":[self.product]},"Bolsas","bolsas","2026-10-21T23:00:00+00:00")
  self.assertEqual(len(items),1)
  self.assertEqual(items[0]["price"],5800.0)
  self.assertEqual(items[0]["image"],"https://cdn.shopify.com/s/files/1/original.jpg")
  self.assertEqual(items[0]["category"],"Bolsas")
  self.assertEqual(items[0]["originalPrice"],6400.)
 def test_skip_missing_photo(self):
  p=dict(self.product,images=[])
  self.assertEqual(extract_products({"products":[p]},"Bolsas","bolsas","2026-10-21T23:00:00+00:00"),[])
 def test_skip_sold_out(self):
  p=dict(self.product,variants=[{"id":2,"price":"10.00","available":False}])
  self.assertEqual(extract_products({"products":[p]},"Bolsas","bolsas","2026-10-21T23:00:00+00:00"),[])
 def test_bad_feed(self):
  with self.assertRaises(ValueError):
   extract_products({"no_products":1},"Bolsas","bolsas","2026-10-21T23:00:00+00:00")
if __name__=="__main__":unittest.main()
