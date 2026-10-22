import unittest,html,json
from king_listings import parse_king
class KingVariantsTest(unittest.TestCase):
 def html(self,v,alt="Xerjoff - Erba Pura"):
  variants=html.escape(json.dumps(v),quote=True)
  return ('<div class="js-item-product item-product col-grid" data-product-id="134978667">'
          +'<div class="item-king-card" data-product-id="134978667" data-variants="'+variants+'">'
          +'<a href="https://www.thekingofparfums.com.br/produtos/xerjoff-erba-pura/">'
          +'<img alt="'+alt+'" src="/placeholder.gif"></a></div></div>')
 def variants(self):
  return [
    {"id":1001,"available":False,"price_number":1299,"compare_at_price_number":1999,"price_short":"R$1.299,00","option0":"100 ML SEM CAIXA","image_url":"//acdn-us.mitiendanube.com/stores/001/216/674/products/erba.webp"},
    {"id":1002,"available":True,"price_number":1499,"compare_at_price_number":1999,"price_short":"R$1.499,00","option0":"100 ML","image_url":"//acdn-us.mitiendanube.com/stores/001/216/674/products/erba.webp"}]
 def test_discount_and_volume_by_variant(self):
  products=parse_king(self.html(self.variants()),"Perfumes de nicho","2026-10-22T00:00:00+00:00")
  self.assertEqual(len(products),1)
  p=products[0]
  self.assertEqual(p["id"],"king-1002")
  self.assertEqual(p["brand"],"Xerjoff")
  self.assertEqual(p["volumeMl"],100.)
  self.assertEqual(p["price"],1499.)
  self.assertEqual(p["originalPrice"],1999.)
  self.assertTrue(p["discountDeclared"])
  self.assertEqual(p["image"].split(":")[0],"https")
 def test_preserve_distinct_bottles(self):
  variants=self.variants()
  variants[0]["available"]=True
  result=parse_king(self.html(variants),"Perfumes de nicho","2026-10-22T00:00:00+00:00")
  self.assertEqual(len(result),2)
  self.assertEqual(result[0]["condition"],"Sem caixa")
 def test_reject_unsupported_currency(self):
  variants=self.variants()
  variants[1]["price_short"]="USD 1499"
  self.assertEqual(parse_king(self.html(variants),"Perfumes de nicho","2026-10-22T00:00:00+00:00"),[])
 def test_no_unverified_compare_price(self):
  variants=self.variants()
  variants[1]["compare_at_price_number"]=1200
  prod=parse_king(self.html(variants),"Perfumes de nicho","2026-10-22T00:00:00+00:00")
  self.assertIsNone(prod[0]["originalPrice"])
if __name__=="__main__":unittest.main()
