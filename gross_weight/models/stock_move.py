from odoo import _, api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move'
    
    gross_weight = fields.Float('Peso bruto', compute='_quantity_gross_weight_cone_compute')
    cone_quantity = fields.Float('Cantidad de conos', compute='_quantity_gross_weight_cone_compute')

    @api.depends('move_line_ids.gross_weight', 'move_line_ids.cone_quantity')
    def _quantity_gross_weight_cone_compute(self):
        for move in self:
            move.gross_weight = sum(move.move_line_ids.mapped(lambda r: r.gross_weight))
            move.cone_quantity = sum(move.move_line_ids.mapped(lambda r: r.cone_quantity))