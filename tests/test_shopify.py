import unittest
from shopify_radar import money,parse_products

class ShopifyTest(unittest.TestCase):
 def test_parse_product(self):
  data={"products":[{"title":"Classic Flap","handle":"classic-flap","vendor":"Chanel","variants":[{"id":1234567,"price":"12000.50","available":True}],"images":[{"src":"https://cdn.shopify.com/x.jpg"}]}]}
  p=parse_products(data,"gringa.com.br","Gringa",8)[0]
  self.assertEqual(p["price"],12000.50)
  self.assertEqual(p["currency"],"BRL")
  self.assertTrue(p["url"].startswith("https://gringa.com.br/products/classic-flap?variant="))
 def test_sold_out(self):
  self.assertEqual(parse_products({"products":[{"handle":"sold-out","variants":[{"id":1,"price":"123","available":False}]}]},"gringa.com.br","Gringa",8),[])
 def test_bad_input(self):
  with self.assertRaises(ValueError):parse_products({"x":[]},"gringa.com.br","Gringa",8)
 def test_money(self):
  self.assertIsNone(money("R$ 1.000,00"))
  self.assertEqual(money("1290.99"),1290.99)
if __name__=="__main__":unittest.main()
