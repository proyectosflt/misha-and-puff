# -*- coding: utf-8 -*-
from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _auto_record_subcontracting(self):
        """Do what the 'Registrar producción' wizard does, for the full ordered quantity.

        Skipped (left for manual registration) when the finished product or any component
        is tracked by lot/serial, since those need user input.
        """
        for production in self:
            if production.state in ('draft', 'done', 'cancel'):
                continue
            if production.subcontracting_has_been_recorded:
                continue
            if production.product_tracking != 'none':
                continue
            if any(m.product_id.tracking != 'none' for m in production.move_raw_ids):
                continue
            production.qty_producing = production.product_qty
            production._set_qty_producing()
            production.move_raw_ids.filtered(lambda m: m.quantity).picked = True
            production.subcontracting_record_component()
