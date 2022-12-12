import json
from random import randint

from core.constants import CONFIG_NAME

with open(CONFIG_NAME) as config_file:
    file_data = config_file.read()
    config_data = json.loads(file_data)


def config_get(param, default=''):
    value = config_data.get(param, default)
    return value or default


# Имя директории, в которую будут записываться csv-файлы c
# результатами парсинга. По умолчанию: "out".
OUT_DIR = config_get('output_directory', 'out')

# Список id категорий, которые будем парсить.
# Возможность указать несколько категорий через запятую.
# Если категорий не задано, перебираем полный каталог, т.е. все категории.
CATEGORIES = config_get('categories', '')
CATEGORIES = CATEGORIES.split(',') if CATEGORIES else []

# Минимальное и максимальное значение искусственной задержки между
# товарами в секундах (чтобы избежать блокировки за спам). Программа должна
# выбирать задержку случайным образом в заданном интервале.
# По умолчанию 1-3 секунды. При значении 0 искусственная задержка отключается и
# скорость работы парсера зависит от аппаратного обеспечения.
DELAY_RANGE_S = config_get('delay_range_s', '1-3')
DELAY_RANGE_S = [
    int(x) for x in DELAY_RANGE_S.split('-')
] if DELAY_RANGE_S else []

get_delay = (
    lambda: randint(DELAY_RANGE_S[0], DELAY_RANGE_S[1]) if DELAY_RANGE_S else 0)

#  Количество попыток повторного запроса, в случае некорректного ответа.
MAX_RETRIES = config_get('max_retries', 1)
MAX_RETRIES = int(MAX_RETRIES)

# Необходимые заголовки запросов (User-agent и т.п.).
HEADERS = config_get('headers', '')

# имя директории, в которую будут записываться логи.
LOGS_DIR = config_get('logs_dir', 'logs')

# Количество попыток перезапуска и задержка между ними при аварийном
# завершении парсинга.
RESTART_COUNT = config_data.get('restart').get('restart_count', 0)
INTERVAL_M = config_data.get('restart').get('interval_m', 0)
