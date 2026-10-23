# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    subcontract_return_origin_id = fields.Many2one(
        'stock.picking',
        string='Reception',
        copy=False,
        readonly=True,
        index='btree_not_null',
        help="Reception that triggered the creation of this unused-components return.",
    )
    subcontract_return_ids = fields.One2many(
        'stock.picking',
        'subcontract_return_origin_id',
        string='Unused Component Returns',
    )
    subcontract_return_count = fields.Integer(
        string='Unused Component Returns',
        compute='_compute_subcontract_return_count',
    )

    subcontract_return_po_id = fields.Many2one(
        'purchase.order',
        string='Subcontract Return of',
        copy=False,
        readonly=True,
        index='btree_not_null',
        help="Purchase order whose unused subcontracting components this transfer returns.",
    )

    @api.depends('subcontract_return_ids')
    def _compute_subcontract_return_count(self):
        for picking in self:
            picking.subcontract_return_count = len(picking.subcontract_return_ids)

    def action_view_subcontract_returns(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Unused Component Returns'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.subcontract_return_ids.ids)],
            'context': {'create': False},
        }
        if len(self.subcontract_return_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.subcontract_return_ids.id,
            })
        return action

    def _action_done(self):
        res = super()._action_done()
        receipts = self.filtered(
            lambda picking: picking.picking_type_code == 'incoming' and picking.state == 'done'
        )
        for receipt in receipts:
            orders = receipt.move_ids.purchase_line_id.order_id
            if orders:
                orders._create_subcontract_unused_components_return(last_receipt=receipt)
        return res
