# -*- coding: utf-8 -*-
from odoo import models, fields

class StockPackageType(models.Model):
    _inherit = 'stock.package.type'

    name = fields.Char(string='Tipo de Bolsa')
    base_weight = fields.Float(string='Tara bolsa', digits='Stock Weight')
    max_weight = fields.Float(digits='Stock Weight')
