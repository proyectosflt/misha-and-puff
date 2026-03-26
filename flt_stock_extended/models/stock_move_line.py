# -*- coding: utf-8 -*-
from odoo import api, models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    cantidad_conos = fields.Integer(string="Conos")
    cono_id = fields.Many2one('tipo.cono', string='Tipo de Cono')
    tara_bolsa = fields.Float(string="Tara bolsa", compute='_compute_tara_bolsa', store=True, readonly=False)
    tara_cono = fields.Float(string="Tara cono", compute='_compute_tara_cono', store=True, readonly=False)
    peso_bruto = fields.Float(string="Peso bruto")
    peso_neto = fields.Float(string="Peso neto", compute='_compute_peso_neto', store=True, readonly=False)

    @api.depends('result_package_id.package_type_id.base_weight')
    def _compute_tara_bolsa(self):
        for record in self:
            if not record.tara_bolsa:
                record.tara_bolsa = record.result_package_id.package_type_id.base_weight or 0.0

    @api.depends('cono_id.tara_cono')
    def _compute_tara_cono(self):
        for record in self:
            if not record.tara_cono:
                record.tara_cono = record.cono_id.tara_cono or 0.0

    @api.depends('peso_bruto', 'tara_bolsa', 'tara_cono', 'cantidad_conos')
    def _compute_peso_neto(self):
        for record in self:
            if not record.exists():
                continue
            try:
                value = (record.peso_bruto or 0.0) - (record.tara_bolsa or 0.0) - ((record.tara_cono or 0.0) * (record.cantidad_conos or 0))
                record.peso_neto = value
                if value != 0:
                    record.quantity = value
            except Exception:
                continue

    def action_duplicar(self):
        for record in self:
            record.copy({
                'result_package_id': False,
                'peso_bruto': 0.0,
                'peso_neto': 0.0,
                'quantity': 0.0,
            })

    def _action_done(self):
        """Override to pass custom fields in context for stock.quant updates"""
        for ml in self:
            # Pass the custom field values and location/package info in context
            ctx = dict(ml.env.context or {})
            ctx.update({
                'quant_cantidad_conos': ml.cantidad_conos or 0,
                'quant_peso_bruto': ml.peso_bruto or 0.0,
                'quant_peso_neto': ml.peso_neto or 0.0,
                'move_line_location_id': ml.location_id.id,
                'move_line_location_dest_id': ml.location_dest_id.id,
                'move_line_package_id': ml.package_id.id if ml.package_id else False,
                'move_line_result_package_id': ml.result_package_id.id if ml.result_package_id else False,
            })
            super(StockMoveLine, ml.with_context(ctx))._action_done()
        return True
