# -*- coding: utf-8 -*-
{
    'name': 'Stock Extended',
    'category': 'Stock',
    'summary': 'Add new features to stock module',
    'depends': ['stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_line.xml',
        'views/stock_picking_views.xml',
        'views/product_template_views.xml',
        'views/product_product.xml',
        'views/report_package_barcode.xml',
        'views/stock_quant.xml',
        'views/stock_quant_package.xml',
        'views/color_family_views.xml',
        'views/product_attribute_value_views.xml',
        'views/tipo_cono_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
