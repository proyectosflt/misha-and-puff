from odoo import models, fields, api


class ProductTalla(models.Model):
    _name = 'product.talla'
    _description = 'Talla de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)