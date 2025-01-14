import json
import threading
import time
from scraper.scraper import OBSScraper
from logging_config import logger


class Manager:
    _instance: "Manager" = None
    accounts: list[dict] = None
    scrapers: list[OBSScraper] = []
    interval: int = 60
    lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating manager instance.")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.loadAccounts()
        self.initializeScrapers()
        self.startScrapers()
        self.runScrapers()

    def loadAccounts(self):
        logger.info("Loading accounts.")
        with open("manager/accounts.json", "r", encoding="utf-8") as file:
            self.accounts = json.load(file)

    def initializeScrapers(self):
        logger.info("Initializing scrapers.")
        for account in self.accounts:
            self.scrapers.append(
                OBSScraper(account["label"], account["username"], account["password"])
            )

    def startScrapers(self):
        logger.info("Starting scrapers.")
        for scraper in self.scrapers:
            scraper.start()

    def runScrapers(self):
        def scrape():
            while True:
                start_time = time.time()
                for scraper in self.scrapers:
                    logger.info(f"Scraping in session: {scraper.label}")
                    scraper.refresh()
                    scraper.navigateSite()
                    scraper.extractResults()

                elapsed_time = time.time() - start_time
                logger.info(f"Completed execution in: {elapsed_time:.2f} seconds")
                remaining_time = self.interval - elapsed_time
                logger.info(f"Remaining time: {remaining_time:.2f}")
                if remaining_time > 0:
                    time.sleep(remaining_time)

        thread = threading.Thread(target=scrape)
        thread.start()


if __name__ == "__main__":
    x = Manager()
