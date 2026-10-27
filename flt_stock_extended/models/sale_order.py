# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    tolerancia = fields.Float(
        string='Tolerancia',
        compute='_compute_tolerancia',
        store=True,
        readonly=False,
        copy=False,
        help='Tolerancia de venta tomada del producto'
    )

    @api.depends('product_id')
    def _compute_tolerancia(self):
        for line in self:
            if line.product_id:
                line.tolerancia = line.product_id.tolerancia_venta
            else:
                line.tolerancia = 0.0
