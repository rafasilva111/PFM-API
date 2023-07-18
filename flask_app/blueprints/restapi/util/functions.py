from ....ext.logger import log


COLHER_DE_CHA = 4

def normalize_quantity(quantity_original):
    if 'g' in quantity_original:
        return float(quantity_original.replace('g', '').strip())

    if 'gr' in quantity_original:
        return float(quantity_original.replace('g', '').strip())

    if 'c. de chá' in quantity_original:
        quantity_helper = quantity_original.replace('c. de chá', '')
        total = float(0)
        if "½" in quantity_helper:
            total = 0.5 * COLHER_DE_CHA
            quantity_helper = quantity_helper.replace("½", '')
        try:
            total = total + float(quantity_helper.strip()) * COLHER_DE_CHA
        except:
            # Se o quantity_helper não der para ser parsed
            log.debug(f"Quantity_helper was unable to be parsed {quantity_helper.strip()}")
            pass

        return total