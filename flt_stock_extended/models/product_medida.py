from odoo import models, fields, api


class ProductMedida(models.Model):
    _name = 'product.medida'
    _description = 'Medida de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)