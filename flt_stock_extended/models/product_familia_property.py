from odoo import models, fields

class ProductFamiliaProperty(models.Model):
    _name = 'product.familia.property'
    _description = 'Propiedad de Familia de Producto'
    _order = 'sequence'

    familia_id = fields.Many2one('product.familia', string='Familia', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Secuencia', default=10)
    property_field = fields.Selection([
        ('product_rubro_id', 'Rubro'),
        ('product_material_id', 'Material'),
        ('product_detalle_id', 'Detalle'),
        ('product_titulo_id', 'Título'),
        ('product_type_id', 'Tipo'),
        ('product_model_id', 'Modelo'),
        ('product_tenido_id', 'Teñido'),
        ('product_color_id', 'Color'),
        ('product_medida_id', 'Medida'),
        ('product_texto_id', 'Texto'),
        ('product_talla_id', 'Talla'),
        ('product_otros_id', 'Otros Atributos'),
    ], string='Propiedad', required=True)
