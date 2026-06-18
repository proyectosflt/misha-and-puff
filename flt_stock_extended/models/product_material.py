from odoo import models, fields, api


class ProductMaterial(models.Model):
    _name = 'product.material'
    _description = 'Material de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    familia_ids = fields.Many2many('product.familia', string='Familias')