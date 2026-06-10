# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductType(models.Model):
    _name = 'product.type'
    _description = 'Tipo de Producto'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)