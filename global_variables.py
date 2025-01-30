import logging
import time
import os
from typing import Literal

# Dont change this unless the login page has been changed
OBS_LOGIN_URL = "https://obs.ankara.edu.tr/Account/Login"

# Where training data is located
TRAIN_DATA_FOLDER = "ocr/trainingdata/"

# Where test data is located
TEST_DATA_FOLDER = "ocr/testdata/"

# Path to the SQL database
SQL_DATABASE_PATH = "results.db"

# Path to the json file containing account information
ACCOUNTS_JSON_PATH = "accounts.json"

# How often should the scrapers refresh the page
INTERVAL = 300

# Path the logs will be saved
LOG_DIR = "logs"

# Log mode, "file" if you want to log to a file, "terminal" for logging to console,
# "both" for both saving logs to a file and printing to console. Default is file
LOG_MODE: Literal["file", "terminal", "both"] = "file"

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
