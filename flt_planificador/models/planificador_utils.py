import pytz

# Valor alto para que las prioridades vacías o en 0 queden al final
SORT_LAST = 999999


def local_date(dt, company):
    """Convierte un datetime UTC a fecha en la zona horaria de la compañía."""
    if not dt:
        return False
    tz = pytz.timezone(company.partner_id.tz or 'UTC')
    return pytz.utc.localize(dt).astimezone(tz).date()