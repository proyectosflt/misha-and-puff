# -*- coding: utf-8 -*-
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_confirm(self, merge=True, merge_into=False):
        moves = super()._action_confirm(merge=merge, merge_into=merge_into)
        if not self.env.context.get('skip_subcontract_auto_record'):
            subcontract_moves = moves.filtered(
                lambda m: m.is_subcontract and m.state not in ('done', 'cancel'))
            if subcontract_moves:
                subcontract_moves.move_orig_ids.production_id._auto_record_subcontracting()
        return moves
