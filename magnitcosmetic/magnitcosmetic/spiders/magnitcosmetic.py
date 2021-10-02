import json
import random
from datetime import datetime

import scrapy


class MagnitcosmeticSpider(scrapy.Spider):
    name = 'magnitcosmetic'
    allowed_domains = ['https://magnitcosmetic.ru/']
    start_urls = [
        'https://magnitcosmetic.ru/catalog/bytovaya_khimiya/stiralnye_poroshki_geli_kapsuly/?perpage=96',
        'https://magnitcosmetic.ru/catalog/tovary_dlya_doma/stroitelstvo_i_remont/?perpage=96'
    ]  # 237 + 208 = 445 товаров на 01.10.2021
    shop_xml_code = '19077662880'  # г. Москва, ул. Абельмановская, 6, 18850594800 - shop_xml_code по умолчанию
    # шлём POST-запрос по данному url, чтобы получить данные о цене товара
    catalog_load_remains_url = 'https://magnitcosmetic.ru/local/ajax/load_remains/catalog_load_remains.php'
    proxy_list = [
        '188.130.186.88:3000',
        '109.248.13.233:3000',
        '188.130.211.27:3000',
        '109.248.49.171:3000',
        '95.182.127.19:3000',
        '95.182.124.180:3000',
        '46.8.11.161:3000',
        '188.130.136.84:3000',
        '45.90.196.41:3000',
        '46.8.56.153:3000',
        '188.130.219.141:3000',
        '109.248.128.82:3000',
        '188.130.129.184:3000',
        '109.248.48.235:3000',
        '188.130.129.196:3000',
        '185.181.244.178:3000',
        '46.8.14.58:3000',
        '188.130.221.80:3000',
        '46.8.110.172:3000',
        '109.248.143.156:3000',
    ]  # текущие прокси привязаны к моему IP, требуется заменить на свои

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url,
                                 callback=self.parse_catalog,
                                 meta={'proxy': random.choice(self.proxy_list)})

    def parse_catalog(self, response):
        all_products = response.css('.catalog__item')
        product_urls = []
        for product in all_products:
            product_url = product.css('.product__link::attr(href)').get()
            product_url = response.urljoin(product_url)
            product_urls.append(product_url)
            yield scrapy.Request(url=product_url,
                                 callback=self.parse_details,
                                 meta={'proxy': random.choice(self.proxy_list)},
                                 dont_filter=True)

        current_page: str = response.css('.curPage::text').get()
        total_pages: str = response.css('.pageCount::text').get()
        has_next_page: bool = current_page < total_pages
        if has_next_page and current_page.isdigit():  # isdigit() вместо except ValueError, в теории можно удалить
            next_page_number = int(current_page) + 1
            next_page_url = response.urljoin(f'?perpage=96&PAGEN_1={next_page_number}')
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_catalog,
                dont_filter=True)

    def parse_details(self, response):
        product_title: str = response.css('.action-card__name::text').get()
        if product_title:  # иного события не происходило
            product_title = product_title.strip()
        product_id: str = response.url.split('/')[-2]  # '55783' из '.../best_url/53783/'

        all_rows = response.css('.action-card__table > tr')
        metadata = dict()
        for row in all_rows:
            property_row: list = row.css('td::text').getall()
            if len(property_row) >= 2:
                property_name: str = property_row[0].strip()
                property_name: str = property_name[:-1] if property_name.endswith(':') else property_name
                property_value: str = property_row[1].strip()
                metadata[property_name] = property_value

        brand = metadata.get('Бренд', '')  # у Магнита часто не указывается бренд
        product_description = response.css('.action-card__text:nth-child(1)::text').get() or ''
        metadata['__description'] = product_description

        product_sections = response.css('.breadcrumbs__link::text').getall()
        section = []
        for i in product_sections[2:]:  # первый элемент - "Главная", второй элемент - "Каталог"
            section.append(i.strip())

        product_image = response.css('.action-card__cols .product__image::attr(src)').get()
        product_image = response.urljoin(product_image)

        marketing_tag = 'Акция' if response.css('.event__product-title') else ''  # блок есть только во время акции

        product_data = {
            'timestamp': datetime.utcnow(),
            'RPC': product_id,
            'url': response.url,
            'title': product_title,
            'marketing_tags': marketing_tag,
            'brand': brand,
            'section': section,
            'assets': {
                'main_image': product_image,
                'set_images': [],  # обязательно ли указывать?
                'view360': [],  # сайт не использует такие
                'video': []  # современные технологии
            },
            'metadata': metadata,
            'variants': 1
        }

        body = self._get_request_body_for_get_price(response)
        if body:  # шлём POST-запрос только если есть что слать
            yield scrapy.Request(
                url=self.catalog_load_remains_url,
                body=body,
                method='POST',
                headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                         'X-Requested-With': 'XMLHttpRequest',
                         'Referer': response.url},
                meta={'product_data': product_data},
                callback=self.parse_price,
                dont_filter=True
            )
        else:  # не сохранять сломанные товары?
            # предполагается, что товар сломан - о нём нельзя вытащить цену и другие данные
            # хороший пример - https://magnitcosmetic.ru/catalog/bytovaya_khimiya/stiralnye_poroshki_geli_kapsuly/52098/
            # на момент написания комментария карточка товара выглядит так: https://i.imgur.com/UnNo3pl.png
            yield product_data

    def parse_price(self, response):
        product_data: dict = response.meta.get('product_data')
        price_dict: dict = json.loads(response.text)  # получаем от POST-запроса на catalog_load_remains.php
        try:
            price_data: dict = price_dict.get('data')[0]
        except (IndexError, TypeError):
            price_data = {}
        quantity = price_data.get('quantity')
        original_price = float(price_data.get('price', 0))  # сделать условную цену в -1, если не пришла цена?

        if product_data.get('marketing_tags'):  # значит участвует в акции
            current_price = float(price_data.get('price_promo', original_price))
        else:  # price_promo приходит вне зависимости от участия в акции, по этой причине проверяем именно участие
            current_price = float(original_price)

        try:
            sale_percent = round(100 - current_price * 100 / original_price, 2)
        except ZeroDivisionError:
            sale_percent = 0
        sale_tag = f'Скидка {sale_percent}%' if sale_percent else ''

        product_data['price_data'] = {
            'current': float(current_price),
            'original': float(original_price),
            'sale_tag': sale_tag
        }
        product_data['stock'] = {
            'in_stock': bool(quantity),
            'count': 0
        }
        yield product_data

    def _get_request_body_for_get_price(self, response):
        """
        На странице товара есть тег <script>, содержащий информацию для идентификации товара. Эта информация
        потребуется для POST-запроса к API сайта и получения актуальной цены на товар,
        поскольку цена не указывается в теле базового HTML.

        - SHOP_XML_CODE - код магазина, цену в котором мы пытаемся узнать. Указываем при инициализации класса.
        - В оригинальном теле запроса указывается enigma, она находится в input.remains__detail::attr(value) страницы,
        но API принимает запрос с любой ненулевой энигмой.
        - В оригинальном теле запроса имеются параметры JUST_ONE, wru и type, которые можно опустить,
        если параметр ism указать как Y (по умолчанию стоит N).
        """
        # если товар частично убран с сайта, то PRODUCT_XML_CODE будет равен строке '[0]'
        # пример товара: https://magnitcosmetic.ru/catalog/bytovaya_khimiya/stiralnye_poroshki_geli_kapsuly/52098/
        data = response.xpath("//script[contains(., 'PRODUCT_XML_CODE')]/text()").re('PRODUCT_XML_CODE = {(.*)')
        try:
            data_json: dict = json.loads(data[0])
            product_key = [key for key in data_json.keys()][0]
            product_value = data_json.get(product_key, 0)
        except (TypeError, IndexError, AttributeError, json.JSONDecodeError):
            return None
        return f'SHOP_XML_CODE={self.shop_xml_code}&PRODUCTS%5B{product_key}%5D={product_value}&enigma=1&ism=Y'
