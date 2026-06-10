from odoo import models, fields, api


class ProductTexto(models.Model):
    _name = 'product.texto'
    _description = 'Texto de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)