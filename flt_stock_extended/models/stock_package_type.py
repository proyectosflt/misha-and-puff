# -*- coding: utf-8 -*-
from odoo import models, fields

class StockPackageType(models.Model):
    _inherit = 'stock.package.type'

    base_weight = fields.Float(digits='Stock Weight')
    max_weight = fields.Float(digits='Stock Weight')
