from odoo import models, _, api
from odoo.exceptions import UserError
import logging

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_open_edi_status_wizard(self):
        """Open wizard to display EDI status and errors"""
        return {
            'name': 'Estado Factura Electrónica',
            'type': 'ir.actions.act_window',
            'res_model': 'edi.status.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_ids': [(6, 0, self.ids)]
            }
        }

    def action_export_edi_xml(self):
        """Download the zip file attached to the invoice."""
        self.ensure_one()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.id),
            ('name', 'ilike', '.zip'),
        ], limit=1)

        if not attachment:
            raise UserError(_("No hay un zip adjunto a la factura. Compruebe los archivos adjuntos directamente desde el chatter de la factura."))

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def action_post_or_process_edi(self):
            for move in self:
                if move.state == 'draft':
                    move.action_post()
                if move.state == 'posted':
                    edi_error_count = move.edi_error_count 
                    edi_blocking_level = move.edi_blocking_level
                    if edi_error_count != 0 and edi_blocking_level == 'error':
                        move.action_retry_edi_documents_error()
                    else:
                        move.button_process_edi_web_services()
            return True