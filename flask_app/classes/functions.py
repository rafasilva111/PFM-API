from datetime import datetime, timedelta

from .models import UNITS_TYPE
from ..ext.logger import log

## parsing strings dd/mm/yyyy to dates


COLHER_DE_CHA = 4
COLHER_DE_SOPA = 10


def normalize_quantity(quantity_original):
    if "unid.)" in quantity_original:
        return UNITS_TYPE.UNITS.value,float(quantity_original.split('(')[1].split(' ')[0].strip())
    elif 'g' in quantity_original:
        return UNITS_TYPE.GRAMS.value,float(quantity_original.replace('g', '').strip())

    elif 'gr' in quantity_original:
        return UNITS_TYPE.GRAMS.value,float(quantity_original.replace('g', '').strip())

    elif 'c. de chá' in quantity_original:
        quantity_helper = quantity_original.replace('c. de chá', '')
        total = float(0)
        if "½" in quantity_helper:
            total = 0.5 * COLHER_DE_CHA
            quantity_helper = quantity_helper.replace("½", '')
        try:
            return UNITS_TYPE.GRAMS.value,total + float(quantity_helper.strip()) * COLHER_DE_CHA
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed: {quantity_helper.strip()}")
            return -1
    elif 'c. de sopa' in quantity_original:
        quantity_helper = quantity_original.replace('c. de sopa', '')
        total = float(0)
        if "½" in quantity_helper:
            total = 0.5 * COLHER_DE_SOPA
            quantity_helper = quantity_helper.replace("½", '')

        try:
            return UNITS_TYPE.GRAMS.value,total + float(quantity_helper.strip()) * COLHER_DE_SOPA
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {quantity_helper}")
            return -1

    log.debug(f"Quantity_helper was unable to be parsed: {quantity_original.strip()}")
    return UNITS_TYPE.GRAMS.value,0



def parse_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%YT%H:%M:%S")
        return date_obj
    except ValueError:
        raise ValueError("Invalid date format. Please use 'DD/MM/YYYYThh:mm:ss' format.")


def add_days(date_obj, days):
    new_date = date_obj + timedelta(days=days)
    return new_date
