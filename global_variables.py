import logging
import time
import os
from os import getenv

OBS_LOGIN_URL = getenv("OBS_LOGIN_URL")
TRAIN_DATA_FOLDER = getenv("TRAIN_DATA_FOLDER")
TEST_DATA_FOLDER = getenv("TEST_DATA_FOLDER")
SQL_DATABASE_PATH = getenv("SQL_DATABASE_PATH")
ACCOUNTS_JSON_PATH = getenv("ACCOUNTS_JSON_PATH")
INTERVAL = int(getenv("INTERVAL"))
LOG_DIR = getenv("LOG_DIR")
LOG_MODE = getenv("LOG_MODE")
BOT_TOKEN = getenv("BOT_TOKEN")

execution_time = time.strftime("%Y-%m-%d_%H-%M-%S")
log_formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - [%(threadName)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("main_logger")

if LOG_MODE == "file" or LOG_MODE == "both":
    os.makedirs(LOG_DIR, exist_ok=True)
    log_filename = f"{LOG_DIR}/{execution_time}.log"
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

if LOG_MODE == "terminal" or LOG_MODE == "both":
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)

logger.setLevel(logging.INFO)
logger.info("Booting up.")
