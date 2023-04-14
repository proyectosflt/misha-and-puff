from odoo import _, api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move'
    
    gross_weight = fields.Float('Peso bruto')
    cone_quantity = fields.Float('Cantidad de conos')