# -*- coding: utf-8 -*-
from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    numero_guia_remision = fields.Char(
        string='Número guía de remisión',
        help='Número de la guía de remisión'
    )
