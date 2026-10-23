# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    subcontract_return_po_id = fields.Many2one(
        'purchase.order',
        string='Subcontract Return of',
        copy=False,
        readonly=True,
        index='btree_not_null',
        help="Purchase order whose unused subcontracting components this transfer returns.",
    )

    def _action_done(self):
        res = super()._action_done()
        receipts = self.filtered(lambda p: p.picking_type_code == 'incoming')
        orders = receipts.move_ids.filtered('is_subcontract').purchase_line_id.order_id
        if orders:
            orders._create_subcontract_unused_components_return()
        return res
