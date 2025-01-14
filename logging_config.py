import logging
import time

execution_time = time.strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"logs/{execution_time}.log"

with open(log_filename, "w"):
    ...

logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,
    encoding="utf-8",
    filemode="a",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("main_logger")

logger.info("Booting up.")