from odoo import models, fields, api


class ProductColor(models.Model):
    _name = 'product.color'
    _description = 'Color de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    color_family_id = fields.Many2one('color.family', string='Familia de Color')
    familia_ids = fields.Many2many('product.familia', string='Familias') 