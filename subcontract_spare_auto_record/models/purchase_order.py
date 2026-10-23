# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import Command, _, models
from odoo.tools import float_compare


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _create_subcontract_unused_components_return(self):
        """Create (in draft) a transfer returning the components sent to the subcontractor
        and not consumed, once the PO has no more pending subcontract receipts.

        Everything is computed from this PO only:
            to return = sent in the resupply transfers linked to this PO
                        - what the BOM says the total received quantity should have consumed
        The stock currently at the subcontracting location is never looked at.
        """
        Picking = self.env['stock.picking'].sudo()
        for order in self.sudo():
            po_moves = order.order_line.move_ids.filtered('is_subcontract')
            if not po_moves:
                continue
            # Still waiting for more receipts (a backorder exists) -> not yet.
            if po_moves.filtered(lambda m: m.state not in ('done', 'cancel')):
                continue
            done_moves = po_moves.filtered(lambda m: m.state == 'done')
            if not done_moves:
                continue
            # Already generated for this PO.
            if Picking.search_count([
                ('subcontract_return_po_id', '=', order.id),
                ('state', '!=', 'cancel'),
            ]):
                continue

            # 1) What should have been consumed, based on the BOM and the total received.
            expected = defaultdict(float)
            for move in done_moves:
                bom = move.move_orig_ids.production_id[:1].bom_id or move._get_subcontract_bom()
                if not bom:
                    continue
                qty_in_bom_uom = move.product_uom._compute_quantity(move.quantity, bom.product_uom_id)
                _boms, lines = bom.explode(
                    move.product_id, qty_in_bom_uom / bom.product_qty, picking_type=bom.picking_type_id)
                for line, data in lines:
                    expected[line.product_id.id] += line.product_uom_id._compute_quantity(
                        data['qty'], line.product_id.uom_id)

            # 2) What was actually sent to the subcontractor for this PO (all its MOs,
            #    including backorders; the union of records avoids double counting).
            resupply_moves = po_moves.move_orig_ids.production_id.move_raw_ids.move_orig_ids.filtered(
                lambda m: m.state == 'done')
            sent = defaultdict(float)
            reference_move = {}
            for move in resupply_moves:
                sent[move.product_id.id] += move.product_uom._compute_quantity(
                    move.quantity, move.product_id.uom_id)
                reference_move.setdefault(move.product_id.id, move)

            # 3) Difference -> lines of the return transfer, grouped by type/locations.
            groups = defaultdict(list)
            for product_id, sent_qty in sent.items():
                product = self.env['product.product'].sudo().browse(product_id)
                diff = sent_qty - expected.get(product_id, 0.0)
                if float_compare(diff, 0.0, precision_rounding=product.uom_id.rounding) <= 0:
                    continue
                ref = reference_move[product_id]
                picking_type = ref.picking_id.picking_type_id
                picking_type = picking_type.return_picking_type_id or picking_type
                key = (picking_type.id, ref.location_dest_id.id, ref.location_id.id)
                groups[key].append((product, diff))

            created = Picking
            for (picking_type_id, src_id, dest_id), items in groups.items():
                origin = _("Unused components return - %s", order.name)
                created |= Picking.with_company(order.company_id).create({
                    'picking_type_id': picking_type_id,
                    'partner_id': order.partner_id.id,
                    'location_id': src_id,
                    'location_dest_id': dest_id,
                    'origin': origin,
                    'company_id': order.company_id.id,
                    'subcontract_return_po_id': order.id,
                    'move_ids': [Command.create({
                        'name': product.display_name,
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'product_uom_qty': qty,
                        'location_id': src_id,
                        'location_dest_id': dest_id,
                        'picking_type_id': picking_type_id,
                        'company_id': order.company_id.id,
                        'origin': origin,
                    }) for product, qty in items],
                })
            if created:
                order.message_post(body=_(
                    "Draft transfer created to return the unused subcontracting components: %s",
                    ", ".join(created.mapped('name'))))
