from odoo import models, fields, api


class ProductOtros(models.Model):
    _name = 'product.otros'
    _description = 'Otros Atributos de Producto'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)