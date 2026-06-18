from odoo import models, fields, api


class ProductModel(models.Model):
    _name = 'product.model'
    _description = 'Modelo de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    familia_ids = fields.Many2many('product.familia', string='Familias')