from odoo import models, fields

class ColorFamily(models.Model):
    _name = 'color.family'
    _description = 'Familia de Colores'

    name = fields.Char(string='Nombre', required=True)
