# -*- coding: utf-8 -*-
{
    'name': 'Stock Extended',
    'category': 'Stock',
    'summary': 'Add new features to stock module',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_line.xml',
        'views/product_product.xml',
        'views/report_package_barcode.xml',
        'views/stock_quant.xml',
        'views/stock_quant_package.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
