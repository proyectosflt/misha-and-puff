{
    'name': 'FLT Planificador',
    'version': '18.0.1.0.0',
    'category': 'Sales/Inventory',
    'summary': 'Gestión de planificaciones para Ventas e Inventario',
    'depends': ['base', 'sale_management', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/flt_planificador_views.xml',
        'views/flt_planificador_menus.xml',
        "views/flt_planificador_inherited_views.xml",
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}