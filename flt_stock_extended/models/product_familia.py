from odoo import models, fields, api


class ProductFamilia(models.Model):
    _name = 'product.familia'
    _description = 'Familia de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)