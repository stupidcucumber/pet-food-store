import logging
import queue
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

log_listener: QueueListener | None = None


def start_logging() -> None:
    global log_listener

    log_queue = queue.Queue(-1)
    log_listener = QueueListener(
        log_queue, RotatingFileHandler("app.log", maxBytes=1024 * 1024, backupCount=5)
    )
    log_listener.start()

    logging.basicConfig(handlers=[QueueHandler(log_queue)], level=logging.ERROR)


def stop_logging() -> None:
    global log_listener

    if log_listener:

        log_listener.stop()
