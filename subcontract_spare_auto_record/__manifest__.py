{
    'name': 'Subcontracting: spare components + auto-register production',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing/Subcontracting',
    'summary': 'Send 5% extra components to the subcontractor and auto-register the subcontracting production when the receipt is created',
    'depends': ['purchase', 'mrp_subcontracting', 'flt_stock_extended'],
    'data': [
        'data/ir_config_parameter.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
