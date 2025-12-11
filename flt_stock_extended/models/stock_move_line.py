# -*- coding: utf-8 -*-
from odoo import api, models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    cantidad_conos = fields.Integer(string="Conos")
    tara_bolsa = fields.Float(string="Tara bolsa", compute='_compute_tara_bolsa', store=True, readonly=False)
    tara_cono = fields.Float(string="Tara cono", compute='_compute_tara_cono', store=True, readonly=False)
    peso_bruto = fields.Float(string="Peso bruto")
    peso_neto = fields.Float(string="Peso neto")

    def _compute_tara_bolsa(self):
        for record in self:
            if not record.tara_bolsa:
                record.tara_bolsa = record.result_package_id.package_type_id.base_weight or 0.0

    def _compute_tara_cono(self):
        for record in self:
            if not record.tara_cono:
                record.tara_cono = record.product_id.tara_cono or 0.0

    def action_calcular(self):
        for record in self:
            value = (record.peso_bruto or 0.0) - (record.tara_bolsa or 0.0) - ((record.tara_cono or 0.0) * (record.cantidad_conos or 0))
            record.peso_neto = value
            record.quantity = value
