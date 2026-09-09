# -*- coding: utf-8 -*-
{
    'name': "Escaneo de paquetes",
    'summary': "Escanee paquetes que contienen un producto determinado, estilo de aplicación de código de barras.",
    'description': """
Escaneo de paquetes
===================
Abra una sesión de escaneo, escanee (o escriba) el código de barras de un
producto para listar todos los paquetes que lo contienen actualmente y luego
escanee cada paquete para marcarlo como completado. Diseñado para sentirse
como la aplicación de códigos de barras integrada: una entrada, una pantalla,
retroalimentación visual instantánea por línea.
""",
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'stock_barcode',
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
