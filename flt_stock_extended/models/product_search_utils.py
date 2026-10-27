import json


PRODUCT_SEARCH_META_MARKER = '\n__FLT_PRODUCT_SEARCH_META__'


def format_product_search_result(record):
    metadata = json.dumps({
        'codificacion_anterior': record.codificacion_anterior or '',
        'product_template_id': record.product_template_id or '',
    }, ensure_ascii=False)
    return f'{record.display_name}{PRODUCT_SEARCH_META_MARKER}{metadata}'
