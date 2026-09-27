from odoo import api, models, fields

from .planificador_utils import SORT_LAST, local_date


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

    # Campos técnicos para el orden por defecto de la lista
    commitment_day = fields.Date(
        string='Día de Entrega',
        compute='_compute_commitment_day',
        store=True,
        index=True,
    )
    pri_tp_sort = fields.Integer(compute='_compute_pri_sort', store=True, index=True)
    pri_cp_sort = fields.Integer(compute='_compute_pri_sort', store=True, index=True)

    @api.depends('commitment_date', 'company_id')
    def _compute_commitment_day(self):
        for rec in self:
            rec.commitment_day = local_date(rec.commitment_date, rec.company_id)

    @api.depends('pri_tp', 'pri_cp')
    def _compute_pri_sort(self):
        for rec in self:
            rec.pri_tp_sort = rec.pri_tp or SORT_LAST
            rec.pri_cp_sort = rec.pri_cp or SORT_LAST