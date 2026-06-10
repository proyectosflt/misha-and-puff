from odoo import models, fields, api


class ProductTitle(models.Model):
    _name = 'product.title'
    _description = 'Título de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)