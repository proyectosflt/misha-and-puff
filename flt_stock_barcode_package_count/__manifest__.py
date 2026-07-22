{
    'name': 'Barcode - Conteo de Paquetes',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Barcode',
    'summary': 'Verificación de presencia física de paquetes por producto sin realizar ajustes de inventario',
    'depends': ['stock', 'stock_barcode'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'stock_barcode_package_count/static/src/js/main_menu_patch.js',
            'stock_barcode_package_count/static/src/js/package_count_screen.js',
            'stock_barcode_package_count/static/src/xml/main_menu_patch.xml',
            'stock_barcode_package_count/static/src/xml/package_count_screen.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}