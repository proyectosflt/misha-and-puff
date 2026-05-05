# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    numero_guia_remision = fields.Char(
        string='Número guía de remisión',
        help='Número de la guía de remisión'
    )

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super(StockPicking, self).create(vals_list)
        for picking in pickings:
            picking._assign_item_numbers()
        return pickings

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if 'move_ids_without_package' in vals or 'move_line_ids_without_package' in vals:
            for picking in self:
                picking._assign_item_numbers()
        return res

    def _assign_item_numbers(self):
        for picking in self:
            for i, move in enumerate(picking.move_ids_without_package, 1):
                if move.item_number != i:
                    move.item_number = i
