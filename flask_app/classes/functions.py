import os
from datetime import datetime, timedelta, timezone

import requests
from flask_jwt_extended import get_jwt, jwt_required

from .models import UNITS_TYPE, NOTIFICATION_TYPE, TokenBlocklist, Notification
from ..ext.logger import log
import re

## parsing strings dd/mm/yyyy to dates

FCM_SERVER_KEY = os.environ.get('FMC_SERVER_KEY')

COLHER_DE_CHA = 4
COLHER_DE_SOPA = 14
COLHER_DE_SOBREMESA = 9
COLHER_DE_CAFE = 1.5
CHAVENA = 250

units_model = ['dente', 'folha', 'q.b.', 'ml', 'L', 'lata', 'fatia', 'g', 'gr', 'kg', 'cápsula', 'tira', 'tiras',
               'rodela', 'cabeça', 'unid', 'porção', 'ramo', 'frasco', 'pés', 'saqueta']


def normalize_quantity(quantity_original):
    # general stuff

    if "100 ml (+ 2 c. de sobremesa)" in quantity_original:
        print()
    # remover espaços
    quantity_original = quantity_original.strip()

    # trocar virgulas por pontos
    quantity_original = quantity_original.replace(",", ".")

    # remover +/- da string
    if "(±)" in quantity_original:
        quantity_original = quantity_original.replace("(±)", "").strip()
    if "±" in quantity_original:
        quantity_original = quantity_original.replace("±", "").strip()

    if "+-" in quantity_original:
        quantity_original = quantity_original.replace("+-", "").strip()

    # remover fractions
    if "½" in quantity_original or "1⁄2" in quantity_original:
        quantity_original = quantity_original.replace("½", "0.5")
        quantity_original = quantity_original.replace("1⁄2", "0.5")
        helper = quantity_original.split(" ")
        try:
            value = float(helper[0]) + float(helper[1])
            quantity_original = f'{value} {" ".join(helper[2:])}'
        except ValueError:
            pass
    if "¼" in quantity_original:
        quantity_original = quantity_original.replace("¼", "0.25")
        helper = quantity_original.split(" ")
        if helper[0].isdigit() and helper[1].isdigit():
            value = float(helper[0]) + float(helper[1])
            quantity_original = f'{value} {" ".join(helper[2:])}'

    ## more specific general stuff

    if quantity_original == "unid." or quantity_original == "1":
        quantity_original = "1 unid."

    if "q.b." in quantity_original:
        quantity_original = "1 q.b."

    # check for sums

    if "+" in quantity_original:
        helper = quantity_original.split("+", 1)
        helper2 = helper[1].strip().split(" ")
        try:
            value = float(helper[0]) + float(helper2[0])
            quantity_original = f'{value} {" ".join(helper[1:])}'
        except ValueError:
            pass

    # main split
    helper = quantity_original.split(" ", 1)

    value = helper[0].strip()
    units = helper[1].strip()

    extra_units = None
    extra_value_normalized = None

    if " (" in units:
        match = re.search(r'\(\s*([\d.]+)\s*(\D+)\s*\)', units)
        if match:
            units = units.split(" (")[0]
            if extra_units not in ['c. de chá', 'c. de sopa', 'c. de sobremesa', 'c. sobremesa', 'c. de café', 'cháv.']:
                extra_value_normalized, extra_units = match.groups()
        else:
            # the cases '(2x250g) (4x80 g)'
            pattern = r'\((\d+)x(\d+)\s*(\w+)\)'
            match = re.search(pattern, units)
            extra_value_normalized = 0
            if match:
                quantity, weight, extra_units = match.groups()
                extra_value_normalized += int(quantity) * int(weight)
                helper = units.split(" (")
                units = helper[0]
            else:
                helper = units.split(" (")
                units = helper[0]

    if 'c. de chá' in units:
        try:
            return UNITS_TYPE.GRAMS.value, float(value) * COLHER_DE_CHA, None, None
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed: {value}")
            return -1
    elif 'c. de sopa' in quantity_original:

        try:
            return UNITS_TYPE.GRAMS.value, float(value) * COLHER_DE_SOPA, None, None
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {value}")
            return -1
    elif 'c. de sobremesa' in quantity_original or 'c. sobremesa' in quantity_original:
        try:
            return UNITS_TYPE.GRAMS.value, float(value) * COLHER_DE_SOPA, None, None
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {value}")
            return -1
    elif 'c. de café' in quantity_original:

        try:
            return UNITS_TYPE.GRAMS.value, float(value) * COLHER_DE_CAFE, None, None
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {value}")
            return -1
    elif 'cháv.' in quantity_original:

        try:
            return UNITS_TYPE.MILILITROS.value, float(value) * CHAVENA, None, None
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {value}")
            return -1

    # deal whit extra

    if (extra_units == "g"):
        helper_var = units
        helper_var2 = value
        units = extra_units
        value = extra_value_normalized
        extra_units = helper_var
        extra_value_normalized = helper_var2

    # make evertthing in the same units

    if extra_units == "kg":
        extra_units = "g"
        extra_value_normalized = float(extra_value_normalized) * 1000
    if extra_units == "L":
        extra_units = "ml"
        extra_value_normalized = float(extra_value_normalized) * 1000

    if units == "kg":
        units = "g"
        value = float(value) * 1000
    if units == "L":
        units = "ml"
        value = float(value) * 1000

    return units, value, extra_units, extra_value_normalized


def parse_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%YT%H:%M:%S")
        return date_obj
    except ValueError:
        raise ValueError("Invalid date format. Please use 'DD/MM/YYYYThh:mm:ss' format.")


def add_days(date_obj, days):
    new_date = date_obj + timedelta(days=days)
    return new_date


notification_model = {
    'data': {
        'title': '',
        'message': ''
    },
    'to': ''
}

headers = {'Content-Type': 'application/json', 'Authorization': f'key={FCM_SERVER_KEY}'}


def push_notification(reciever_user, notification_type):
    if notification_type == NOTIFICATION_TYPE.FOLLOWED_USER.value:
        title = "Follow"
        message = "You have a new follower"

        notifcation_entry = Notification(title=title, message=message, user=reciever_user, type=notification_type)
        notifcation_entry.save()

        notification_model['data']['title'] = title
        notification_model['data']['message'] = message
        notification_model['to'] = reciever_user.fmc_token
    elif notification_type == NOTIFICATION_TYPE.FOLLOW_REQUEST.value:

        title = "Follow request"
        message = "You have a new follow request"

        notifcation_entry = Notification(title=title, message=message, user=reciever_user, type=notification_type)
        notifcation_entry.save()

        notification_model['data']['title'] = title
        notification_model['data']['message'] = message
        notification_model['to'] = reciever_user.fmc_token

    requests.post('https://fcm.googleapis.com/fcm/send', json=notification_model, headers=headers)



@jwt_required()
def block_user_session_id():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    token_block_record = TokenBlocklist(jti=jti, created_at=now)
    token_block_record.save()

