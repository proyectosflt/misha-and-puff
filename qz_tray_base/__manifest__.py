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
    "name"          : "QZ Tray Base for Odoo",
    "summary"       : """QZ Tray Base : This module acts as the base for all QZ Tray related modules.  Install our utility modules to fully utilize the printing features. qz tray odoo | odoo qz tray base | odoo qz tray printing | odoo pos qz tray | odoo local printer integration | odoo direct printing | qz tray integration with odoo | odoo qz tray printing module | odoo pos local printer qz tray  qz tray report | qz tray zpl reports | qz tray product label | qz tary tugit | qztray tugit | qztray base | qz tray connector | qztray connector |
    """,
    "description"   : """QZ Tray Base is a foundational module required to support printing related features using QZ Tray. 
    It enables seamless communication between Odoo and local printers when used together with our utility modules.
    """,
    "version"       : "18.0.1.0.0",
    "author"        : "TugIT Software",
    "company"       : "TugIT Software",
    "maintainer"    : "TugIT Software",
    "license"       : "OPL-1",
    "website"       : "https://tugit.in",
    "sequence"      : 6,
    "category"      : "Extra Tools",
    "depends"       : ['web'],
    "data"          : [],
    "assets"        : {
                    "web.assets_backend":[
                        "qz_tray_base/static/src/js/qz_tray_lib.js",
                        "qz_tray_base/static/src/js/qz.js",
                    ],
    },
    "images"        : ['static/description/banner.png'],
    "application"   : True,
    "installable"   : True,
    "auto_install"  : False,
    "support"       : "info@tugit.in",
    "price"         : 4,
    "currency"      : "USD",
}
