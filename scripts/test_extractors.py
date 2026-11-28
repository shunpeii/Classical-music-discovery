import unittest
from extractors import jsonld, css, api_json, rss, price
from scrape import normalize


class ExtractorTests(unittest.TestCase):
    def test_jsonld(self):
        html = '<script type="application/ld+json">{"@graph":[{"@type":"MusicEvent","name":"Concert","startDate":"2099-01-01","location":{"name":"Hall"}}]}</script>'
        self.assertEqual(list(jsonld(html))[0]["venue"], "Hall")

    def test_css(self):
        html = '<article><h2>Concert</h2><time datetime="2099-01-01">Jan</time><a href="/event">Details</a></article>'
        config = {"selectors":{"item":"article","title":"h2","date":{"css":"time","attr":"datetime"},"link":"a"}}
        self.assertEqual(list(css(html, config))[0]["date"], "2099-01-01")

    def test_api(self):
        config = {"itemsPath":"data.events","fields":{"title":"name"}}
        self.assertEqual(list(api_json('{"data":{"events":[{"name":"Concert"}]}}', config)), [{"title":"Concert"}])

    def test_rss(self):
        self.assertEqual(list(rss("<rss><item><title>Concert</title></item></rss>", {"fields":{"title":"title"}})), [{"title":"Concert"}])

    def test_normalize(self):
        source = {"id":"test","url":"https://example.com/","venue":"Hall","area":"Tokyo"}
        row = normalize({"title":"Concert","date":"2099-01-01","price":"5,000円"}, source)
        self.assertEqual(row["price"], 5000)
        self.assertIsNone(normalize({"title":"Concert","date":"2099-02-30"}, source))
        self.assertIsNone(price("3000-5000円"))


if __name__ == "__main__":
    unittest.main()
