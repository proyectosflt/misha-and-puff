{
    'name': 'Barcode - Conteo de Paquetes',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Barcode',
    'summary': 'Verificación de presencia física de paquetes por producto',
    'depends': ['stock', 'stock_barcode'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'stock_barcode_package_count/static/src/js/**/*.js',
            'stock_barcode_package_count/static/src/xml/**/*.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}