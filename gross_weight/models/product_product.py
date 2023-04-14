from odoo import _, api, fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'
    _description = 'Product Product'
    
    gross_weight = fields.Float('Peso bruto')
    cone_quantity = fields.Float('Cantidad de conos')