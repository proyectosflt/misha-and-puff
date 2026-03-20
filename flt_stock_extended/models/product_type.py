# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductType(models.Model):
    _name = 'product.type'
    _description = 'Product Type'

    name = fields.Char(string='Name', required=True)