from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    temporada = fields.Char(string='Temporada')
    programa = fields.Char(string='Programa')
    planificador_line_ids = fields.One2many(
        'flt.planificador.line', 
        'sale_order_id', 
        string='Líneas de Planificación',
        readonly=True
    )
    # Añadir campos de prioridad
    pri_tp = fields.Integer(string='Pri T/P')
    pri_cp = fields.Integer(string='Pri C/P')