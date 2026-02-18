from odoo import models, fields

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    nombre = fields.Char(string='Nombre')
    color_family_id = fields.Many2one('color.family', string='Familia de Color')
