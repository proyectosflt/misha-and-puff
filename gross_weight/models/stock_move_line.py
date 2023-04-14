from odoo import _, api, fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    _description = 'Stock Move Line'
    
    gross_weight = fields.Float('Peso bruto')
    cone_quantity = fields.Float('Cantidad de conos')