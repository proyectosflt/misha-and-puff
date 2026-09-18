# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    numero_guia_remision = fields.Char(
        string='Número guía de remisión',
        help='Número de la guía de remisión'
    )

    def _notify_administrators(self, group_xml_id, title, message):
        """Helper method to send an activity notification to all users in a specific group"""
        group = self.env.ref(group_xml_id)
        if not group:
            return
            
        model_id = self.env['ir.model']._get(self._name).id
        
        # Open a completely separate database cursor
        with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
            # Create a new environment using this new cursor
            new_env = odoo.api.Environment(new_cr, self.env.uid, self.env.context)
            
            for user in group.users:
                new_env['mail.activity'].create({
                    'res_id': self.id,
                    'res_model_id': model_id,
                    'activity_type_id': new_env.ref('mail.mail_activity_data_todo').id,
                    'summary': title,
                    'note': f'<p>{message}</p>',
                    'user_id': user.id,
                })

    def _is_fully_validated(self):
        """El albarán está listo para validarse cuando todos sus movimientos
        (sin contar los cancelados) están validados."""
        self.ensure_one()
        if self.state in ('done', 'cancel'):
            return False
        moves = self.move_ids.filtered(lambda m: m.state != 'cancel')
        return bool(moves) and all(m.validation_state == 'validated' for m in moves)

    def button_validate(self):
        for picking in self:
            picking.move_ids.filtered(lambda m: m.state != 'cancel')._check_tolerancia()
        return super(StockPicking, self.with_context(flt_bypass_line_lock=True)).button_validate()
