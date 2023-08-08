from datetime import datetime, timedelta

from .models import UNITS_TYPE
from ..ext.logger import log
import re
## parsing strings dd/mm/yyyy to dates


COLHER_DE_CHA = 4
COLHER_DE_SOPA = 14
COLHER_DE_SOBREMESA = 9
COLHER_DE_CAFE = 1.5
CHAVENA = 250

units_model = ['dente','folha','q.b.','ml','L','lata','fatia','g','gr','kg','cápsula','tira','tiras','rodela','cabeça','unid','porção','ramo']

def normalize_quantity(quantity_original):
    helper = quantity_original.split(" ",1)
    value = helper[0].strip()
    units = helper[1].strip()
    if '(opcional)' in units:
        units = units.replace('(opcional)', '').strip()

    if units in units_model:
        if 'L' in units:
            value = value.replace(",", ".")
        elif 'gr' in units or 'g' in units:
            units = UNITS_TYPE.GRAMS.value
        elif '½' in units:
            value = 0.5

        return units, float(value)
    elif 'g' in quantity_original:
        pattern = r"(\d+)\s*g"
        match = re.search(pattern, quantity_original)
        if match:
            value = match.group(1)

        return 'G',float(value)
    elif 'ml' in quantity_original:
        pattern = r"(\d+)\s*ml"
        match = re.search(pattern, quantity_original)
        if match:
            value = match.group(1)

        return UNITS_TYPE.GRAMS.value,float(value)
    elif "unid.)" in quantity_original:
        return UNITS_TYPE.UNITS.value, float(quantity_original.split('(')[1].split(' ')[0].strip())
    elif "unid." in quantity_original or 'talo' in quantity_original or 'molho' in quantity_original or 'copo'in quantity_original or 'emb' in quantity_original:
        if len(helper) == 2:
            if '1⁄2' in value:
                value = 0.5
            return helper[1], float(value)
        helper = quantity_original.split("(", 1)[1][:-1].split(" ")
        return helper[1], float(helper[0])
    elif 'lata' in quantity_original:
        helper = quantity_original.split("(")[1]
        helper = helper[:-1]
        return UNITS_TYPE.GRAMS.value, float(helper[:-1])

    elif 'c. de chá' in quantity_original:
        quantity_helper = quantity_original.replace('c. de chá', '').strip()
        total = float(0)
        if '1⁄2' in quantity_helper:
            quantity_helper = "0.5"
        if "½" in quantity_helper:
            total = 0.5 * COLHER_DE_CHA
            quantity_helper = quantity_helper.replace("½", '')
        try:
            return UNITS_TYPE.GRAMS.value, total + float(quantity_helper) * COLHER_DE_CHA
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed: {quantity_helper.strip()}")
            return -1
    elif 'c. de sopa' in quantity_original:
        quantity_helper = quantity_original.replace('c. de sopa', '')
        total = float(0)

        if '1⁄2' in quantity_helper:
            quantity_helper = 0.5
        if "½" in quantity_helper:
            total = 0.5 * COLHER_DE_SOPA
            quantity_helper = quantity_helper.replace("½", '')

        try:
            return UNITS_TYPE.GRAMS.value, total + float(quantity_helper.strip()) * COLHER_DE_SOPA
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {quantity_helper}")
            return -1
    elif 'c. de sobremesa' in quantity_original or 'c. sobremesa' in quantity_original:
        quantity_helper = quantity_original.replace('c. de sobremesa', '')
        total = float(0)
        if '1⁄2' in quantity_helper:
            quantity_helper = 0.5
        if "½" in quantity_helper:
            total = 0.5 * COLHER_DE_SOBREMESA
            quantity_helper = quantity_helper.replace("½", '')

        try:
            return UNITS_TYPE.GRAMS.value, total + float(quantity_helper.strip()) * COLHER_DE_SOBREMESA
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {quantity_helper}")
            return -1
    elif 'c. de caf' in quantity_original:
        quantity_helper = quantity_original.replace('c. de sobremesa', '')
        total = float(0)
        if '1⁄2' in quantity_helper:
            quantity_helper = 0.5
        if "½" in quantity_helper:
            total = 0.5 * COLHER_DE_CAFE
            quantity_helper = quantity_helper.replace("½", '')

        try:
            return UNITS_TYPE.GRAMS.value, total + float(quantity_helper.strip()) * COLHER_DE_CAFE
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {quantity_helper}")
            return -1

    elif 'cháv' in quantity_original:
        quantity_helper = quantity_original.replace('c. de sobremesa', '')
        total = float(0)
        if '1⁄2' in quantity_helper:
            quantity_helper = 0.5
        if "½" in quantity_helper:
            total = 0.5 * CHAVENA
            quantity_helper = quantity_helper.replace("½", '')
        if "¼" in quantity_helper:
            total = 0.5 * CHAVENA
            quantity_helper = quantity_helper.replace("½", '')

        try:
            return UNITS_TYPE.MILILITROS.value, total + float(quantity_helper.strip()) * CHAVENA
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {quantity_helper}")
            return -1

    log.debug(f"Quantity_helper was unable to be parsed: {quantity_original.strip()}")
    print(f"Quantity_helper was unable to be parsed: {quantity_original.strip()}")
    return UNITS_TYPE.GRAMS.value, 0


def parse_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%YT%H:%M:%S")
        return date_obj
    except ValueError:
        raise ValueError("Invalid date format. Please use 'DD/MM/YYYYThh:mm:ss' format.")


def add_days(date_obj, days):
    new_date = date_obj + timedelta(days=days)
    return new_date
