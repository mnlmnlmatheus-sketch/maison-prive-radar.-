import unittest
from unittest.mock import patch
import monitor
class FullMonitorRegression(unittest.TestCase):
 def test_photo_is_not_used_as_price(self):
  html='<script type="application/ld+json">{"@type":"Product","image":["https://oqvestir.fbitsstatic.net/img/p/produto/foto.jpg"],"offers":{"price":"449.90","priceCurrency":"BRL"}}</script>'
  item={"id":"unit-one","name":"Tênis","brand":"Teste","shop":"OQVestir","url":"https://www.oqvestir.com.br/tenis-123456","currency":"BRL"}
  captured={}
  def save(path,value):captured[path]=value
  with patch("monitor.read",side_effect=[[item],{"products":{}},[]]),patch("monitor.write",side_effect=save),patch("monitor.permitted",return_value=(True,"robots")),patch("monitor.fetch",return_value=html),patch("monitor.time.sleep",return_value=None):
   monitor.main()
  product=captured["data/prices.json"]["products"]["unit-one"]
  self.assertEqual(product["price"],449.9)
  self.assertTrue(product["image"].startswith("https://oqvestir.fbitsstatic.net/"))
if __name__=="__main__":unittest.main()
