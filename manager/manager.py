import sqlite3
import json


class Manager:
    _instance: "Manager" = None
    accounts: list[dict] = None
    conn = sqlite3.connect("manager/notlar.db")
    cursor = conn.cursor()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.load_accounts()

    def load_accounts(self):
        with open("manager/accounts.json", "r", encoding="utf-8") as file:
            self.accounts = json.load(file)


if __name__ == "__main__":
    Manager()
