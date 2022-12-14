import sys
import time

from core.config import INTERVAL_M
from core.config import RESTART_COUNT
from core.parser import ZooCatalogIterator
from core.parser import ZooProductsIterator
from core.writer import BaseZooCatalogWriter
from core.writer import BaseZooProductsWriter

if __name__ == '__main__':

    if len(sys.argv) != 2:
        raise SyntaxError(
            'Для запуска необходимо указать один из параметров "--catalogs" '
            'или "--products"'
        )

    catalogs = sys.argv[1] == '--catalogs'
    products = sys.argv[1] == '--products'

    if catalogs:
        writer, iterator = BaseZooCatalogWriter, ZooCatalogIterator
    elif products:
        writer, iterator = BaseZooProductsWriter, ZooProductsIterator
    else:
        raise SyntaxError(
            'Указанный параметр отличается от "--catalogs" или "--products"'
        )

    attempts = RESTART_COUNT
    while attempts > 0:
        try:
            print(f'Парсер запущен.')
            writer(zoo_row_iterator=iterator()).run_write()
        except Exception as e:
            print(
                f'Произошла ошибка в работе парсера.\n{str(e)}\n'
                f'Происходит перезапуск...')
            attempts -= 1
            time.sleep(INTERVAL_M)
        else:
            break
