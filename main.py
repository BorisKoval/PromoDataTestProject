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
        runner = BaseZooCatalogWriter(
            zoo_row_iterator=ZooCatalogIterator()).run_write
    elif products:
        runner = BaseZooProductsWriter(
            zoo_row_iterator=ZooProductsIterator()).run_write
    else:
        raise SyntaxError(
            'Указанный параметр отличается от "--catalogs" или "--products"'
        )

    attempts = RESTART_COUNT
    while attempts > 0:
        try:
            runner()
        except:
            attempts -= 1
            time.sleep(INTERVAL_M)
        else:
            break
