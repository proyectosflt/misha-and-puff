{
    'name': 'Custom Report',
    'summary': 'Custom reports for Valvosanitaria',
    'version': '1.0',
    'category': 'Accounting',
    'author': 'Samuel Gomez - FLT',
    'depends': ['account', 'stock','l10n_pe_edi', 'dv_l10n_pe_edi_stock_template'],
    'data': [
        'security/ir.model.access.csv',
        'views/report_invoice.xml',
        'views/external_layout_guide_remission_letter.xml',
        'views/report_guide_remission.xml',
        'views/edi_status_wizard_views.xml',
        'views/account_move_views.xml',
        # 'views/documents_menu.xml',
        # 'views/custom_ubl_templates.xml',
        # 'views/stock_picking_edi.xml',
        'views/stock_picking_views.xml',
        # 'views/res_company_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
