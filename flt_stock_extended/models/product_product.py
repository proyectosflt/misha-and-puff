# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_type_id = fields.Many2one('product.type', string='Clasificación de producto')
    tara_cono = fields.Float(string='Tara Cono')
