import logging
import time
import os

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

execution_time = time.strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"logs/{execution_time}.log"

log_formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - [%(threadName)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("main_logger")

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

logger.info("Booting up.")

OBS_LOGIN_URL = "https://obs.ankara.edu.tr/Account/Login"
TRAIN_DATA_FOLDER = "ocr/trainingdata/"
TEST_DATA_FOLDER = "ocr/testdata/"
SQL_DATABASE_PATH = "results.db"
ACCOUNTS_JSON_PATH = "accounts.json"
INTERVAL = 300
