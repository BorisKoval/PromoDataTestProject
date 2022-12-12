import logging
import os
import traceback

from .config import LOGS_DIR

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)


def setup_logger(name, log_file, level=logging.INFO):
    """Настройка всех логеров."""

    log_file = os.path.join(LOGS_DIR, log_file)

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


error_logger = setup_logger('error_logger', 'errors.log', level=logging.ERROR)
info_logger = setup_logger('info_logger', 'info.log')


#todo Не было понятно, что именно из успешных действий нужно логировать
def log_info(msg):
    """Логирование инфо сообщений"""
    print(msg)
    info_logger.info(msg)


def log_error(msg):
    """Логирование ошибок"""
    error_logger.error(msg)


def run_with_log(func):
    """Декоратор функции для логировани ошибок"""
    def inner(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except:
            log_error(traceback.format_exc())
            raise

        return result

    return inner
