# -*- coding: utf-8 -*-
from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    cantidad_conos = fields.Integer(string="Conos")
