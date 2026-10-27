from odoo import models, fields, api


class ProductRubro(models.Model):
    _name = 'product.rubro'
    _description = 'Rubro de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    familia_ids = fields.Many2many('product.familia', string='Familias')