# -*- coding: utf-8 -*-
{
    'name': "Stock Package Scan",
    'summary': "Scan packages that contain a given product, barcode-app style.",
    'description': """
Stock Package Scan
===================
Open a scanning session, scan (or type) a product's barcode to list every
package that currently holds that product, then scan each package to check
it off the list. Built to feel like the built-in Barcode app: one input,
one screen, instant visual feedback per line.
""",
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'barcode',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_package_scan_sequence.xml',
        'views/stock_package_scan_views.xml',
        'views/stock_package_scan_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_package_scan/static/src/client_action/*.js',
            'stock_package_scan/static/src/client_action/*.xml',
            'stock_package_scan/static/src/client_action/*.scss',
        ],
    },
    'installable': True,
    'application': True,
}
