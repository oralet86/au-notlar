import json
from scraper.scraper import OBSScraper

data = None

with open("scraper/accounts.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for dictionary in data:
    x = OBSScraper(dictionary["label"], dictionary["username"], dictionary["password"])
    x.navigateSite()
