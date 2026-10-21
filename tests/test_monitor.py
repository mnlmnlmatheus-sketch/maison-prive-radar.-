import unittest
from monitor import extract,price
class PriceTests(unittest.TestCase):
 def test_brl_product(self):
  self.assertEqual(extract('<script type="application/ld+json">{"@type":"Product","offers":{"priceCurrency":"BRL","price":"507.50"}}</script>'),507.5)
 def test_usd_rejected(self):
  self.assertIsNone(extract('<script type="application/ld+json">{"@type":"Product","offers":{"priceCurrency":"USD","price":"507.50"}}</script>'))
 def test_meta(self):
  self.assertEqual(extract('<meta property="product:price:amount" content="1.299,90"><meta property="product:price:currency" content="BRL">'),1299.9)
 def test_invalid(self):
  self.assertIsNone(price('sob consulta'))
 def test_thousands(self):
  self.assertEqual(price('R$ 2.499,00'),2499.0)
if __name__=="__main__":unittest.main()
