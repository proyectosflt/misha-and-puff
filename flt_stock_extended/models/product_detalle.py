from odoo import models, fields, api


class ProductDetalle(models.Model):
    _name = 'product.detalle'
    _description = 'Detalle de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)