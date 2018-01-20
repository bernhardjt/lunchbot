from datetime import datetime

import requests

from src.models.dish import Dish
from src.utils.date_util import to_date

MAIN = 4

ui_url = 'http://leonardi.webspeiseplan.de/Menu'
api_url = 'http://leonardi.webspeiseplan.de/index.php?token=d38436e0839755e6cde59cbda0fff016&model=menu&location=2100&languagetype=1&_=1513876707612'


def food_menu_applies_today(provider):
    return to_date(provider['speiseplanAdvanced']['gueltigVon']) <= datetime.today().date() <= to_date(
        provider['speiseplanAdvanced']['gueltigBis'])


def get_lunch_for_date(date=datetime.now(), show_only_current_day=True):
    res = requests.get(
        api_url,
        headers={'User-agent': 'crawler'}
    )

    dishes = []
    date_string = date.strftime('%Y-%m-%d')

    for food_offer in res.json()['content']:
        if food_offer['speiseplanAdvanced']['anzeigename'].strip() == 'Speisenkarte Essbar':
            for menu_item in (food_offer['speiseplanGerichtData']):
                dish_raw = menu_item['speiseplanAdvancedGericht']
                if (dish_raw['datum'].startswith(date_string) or not show_only_current_day) and dish_raw['gerichtkategorieID'] == MAIN:
                    dish_ = menu_item_to_dish(menu_item)
                    dishes.append(dish_)

    return dishes


def menu_item_to_dish(menu_item):
    full_dish = menu_item['speiseplanAdvancedGericht']['gerichtname'].strip().split(' I ', 1)
    dish_name = full_dish[0].strip().replace(' I', ',')
    ingredients = full_dish[1].strip().replace(' I', ',') if len(full_dish) > 1 else ''
    price = menu_item['zusatzinformationen'].get('mitarbeiterpreisDecimal2', None)
    kcal = menu_item['zusatzinformationen'].get('nwkcalInteger', None)
    kj = menu_item['zusatzinformationen'].get('nwkjInteger', None)

    # API is pretty unreliable regarding kcal / kj data, i.e. sometimes mislabels kj and kcal or has no values at all
    actual_kcal = None if kcal is None and kj is None else min(kcal, kj)

    return Dish('Kantine (P7)', dish_name, ingredients, price, actual_kcal, src=ui_url)
