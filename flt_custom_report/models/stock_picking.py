# -*- coding: utf-8 -*-
from odoo import models, _, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_open_edi_status_wizard(self):
        """Open wizard to display EDI status and errors"""
        return {
            'name': 'Estado Guía de Remisión Electrónica',
            'type': 'ir.actions.act_window',
            'res_model': 'edi.status.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_ids': [(6, 0, self.ids)]
            }
        }

    def l10n_pe_edi_action_download(self):
        """Download the zip/xml file attached to the picking."""
        self.ensure_one()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'stock.picking'),
            ('res_id', '=', self.id),
            ('name', 'ilike', '.xml'),
        ], limit=1)
        
        if not attachment:
             attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'stock.picking'),
                ('res_id', '=', self.id),
                ('name', 'ilike', '.zip'),
            ], limit=1)

        if not attachment:
            raise UserError(_("No hay un archivo xml o zip adjunto a la guía. Compruebe los archivos adjuntos directamente desde el chatter."))

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def action_validate_or_process_edi(self):
            """Validate picking and process EDI for delivery guide"""
            for picking in self:
                # Skip if already cancelled
                if picking.state == 'cancel':
                    continue
                
                # Validate the picking if not done yet
                if picking.state != 'done':
                    # Set all move quantities to demand quantity
                    for move in picking.move_ids_without_package:
                        if move.product_uom_qty > 0:
                            move.quantity = move.product_uom_qty
                    
                    # Validate the picking
                    picking.button_validate()
                
                # Process EDI if not already sent
                if picking.state == 'done' and not picking.l10n_pe_edi_status:
                    picking.action_send_delivery_guide()
            
            return True