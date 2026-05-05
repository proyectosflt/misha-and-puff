# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    cantidad_conos = fields.Integer(string="Conos", compute='_compute_totals', store=True)
    peso_bruto = fields.Float(string="Peso bruto", compute='_compute_totals', store=True, digits='Stock Weight')
    peso_neto = fields.Float(string="Peso neto", compute='_compute_totals', store=True, digits='Stock Weight')

    @api.depends('quant_ids', 'quant_ids.cantidad_conos', 'quant_ids.peso_bruto', 'quant_ids.peso_neto')
    def _compute_totals(self):
        for package in self:
            conos = 0
            bruto = 0.0
            neto = 0.0
            for quant in package.quant_ids:
                conos += quant.cantidad_conos
                bruto += quant.peso_bruto
                neto += quant.peso_neto
            package.cantidad_conos = conos
            package.peso_bruto = bruto
            package.peso_neto = neto
