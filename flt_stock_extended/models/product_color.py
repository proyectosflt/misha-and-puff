from odoo import models, fields, api


class ProductColor(models.Model):
    _name = 'product.color'
    _description = 'Color de Producto'
    _rec_name = 'codigo'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Char(string='Código', required=True)
    color_family_id = fields.Many2one('color.family', string='Familia de Color')
    familia_ids = fields.Many2many('product.familia', string='Familias')

    @api.model
    def default_get(self, fields_list):
        """Al crear desde un campo Many2one el texto escrito es el código, no el nombre."""
        res = super().default_get(fields_list)
        typed_value = self.env.context.get('default_name')
        if typed_value and 'codigo' in fields_list and not self.env.context.get('default_codigo'):
            res['codigo'] = typed_value
            res['name'] = False
        return res