# -*- coding: utf-8 -*-
#############################################################################
#
#    TugIT Software
#
#    Copyright © 2026 TugIT. All rights reserved.
#    Author: TugIT <info@tugit.in>
#
#    You should have received a copy of the LICENSE along with this program.
#
#############################################################################
{
    "name"          : "Product Label & ZPL Report Direct Print",
    "summary"       : """Directlly send Product label or ZPL Report for printing. This module allows you to directly send ZPL reports for printing without downloading. It enables fast and reliable printing of ZPL based labels and reports from Odoo.  Zebra printer label printing | Label printing module Zebra | Zebra printer module for labels | Zebra thermal printer support | Thermal label printing Zebra printer | Zebra label printer | Zebra printer | Zebra barcode label printing | Barcode label printing Zebra | Print product labels Zebra | Zebra printer integration for product labels | Print shipping labels Zebra printer | Shipping label printing from Zebra printer | Print warehouse labels Zebra printer | Print location labels Zebra | Product, location, shipping label printer | Odoo Zebra label printing module | Automatic label printing Zebra | Multi-label printing Zebra | print product label direct printer | print stock lot label | zpl lot | zpl product label printer | zpl label direct printing | zpl report print direct print | zpl shipping label print | zpl raw printing odoo | zebra zpl report print |  odoo zpl printing | odoo zpl label printing | odoo zpl report printing | odoo zpl report direct print | direct zpl printing odoo | direct zpl printing in odoo | odoo direct zpl printing | odoo zpl shipping label print | odoo shipping label zpl | odoo barcode label zpl | odoo warehouse label print | odoo delivery label printing | odoo label direct printing | odoo report direct print | odoo printing without download |  qz tray odoo | qz tray base | qz tray connector | qztray connector | qztray base | qztray tugit | qz tray tugit | tugit qz tray odoo | qz tray integration with odoo | odoo qz tray base | odoo qz tray printing | odoo qz tray printing module | odoo qz tray zpl | zpl printer |  odoo qz tray direct print | qz tray zpl printing | qz tray zpl printing in odoo | qz tray zpl report | qz tray zpl reports | qz tray report | qz tray report printing | qz tray label printing | qz tray product label direct printing | qz tray shipping label | qz tray delivery label |  odoo local printer integration | odoo direct printing | odoo pos direct printing | odoo pos qz tray | odoo pos local printer qz tray |  odoo zpl preview | preview zpl attachments in odoo | preview zpl attachment | preview zpl file | preview zebra label | preview shipping label | preview delivery labels | preview label | preview attachment | preview document | preview doc | sticker printer | print sticker label | product sticker
    """,
    "description"   : """This module allows you to directly send ZPL reports for printing without downloading or manual intervention. 
    It enables fast and reliable printing of ZPL based labels and reports from Odoo.
    """,
    "version"       : "18.0.1.0.0",
    "author"        : "TugIT Software",
    "company"       : "TugIT Software",
    "maintainer"    : "TugIT Software",
    "license"       : "OPL-1",
    "website"       : "https://tugit.in",
    "sequence"      : 8,
    "category"      : "Extra Tools",
    "depends"       : ['qz_tray_base_v18'],
    "data"          : [],
    "assets"        : {
                    "web.assets_backend":[
                        "qz_tray_report_v18/static/src/js/*",
                    ],
    },
    "images"        : ['static/description/banner.gif'],
    "application"   : True,
    "installable"   : True,
    "auto_install"  : False,
    "support"       : "info@tugit.in",
    "price"         : 25,
    "currency"      : "USD",
}
