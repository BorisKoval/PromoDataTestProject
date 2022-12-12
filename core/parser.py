import datetime
import re
import time
import traceback

import requests
from bs4 import BeautifulSoup

from .config import HEADERS
from .config import MAX_RETRIES
from .config import get_delay
from .constants import CATALOG_PART
from .constants import CATALOG_URL
from .constants import PRODUCT_PAGES_URL
from .constants import TARGET_URL
from .logger import log_error
from .logger import log_info
from .logger import run_with_log


class BaseZooIterator:
    """Базовый итератор для данных парсера"""

    @staticmethod
    def try_get_url_text(url, delay=0):
        """Попытка вернуть тело страницы по url"""

        attempts = MAX_RETRIES
        time.sleep(delay)

        html_text = None

        while attempts > 0:
            try:
                html_text = requests.get(url, headers=HEADERS).text
            except ConnectionError:
                attempts -= 1
            except:
                log_error(traceback.format_exc())
                return
            else:
                return html_text

        return html_text

    def get_tags_by_url(self, url, tag, class_name):
        """Возвращает BeautifulSoup тэги для разбора"""

        delay = get_delay()

        try:
            html_text = self.try_get_url_text(url, delay)
            html_bs = BeautifulSoup(html_text, "html.parser")
            pages_tags = html_bs.find_all(tag, class_=class_name)
        except:
            log_error(traceback.format_exc())
            return

        return pages_tags, html_bs,

    def __iter__(self):
        raise NotImplementedError


class ZooCatalogIterator(BaseZooIterator):
    """Итератор данных по каталогу"""

    ID_REGEX = r'.+\/(.+)\/(.+)\/$'

    def find_ids(self, href):
        """Поиск родительского и дочернего id из ссылки"""
        parent_id, child_id = re.findall(self.ID_REGEX, href)[0]

        return child_id, parent_id

    @run_with_log
    def __iter__(self):
        pages_tags, _ = self.get_tags_by_url(
            CATALOG_URL, 'ul', 'catalog-menu-left-1')

        pages_catalog_urls = [
            (x['href'], x.text) for x in pages_tags[0].find_all('a') if
            x.text != ''
        ]

        yield ['Каталог', CATALOG_PART]

        pages_len = len(pages_catalog_urls)
        for catalog_href, catalog_title in pages_catalog_urls:
            log_info(f"Обработка каталога: {catalog_title} (всего {pages_len})")

            catalog_href = catalog_href.replace(CATALOG_PART, '')
            yield [catalog_title, catalog_href, CATALOG_PART]

            catalog_urls, catalog_bs = self.get_tags_by_url(
                CATALOG_URL + catalog_href, 'span', 'catalog-menu-opener-blank')

            if catalog_urls:
                for tag in catalog_urls:
                    href_name = tag.parent.find_all('a')[0].text
                    child_id, parent_id = self.find_ids(
                        tag.parent.find_all('a')[0]['href'])
                    yield [href_name, child_id, parent_id]

            else:
                for tag in catalog_bs.find_all(
                        'ul', class_='catalog-menu-left-1')[0].find_all('a'):
                    child_id, parent_id = self.find_ids(tag['href'])
                    yield [tag.text, child_id, parent_id]


class ZooProductsIterator(BaseZooIterator):
    """Итератор по данным каждого найденного товара"""

    SEEN_PRODUCTS = []

    @staticmethod
    def call_product_attr(attr_func):
        """
        Пытаемся полчить атрибут товара, либо записываем инфу об ошибке в лог
        """
        result = ''
        try:
            result = attr_func()
        except:
            log_error(traceback.format_exc())
        return result

    def find_by_regex(self, regex, in_func_str):
        """Достаем информацию по регулярному выражению"""
        result = ''
        in_str = self.call_product_attr(in_func_str)

        if in_str:
            re_result = re.findall(regex, in_str)
            result = re_result[0] if re_result else ''

        return result

    @run_with_log
    def prepare_raw_info(
            self, product_info_tags, product_bs, short_product_url):
        """
        Подготавливаем информацию о товаре в сыром виде, некоторые атрибуты в
        виде функций, для дальнейшего отлова ошибок парсинга
        """

        sku_barcode = self.call_product_attr(
            lambda: product_info_tags[1].contents[1].contents[1].text)

        sku_article = self.call_product_attr(
            lambda: product_info_tags[0].contents[1].text.replace('\n', ''))

        #  Пропускаем товары с одинаковыми артикулами и штрихкодами
        if sku_barcode and sku_article and (
                sku_barcode, sku_article,) in self.SEEN_PRODUCTS:
            return
        else:
            self.SEEN_PRODUCTS.append((sku_barcode, sku_article,))

        raw_product_info = [
            lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

        price = ''
        price_promo = ''
        try:
            price = product_info_tags[4].contents[4].text.replace(' р', '')
            price_promo = (
                product_info_tags[4].contents[7].text.replace(' р', ''))
        except IndexError:
            pass

        sku_status = 1 if price else 0

        head_tags = product_bs.find_all('div', class_='catalog-element-right')
        sku_name = lambda: head_tags[0].contents[1].text

        breadcrumb_tags = product_bs.find_all('ul',
                                              class_='breadcrumb-navigation')
        sku_category = lambda: '|'.join(
            [x.text for x in breadcrumb_tags[0].find_all('a')])

        sku_country = lambda: head_tags[0].contents[3].contents[1].contents[3].text

        # todo гр и шт могут быть не в названии.
        # Пример https://zootovary.ru/catalog/tovary-i-korma-dlya-koshek/korm_vlazhnyy_dlya_koshek/chetveronogiy-gurman/petibon/chetveronogiy_gurman_petibon_smart_pashtet_dlya_koshek_s_indeykoy_i_utkoy.html

        sku_weight_min = self.find_by_regex(r'(\d+)гр', sku_name)
        sku_volume_min = self.find_by_regex(r'(\d+)\s?мл', sku_name)
        sku_quantity_min = self.find_by_regex(r'(\d+)\s?шт', sku_name)

        images_tags = product_bs.find_all('a', class_='cloud-zoom')
        sku_images = lambda: ','.join(
            [TARGET_URL + image['href'] for image in images_tags])

        raw_product_info.extend([
            price, price_promo, sku_status, sku_barcode, sku_article, sku_name,
            sku_category, sku_country, sku_weight_min, sku_volume_min,
            short_product_url, sku_quantity_min, sku_images
        ])

        return raw_product_info

    @run_with_log
    def get_product_info(
            self, product_info_tags, product_bs, short_product_url):
        """Возвращает список найденных атрибутов о товаре"""

        raw_product_info = self.prepare_raw_info(
            product_info_tags, product_bs, short_product_url)

        product_info = []
        for info in raw_product_info:
            if callable(info):
                product_info.append(self.call_product_attr(info))
            else:
                product_info.append(info)

        return product_info

    def __iter__(self):
        pages_tags, _ = self.get_tags_by_url(CATALOG_URL, 'div', 'navigation')

        last_page_num_str = pages_tags[0].find_all('a').pop()['href']
        last_page_num = int(
            re.findall(r'PAGEN_\d+=(\d+)', last_page_num_str)[0])

        for page_num in range(1, last_page_num):
            log_info(f"Обработка страницы {page_num} из {last_page_num}")

            page_url = PRODUCT_PAGES_URL.format(page_num=page_num)
            page_products_urls, _ = self.get_tags_by_url(
                page_url, 'div', 'catalog-content-info')

            for short_product_url in page_products_urls:
                short_product_url = (
                    TARGET_URL + short_product_url.contents[1].attrs['href'])
                product_info_tags, product_bs = self.get_tags_by_url(
                    short_product_url, 'td', 'tg-yw4l22')

                product_info = self.get_product_info(
                    product_info_tags, product_bs, short_product_url)

                log_info(f"Обработка товара: {product_info[6]}")
                if product_info:
                    yield product_info
