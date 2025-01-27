import json
import threading
import time
from scraper.scraper import Scraper
from global_variables import logger, SQL_DATABASE_PATH, ACCOUNTS_JSON_PATH, INTERVAL
import sqlite3


class Manager:
    _instance: "Manager" = None
    accounts: list[dict] = None
    scrapers: list[Scraper] = []
    interval: int = INTERVAL
    lock = threading.Lock()
    conn = sqlite3.connect(SQL_DATABASE_PATH, check_same_thread=False)
    cursor = conn.cursor()

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating manager instance.")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.initializeDatabase()
        self.loadAccounts()
        self.initializeScrapers()
        self.startScrapers()

    def loadAccounts(self):
        logger.info("Loading accounts.")
        with open(ACCOUNTS_JSON_PATH, "r", encoding="utf-8") as file:
            self.accounts = json.load(file)

    def initializeScrapers(self):
        logger.info("Initializing scrapers.")
        for account in self.accounts:
            self.scrapers.append(
                Scraper(account["label"], account["username"], account["password"])
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
                    if scraper.results is not None:
                        with self.lock:
                            self.upsert_data(scraper.label, scraper.results)

                elapsed_time = time.time() - start_time
                logger.info(f"Completed execution in: {elapsed_time:.2f} seconds")
                remaining_time = self.interval - elapsed_time
                logger.info(f"Remaining time: {remaining_time:.2f}")
                if remaining_time > 0:
                    time.sleep(remaining_time)

        thread = threading.Thread(target=scrape)
        thread.start()

    @classmethod
    def initializeDatabase(cls):
        cls.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )"""
        )

        cls.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES Departments(id)
        )"""
        )

        cls.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            percentage TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (lecture_id) REFERENCES Lectures(id)
        )"""
        )

        cls.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            nickname TEXT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES Departments(id)
        )"""
        )

        cls.conn.commit()
        return

    @classmethod
    def upsert_data(cls, department_name, lecture_data):
        # Ensure department exists
        cls.cursor.execute(
            "SELECT id FROM Departments WHERE name = ?", (department_name,)
        )
        department_row = cls.cursor.fetchone()
        if department_row is not None:
            department_id = department_row[0]
        else:
            logger.info(
                f'No value found for "{department_name}" in the Departments table. Creating one.'
            )
            cls.cursor.execute(
                "INSERT INTO Departments (name) VALUES (?)", (department_name,)
            )
            department_id = cls.cursor.lastrowid

        for lecture in lecture_data:
            # Ensure lecture exists
            cls.cursor.execute(
                "SELECT id FROM Lectures WHERE name = ? AND department_id = ?",
                (lecture["name"], department_id),
            )
            lecture_row = cls.cursor.fetchone()
            if lecture_row is not None:
                lecture_id = lecture_row[0]
            else:
                logger.info(
                    f'No value found for "{lecture["name"]}" in the Lectures table. Creating one.'
                )
                cls.cursor.execute(
                    "INSERT INTO Lectures (department_id, name) VALUES (?, ?)",
                    (department_id, lecture["name"]),
                )
                lecture_id = cls.cursor.lastrowid

            for exam in lecture["exams"]:
                # Check for an exam result with identical values
                cls.cursor.execute(
                    """
                    SELECT id FROM Exams
                    WHERE lecture_id = ? AND name = ? AND percentage = ? AND date = ?
                """,
                    (lecture_id, exam["name"], exam["percentage"], exam["date"]),
                )
                exam_row = cls.cursor.fetchone()

                if exam_row is None:
                    # If none were found, that means new exam results were entered
                    cls.cursor.execute(
                        "DELETE FROM Exams WHERE lecture_id = ? AND name = ?",
                        (lecture_id, exam["name"]),
                    )
                    cls.cursor.execute(
                        """
                        INSERT INTO Exams (lecture_id, name, percentage, date)
                        VALUES (?, ?, ?, ?)
                    """,
                        (lecture_id, exam["name"], exam["percentage"], exam["date"]),
                    )
                    logger.info(
                        f'New exam results found for "{lecture["name"]} / {exam["name"]}". Overwriting old ones.'
                    )
                else:
                    ...
                    # This line cluttered up the logs too much.
                    # logger.info(f'Exam results of "{lecture["name"]} / {exam["name"]}" match the ones at the tables.')

        logger.info("Finished database update.")
        cls.conn.commit()


if __name__ == "__main__":
    ...
