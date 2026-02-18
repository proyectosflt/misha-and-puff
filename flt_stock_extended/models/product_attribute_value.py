from odoo import models, fields, api

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    nombre = fields.Char(string='Nombre')
    color_family_id = fields.Many2one('color.family', string='Familia de Color')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_color_attribute') and 'attribute_id' not in res:
            color_attr = self.env['product.attribute'].search([('name', '=', 'Color')], limit=1)
            if color_attr:
                res['attribute_id'] = color_attr.id
        return res
