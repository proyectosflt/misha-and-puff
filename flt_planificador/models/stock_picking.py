from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    temporada = fields.Char(string='Temporada')
    programa = fields.Char(string='Programa')
    planificador_line_ids = fields.Many2many(
        'flt.planificador.line', 
        'flt_planificador_picking_rel', 
        'picking_id', 
        'line_id', 
        string='Líneas de Planificación',
        readonly=True
    )