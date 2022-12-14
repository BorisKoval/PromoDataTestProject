import csv
import datetime
import os.path

from .config import OUT_DIR
from .logger import run_with_log


class BaseZooWriter:
    """Базовый писатель данных в csv"""

    CSV_NAME = ''
    HEADERS = []

    def __init__(self, zoo_row_iterator):
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        out_csv_name = f'{self.CSV_NAME}{now}.csv'

        out_csv_path = os.path.join(
            os.path.dirname(__file__), os.path.pardir, OUT_DIR)

        if not os.path.exists(out_csv_path):
            os.mkdir(out_csv_path)

        self.out_csv_path = os.path.join(out_csv_path, out_csv_name)
        self.zoo_row_iterator = zoo_row_iterator

    @run_with_log
    def run_write(self):
        """Запуск записи данных в файл возвращаемых итератором"""

        with open(self.out_csv_path, 'w') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=';')
            csv_writer.writerow(self.HEADERS)
            for data in self.zoo_row_iterator:
                csv_writer.writerow(data)


class BaseZooCatalogWriter(BaseZooWriter):
    """Класс записи данных по каталогам"""
    CSV_NAME = 'catalog_out_'
    HEADERS = ['name', 'id', 'parent_id']


class BaseZooProductsWriter(BaseZooWriter):
    """Класс записи данных по товарам"""
    CSV_NAME = 'products_out_'
    HEADERS = [
        'price_datetime', 'price', 'price_promo', 'sku_status', 'sku_barcode',
        'sku_article', 'sku_name', 'sku_category', 'sku_country',
        'sku_weight_min', 'sku_volume_min', 'short_product_url',
        'sku_quantity_min', 'sku_images'
    ]
