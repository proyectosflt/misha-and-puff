from odoo import api, models, fields

from .planificador_utils import SORT_LAST, local_date


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
    # Añadir campos de prioridad
    pri_tp = fields.Integer(string='Pri T/P')
    pri_cp = fields.Integer(string='Pri C/P')

    # Campos técnicos para el orden por defecto de la lista
    scheduled_day = fields.Date(
        string='Día Programado',
        compute='_compute_scheduled_day',
        store=True,
        index=True,
    )
    @api.depends('scheduled_date', 'company_id')
    def _compute_scheduled_day(self):
        for rec in self:
            rec.scheduled_day = local_date(rec.scheduled_date, rec.company_id)
            
    no_priority = fields.Boolean(compute='_compute_pri_sort', store=True, index=True)
    pri_tp_sort = fields.Integer(compute='_compute_pri_sort', store=True, index=True)
    pri_cp_sort = fields.Integer(compute='_compute_pri_sort', store=True, index=True)

    @api.depends('pri_tp', 'pri_cp')
    def _compute_pri_sort(self):
        for rec in self:
            rec.no_priority = not rec.pri_tp and not rec.pri_cp
            rec.pri_tp_sort = rec.pri_tp or SORT_LAST
            rec.pri_cp_sort = rec.pri_cp or SORT_LAST