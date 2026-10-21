import unittest
from import_awin import parse_csv, amount, valid_link
class FeedTests(unittest.TestCase):
    def test_brl_csv(self):
        csv_data = 'merchant_id,merchant_name,aw_product_id,product_name,brand_name,search_price,currency,aw_deep_link,aw_image_url,product_price_old\n1,Loja,99,Gloss,Marca,"159,90",BRL,https://example.com/p,https://example.com/i.jpg,"199,90"\n'
        items=parse_csv(csv_data)
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['price'],159.9)
        self.assertEqual(items[0]['declaredDiscountPercent'],20.0)
    def test_reject_other_currency(self):
        self.assertEqual(parse_csv('product_id,product_name,price,currency,deep_link\n1,Shirt,100,USD,https://example.com'),[])
    def test_bad_link(self):
        self.assertFalse(valid_link('http://example.com/p'))
        self.assertFalse(valid_link('file:///etc/passwd'))
    def test_amount(self):
        self.assertEqual(amount("R$ 1.299,90"),1299.9)
        self.assertIsNone(amount("chame no zap"))
    def test_semicolon(self):
        items=parse_csv('product_id;product_name;price;currency;deep_link\n10;Batom;75.00;BRL;https://example.com/p\n')
        self.assertEqual(items[0]['price'],75.0)
if __name__ == '__main__': unittest.main()
