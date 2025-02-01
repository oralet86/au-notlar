import json
import threading
import time
from scraper import Scraper
from global_variables import logger, SQL_DATABASE_PATH, ACCOUNTS_JSON_PATH, INTERVAL
import sqlite3
from functools import partial


class Manager(object):
    threads: list[threading.Thread] = []
    lock = threading.Lock()
    accounts: list[dict] = []
    _ready = False

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Manager, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.initializeDatabase()
        self.loadAccounts()

    def start(self):
        self.createThreads()
        while not self._ready:
            time.sleep(1)
        self.startThreads()

    def loadAccounts(self):
        logger.info("Loading accounts.")
        with open(ACCOUNTS_JSON_PATH, "r", encoding="utf-8") as file:
            self.accounts = json.load(file)

    def startThreads(self):
        for thread in self.threads:
            thread.start()

    def createThreads(self):
        logger.info("Creating threads..")

        def threadTarget(account):
            logger.info("Executing thread..")
            scraper = Scraper(
                account["label"], account["username"], account["password"]
            )

            logger.info("Starting scraper..")
            scraper.start()

            while True:
                start_time = time.time()
                logger.info("Scraping in session..")
                scraper.navigateSite()
                scraper.extractResults()

                if scraper.results is not None:
                    with self.lock:
                        self.upsert_data(scraper.label, scraper.results)

                elapsed_time = time.time() - start_time
                logger.info(
                    f"Completed execution in: {elapsed_time:.2f} seconds, remaining time is: {(INTERVAL - elapsed_time):.2f} seconds."
                )

                while time.time() - start_time < INTERVAL:
                    time.sleep(1)

        for account in self.accounts:
            thread = threading.Thread(
                target=partial(threadTarget, account), name=account["label"]
            )
            self.threads.append(thread)

        self._ready = True

    @staticmethod
    def initializeDatabase():
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )"""
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES Departments(id)
        )"""
        )

        cursor.execute(
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

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (lecture_id) REFERENCES Lectures(id)
        )"""
        )

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def upsert_data(department_name, lecture_data):
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        # Ensure department exists
        cursor.execute("SELECT id FROM Departments WHERE name = ?", (department_name,))
        department_row = cursor.fetchone()
        if department_row is not None:
            department_id = department_row[0]
        else:
            logger.info(
                f'No value found for "{department_name}" in the Departments table. Creating one.'
            )
            cursor.execute(
                "INSERT INTO Departments (name) VALUES (?)", (department_name,)
            )
            department_id = cursor.lastrowid

        for lecture in lecture_data:
            # Ensure lecture exists
            cursor.execute(
                "SELECT id FROM Lectures WHERE name = ? AND department_id = ?",
                (lecture["name"], department_id),
            )
            lecture_row = cursor.fetchone()
            if lecture_row is not None:
                lecture_id = lecture_row[0]
            else:
                logger.info(
                    f'No value found for "{lecture["name"]}" in the Lectures table. Creating one.'
                )
                cursor.execute(
                    "INSERT INTO Lectures (department_id, name) VALUES (?, ?)",
                    (department_id, lecture["name"]),
                )
                lecture_id = cursor.lastrowid

            for exam in lecture["exams"]:
                # Check for an exam result with identical values
                cursor.execute(
                    """
                    SELECT id FROM Exams
                    WHERE lecture_id = ? AND name = ? AND percentage = ? AND date = ?
                """,
                    (lecture_id, exam["name"], exam["percentage"], exam["date"]),
                )
                exam_row = cursor.fetchone()

                if exam_row is None:
                    # If none were found, that means new exam results were entered
                    cursor.execute(
                        "DELETE FROM Exams WHERE lecture_id = ? AND name = ?",
                        (lecture_id, exam["name"]),
                    )
                    cursor.execute(
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
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_departments():
        logger.info("Retrieving department information.")
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Departments")
        dept_info = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        return dept_info

    @staticmethod
    def get_department_name(dept_id: str):
        logger.info(
            f'Retrieving department name from department with id: "{dept_id}" .'
        )
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM Departments WHERE id = ?", dept_id)
        dept_info = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return dept_info[0]

    @staticmethod
    def get_lectures(dept_id: str):
        logger.info(
            f'Retrieving lecture information from department with id: "{dept_id}" .'
        )
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Lectures WHERE department_id = ?", dept_id)
        dept_info = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        return dept_info

    @staticmethod
    def add_lecture_notification(lecture_id: str, user_id: str) -> bool:
        logger.info(f'Adding user notification to lecture with id: "{lecture_id}".')
        try:
            conn = sqlite3.connect(SQL_DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM Notifications WHERE lecture_id = ? AND user_id = ?",
                (lecture_id, user_id),
            )
            department_row = cursor.fetchone()
            if department_row is None:
                cursor.execute(
                    "INSERT INTO Notifications (lecture_id, user_id) VALUES (?, ?)",
                    (
                        str(lecture_id),
                        str(user_id),
                    ),
                )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.exception(
                f'Exception while adding user notification to lecture with id: "{lecture_id}", {e}'
            )
            return False

    @staticmethod
    def delete_lecture_notification(lecture_id: str, user_id: str) -> bool:
        logger.info(f'Deleting user notification to lecture with id: "{lecture_id}".')
        try:
            conn = sqlite3.connect(SQL_DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM Notifications WHERE lecture_id = ? AND user_id = ?",
                (lecture_id, user_id),
            )
            department_row = cursor.fetchone()
            if department_row is not None:
                cursor.execute(
                    "DELETE FROM Notifications WHERE lecture_id = ? AND user_id = ?",
                    (
                        str(lecture_id),
                        str(user_id),
                    ),
                )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.exception(
                f'Exception while deleting user notification to lecture with id: "{lecture_id}", {e}'
            )
            return False

    @staticmethod
    def get_lecture_users(lecture_id: str) -> list[str]:
        logger.info(f'Getting user notifications from lecture with id: "{lecture_id}".')
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM Notifications WHERE lecture_id = ?", (str(lecture_id),)
        )
        user_ids = [x[0] for x in cursor.fetchall()]
        conn.commit()
        cursor.close()
        conn.close()
        return user_ids

    @staticmethod
    def get_user_notifications(user_id: str) -> list[str]:
        logger.info(f'Getting user notifications from user with id: "{user_id}".')
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT lecture_id FROM Notifications WHERE user_id = ?",
            (str(user_id),),
        )
        lecture_info = [x[0] for x in cursor.fetchall()]
        conn.commit()
        cursor.close()
        conn.close()
        return lecture_info

    @staticmethod
    def does_user_follow_lecture(lecture_id: str, user_id: str) -> bool:
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM Notifications WHERE lecture_id = ? AND user_id = ?",
            (str(lecture_id), str(user_id)),
        )
        return_bool = cursor.fetchone() is not None
        conn.commit()
        cursor.close()
        conn.close()
        return return_bool

    @staticmethod
    def get_lecture_name(lecture_id: str) -> str:
        conn = sqlite3.connect(SQL_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM Lectures WHERE id = ?", (str(lecture_id),))
        lecture_name = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return lecture_name[0]


if __name__ == "__main__":
    ...
