from odoo import models, fields, api


class ProductColor(models.Model):
    _name = 'product.color'
    _description = 'Color de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)