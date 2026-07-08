# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    tolerancia = fields.Float(
        string='Tolerancia',
        compute='_compute_tolerancia',
        store=True,
        readonly=False,
        help='Tolerancia de compra tomada del producto'
    )

    @api.depends('product_id')
    def _compute_tolerancia(self):
        for line in self:
            if line.product_id:
                line.tolerancia = line.product_id.tolerancia_compra
            else:
                line.tolerancia = 0.0
