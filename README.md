## Magnitcosmetic-Scrapy

Скрипт, использующий фреймворк `Scrapy`, предназначенный для получения полной информации о товарах на
сайте https://magnitcosmetic.ru/.

Реализовано сохранение всех требуемых и поддерживаемых сайтом функций:

- :white_check_mark: Парсинг нескольких категорий
- :white_check_mark: Парсинг категорий с 200+ товаров
- :white_check_mark: Поддержка прокси
- :white_check_mark: Сбор данных с учётом региона - Москва
- :white_check_mark: Сохранение данных в .json файле 

<details> 
<summary>Задача:</summary>

Используя фреймворк Scrapy необходимо написать код программы для получения информации о товарах интернет-магазина из
списка категорий по заранее заданному шаблону, данную информацию необходимо представлять в виде списка словарей (один
товар - один словарь) и сохрянить в файл с расширением .json

Выбрать 2 категории или больше, с количеством от 200 товаров на сайте magnitcosmetic.ru (
например https://magnitcosmetic.ru/catalog/kosmetika/makiyazh_glaz/)

Обязательно осуществлять сбор данных с учетом региона - Москва. Магазин можно выбрать любой.

По возможности в процессе сбора использовать подключение через прокси.

```python
{
    "timestamp": "",  # {str} Текущее время в формате timestamp
    "RPC": "",  # {str} Уникальный код товара
    "url": "",  # {str} Ссылка на страницу товара
    "title": "",
    # {str} Заголовок/название товара (если в карточке товара указан цвет или объем, необходимо добавить их в title в формате: "{название}, {цвет}")
    "marketing_tags": [],
    # {list of str} Список тегов, например: ['Популярный', 'Акция', 'Подарок'], если тэг представлен в виде изображения собирать его не нужно
    "brand": "",  # {str} Брэнд товара
    "section": [],
    # {list of str} Иерархия разделов, например: ['Игрушки', 'Развивающие и интерактивные игрушки', 'Интерактивные игрушки']
    "price_data": {
        "current": 0.,  # {float} Цена со скидкой, если скидки нет то = original
        "original": 0.,  # {float} Оригинальная цена
        "sale_tag": ""
        # {str} Если есть скидка на товар, то необходимо вычислить процент скидки и записать формате: "Скидка {}%"
    },
    "stock": {
        "in_stock": True,  # {bool} Должно отражать наличие товара в магазине
        "count": 0  # {int} Если есть возможность получить информацию о количестве оставшегося товара в наличии, иначе 0
    },
    "assets": {
        "main_image": "",  # {str} Ссылка на основное изображение товара
        "set_images": [],  # {list of str} Список больших изображений товара
        "view360": [],  # {list of str}
        "video": []  # {list of str} 
    },
    "metadata": {
        "__description": "",  # {str} Описание товара
        # Ниже добавить все характеристики которые могут быть на странице товара, такие как Артикул, Код товара, Цвет, Объем, Страна производитель и т.д.
        "АРТИКУЛ": "A88834",
        "СТРАНА ПРОИЗВОДИТЕЛЬ": "Китай"
    },
    "variants": 1,
    # {int} Кол-во вариантов у товара в карточке (За вариант считать только цвет или объем/масса. Размер у одежды или обуви вариантами не считаются)
}
```

</details>