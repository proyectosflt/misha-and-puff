# -*- coding: utf-8 -*-
from odoo import api, models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    cantidad_conos = fields.Integer(string="Conos")
    tara_bolsa = fields.Float(string="Tara bolsa", compute='_compute_tara_bolsa', store=True, readonly=False)
    tara_cono = fields.Float(string="Tara cono", compute='_compute_tara_cono', store=True, readonly=False)
    peso_bruto = fields.Float(string="Peso bruto")
    peso_neto = fields.Float(string="Peso neto")

    @api.depends('result_package_id.package_type_id.base_weight')
    def _compute_tara_bolsa(self):
        for record in self:
            if not record.tara_bolsa:
                record.tara_bolsa = record.result_package_id.package_type_id.base_weight or 0.0

    @api.depends('product_id.tara_cono')
    def _compute_tara_cono(self):
        for record in self:
            if not record.tara_cono:
                record.tara_cono = record.product_id.tara_cono or 0.0

    def action_calcular(self):
        for record in self:
            value = (record.peso_bruto or 0.0) - (record.tara_bolsa or 0.0) - ((record.tara_cono or 0.0) * (record.cantidad_conos or 0))
            record.peso_neto = value
            record.quantity = value

    def _action_done(self):
        """Override to pass custom fields in context for stock.quant updates"""
        for ml in self:
            # Pass the custom field values in context
            ctx = dict(ml.env.context or {})
            ctx.update({
                'quant_cantidad_conos': ml.cantidad_conos or 0,
                'quant_peso_bruto': ml.peso_bruto or 0.0,
                'quant_peso_neto': ml.peso_neto or 0.0,
            })
            super(StockMoveLine, ml.with_context(ctx))._action_done()
        return True
