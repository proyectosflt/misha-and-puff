from odoo import _, api, fields, models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Stock Picking'
    
    def button_validate(self):
        for record in self:
            move_ids_without_package = record.move_ids_without_package
            no_value = all(move_ids_without_package.mapped(lambda r: r.cone_quantity != 0) + move_ids_without_package.mapped(lambda r: r.gross_weight != 0))
            if not no_value:
                raise UserError('La cantidad de conos y el peso bruto es requerido.')
        return super().button_validate()