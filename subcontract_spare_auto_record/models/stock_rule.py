# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools import float_round


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_dest_id,
                               name, origin, company_id, values):
        move_values = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values)

        # Only the resupply move that directly feeds the raw move of a subcontracting MO
        # gets the extra quantity (so multi-step resupply routes don't compound the factor).
        dest_moves = values.get('move_dest_ids')
        if dest_moves and hasattr(dest_moves, 'raw_material_production_id'):
            productions = dest_moves.raw_material_production_id
            if productions and all(p.bom_id.type == 'subcontract' for p in productions):
                factor = float(self.env['ir.config_parameter'].sudo().get_param(
                    'subcontract_spare_auto_record.spare_factor', 1.05))
                if factor and factor != 1.0 and move_values.get('product_uom_qty'):
                    uom = product_uom
                    move_values['product_uom_qty'] = float_round(
                        move_values['product_uom_qty'] * factor,
                        precision_rounding=uom.rounding,
                        rounding_method='UP',
                    )
        return move_values
