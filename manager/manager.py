import sqlite3
from scraper.scraper import OBSScraper


class Manager:
    _instance: "Manager" = ...
    conn = sqlite3.connect("notlar.db")
    cursor = conn.cursor()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self): ...
