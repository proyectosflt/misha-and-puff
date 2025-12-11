# -*- coding: utf-8 -*-
from odoo import api, models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    cantidad_conos = fields.Integer(string="Conos")
    tara_bolsa = fields.Float(string="Tara bolsa", compute='_compute_tara_bolsa', store=True)
    tara_cono = fields.Float(string="Tara cono")
    peso_bruto = fields.Float(string="Peso bruto")

    @api.depends('result_package_id.package_type_id.base_weight')
    def _compute_tara_bolsa(self):
        for record in self:
            if not record.tara_bolsa:
                record.tara_bolsa = record.result_package_id.package_type_id.base_weight or 0.0
