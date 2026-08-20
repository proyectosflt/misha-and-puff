from odoo import models, fields, api


class FltPlanificador(models.Model):
    _name = 'flt.planificador'
    _description = 'Planificación'

    name = fields.Char(
        string='Nombre',
        required=True,
        readonly=True,
        default=lambda self: f"Planificación {fields.Date.today().strftime('%Y-%m-%d')}"
    )
    date = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
        required=True
    )
    line_ids = fields.One2many(
        'flt.planificador.line',
        'planificador_id',
        string='Líneas de Planificación'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                date_val = vals.get('date') or fields.Date.today()
                vals['name'] = f"Planificación {date_val}"
        return super().create(vals_list)