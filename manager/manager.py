import sqlite3
import json
from scraper.scraper import OBSScraper


class Manager:
    _instance: "Manager" = None
    accounts: list[dict] = None
    scrapers: list[OBSScraper] = []
    conn = sqlite3.connect("manager/notlar.db")
    cursor = conn.cursor()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.loadAccounts()

    def loadAccounts(self):
        with open("manager/accounts.json", "r", encoding="utf-8") as file:
            self.accounts = json.load(file)

    def initializeScrapers(self):
        for account in self.accounts:
            self.scrapers.append(
                OBSScraper(account["label"], account["username"], account["password"])
            )


if __name__ == "__main__":
    x = Manager()
    print(x.accounts)
