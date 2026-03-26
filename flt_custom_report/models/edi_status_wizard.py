from odoo import models, fields, api


class EdiStatusWizard(models.TransientModel):
    _name = 'edi.status.wizard'
    _description = 'EDI Status Display Wizard'

    move_ids = fields.Many2many('account.move', string='Invoices')
    picking_ids = fields.Many2many('stock.picking', string='Pickings')
    edi_error_message = fields.Html(string='EDI Error Message', compute='_compute_edi_info')
    edi_web_services_to_process = fields.Char(string='EDI Web Services to Process', compute='_compute_edi_info')
    edi_error_count = fields.Integer(string='EDI Error Count', compute='_compute_edi_info')
    edi_blocking_level = fields.Selection([
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error')
    ], string='EDI Blocking Level', compute='_compute_edi_info')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='State', compute='_compute_edi_info')

    @api.depends('move_ids', 'picking_ids')
    def _compute_edi_info(self):
        for wizard in self:
            error_messages = []
            web_services = []
            total_errors = 0
            blocking_level = False
            state = False

            if wizard.move_ids:
                # Aggregate information from selected moves
                for move in wizard.move_ids:
                    if move.edi_error_message:
                        error_messages.append(f"<strong>{move.name}:</strong> {move.edi_error_message}")
                    if move.edi_web_services_to_process:
                        web_services.append(f"{move.name}: {move.edi_web_services_to_process}")
                    total_errors += move.edi_error_count or 0
                    
                    # Get the highest severity blocking level
                    if move.edi_blocking_level:
                        if not blocking_level:
                            blocking_level = move.edi_blocking_level
                        elif move.edi_blocking_level == 'error':
                            blocking_level = 'error'
                        elif move.edi_blocking_level == 'warning' and blocking_level != 'error':
                            blocking_level = 'warning'
                    
                    if not state:
                        state = move.state
            
            if wizard.picking_ids:
                for picking in wizard.picking_ids:
                    if picking.l10n_pe_edi_error:
                        error_messages.append(f"<strong>{picking.name}:</strong> {picking.l10n_pe_edi_error}")
                        total_errors += 1
                        if not blocking_level or blocking_level != 'error':
                            blocking_level = 'error'
                    
                    if not state:
                        if picking.state == 'done':
                            state = 'posted'
                        elif picking.state == 'cancel':
                            state = 'cancel'
                        else:
                            state = 'draft'

            wizard.edi_error_message = '<br/>'.join(error_messages) if error_messages else False
            wizard.edi_web_services_to_process = ', '.join(web_services) if web_services else False
            wizard.edi_error_count = total_errors
            wizard.edi_blocking_level = blocking_level
            wizard.state = state

    def button_process_edi_web_services(self):
        """Process EDI web services for all selected moves"""
        self.move_ids.button_process_edi_web_services()
        return {'type': 'ir.actions.act_window_close'}

    def action_retry_edi_documents_error(self):
        """Retry EDI documents for all selected moves"""
        if self.move_ids:
            self.move_ids.action_retry_edi_documents_error()
        if self.picking_ids:
            for picking in self.picking_ids:
                picking.action_send_delivery_guide()
        return {'type': 'ir.actions.act_window_close'}
