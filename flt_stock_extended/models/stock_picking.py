# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    _PACKAGE_APPLICATION_MOVE_NAME = "Relizado sin validar recepción"
    _PACKAGE_APPLICATION_REVERSAL_NAME = "Reversión por validación de recepción"
    
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

    def button_validate(self):
        is_purchase_admin = self.env.user.has_group('purchase.group_purchase_manager')
        is_sales_admin = self.env.user.has_group('sales_team.group_sale_manager')
        
        # Verificar si es una recepción (albarán de entrada) y si el usuario NO es Administrador
        if self.picking_type_id.code == 'incoming' and not is_purchase_admin:
            for move in self.move_ids:
                tolerancia = move.tolerancia_compra or 0.0
                max_allowed = move.product_uom_qty + tolerancia
                tolerancia_date = move.product_id.product_tmpl_id.fecha_minima_tolerancia_compra
                purchase_date_as_date = fields.Date.to_date(move.purchase_line_id.order_id.date_approve)
                
                if tolerancia_date and purchase_date_as_date and purchase_date_as_date < tolerancia_date:
                    continue 
                
                if move.quantity > max_allowed:
                    # Enviar notificación/actividad a Administradores de Compra
                    msg_title = "Validación de Recepción en Exceso"
                    msg_body = (
                        f"El usuario {self.env.user.name} recibió unidades en exceso "
                        f"para el producto <b>{move.product_id.display_name}</b> en el traslado <b>{self.name}</b>.<br/>"
                        f"Demanda: {move.product_uom_qty} | Tolerancia: {tolerancia} | Realizado: {move.quantity}.<br/>"
                        f"Por favor, revise este albarán directamente."
                    )
                    self._notify_administrators('purchase.group_purchase_manager', msg_title, msg_body)

        # Verificar si es una entrega (albarán de salida) y si el usuario NO es Administrador de Ventas
        if self.picking_type_id.code == 'outgoing' and not is_sales_admin:
            for move in self.move_ids:
                tolerancia = move.tolerancia_venta or 0.0
                max_allowed = move.product_uom_qty + tolerancia
                tolerancia_date = move.product_id.product_tmpl_id.fecha_minima_tolerancia_venta
                sale_date_as_date = fields.Date.to_date(move.sale_line_id.order_id.date_order)
                
                if tolerancia_date and sale_date_as_date and sale_date_as_date < tolerancia_date:
                    continue 
                
                if move.quantity > max_allowed:
                    # Enviar notificación/actividad a Administradores de Venta
                    msg_title = "Validación de Entrega en Exceso"
                    msg_body = (
                        f"El usuario {self.env.user.name} entregó unidades en exceso "
                        f"para el producto <b>{move.product_id.display_name}</b> en el traslado <b>{self.name}</b>.<br/>"
                        f"Demanda: {move.product_uom_qty} | Tolerancia: {tolerancia} | Realizado: {move.quantity}.<br/>"
                        f"Por favor, revise este albarán directamente."
                    )
                    self._notify_administrators('sales_team.group_sale_manager', msg_title, msg_body)
                    
        result = super(StockPicking, self).button_validate()
        completed_receipts = self.filtered(
            lambda picking: picking.picking_type_id.code == 'incoming'
            and picking.state == 'done'
        )
        for picking in completed_receipts:
            picking._reverse_package_application_moves()
        return result

    def _reverse_package_application_moves(self):
        self.ensure_one()
        package_moves = self.env['stock.move'].search([
            ('name', '=', self._PACKAGE_APPLICATION_MOVE_NAME),
            ('origin', '=', self.name),
            ('company_id', '=', self.company_id.id),
            ('picking_id', '=', False),
            ('is_inventory', '=', True),
            ('state', '=', 'done'),
        ]).filtered(lambda move: not move.returned_move_ids)

        for package_move in package_moves:
            inventory_location = package_move.location_id
            reversal = self.env['stock.move'].create({
                'name': self._PACKAGE_APPLICATION_REVERSAL_NAME,
                'origin': self.name,
                'origin_returned_move_id': package_move.id,
                'product_id': package_move.product_id.id,
                'product_uom': package_move.product_uom.id,
                'product_uom_qty': package_move.product_uom_qty,
                'company_id': package_move.company_id.id,
                'location_id': package_move.location_dest_id.id,
                'location_dest_id': inventory_location.id,
                'restrict_partner_id': package_move.restrict_partner_id.id,
                'is_inventory': True,
                'picked': True,
                'state': 'confirmed',
            })

            reversal_lines = []
            for line in package_move.move_line_ids:
                reversal_lines.append({
                    'move_id': reversal.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'company_id': package_move.company_id.id,
                    'location_id': line.location_dest_id.id,
                    'location_dest_id': line.location_id.id,
                    'lot_id': line.lot_id.id,
                    'lot_name': line.lot_name,
                    'package_id': line.result_package_id.id,
                    'owner_id': line.owner_id.id,
                    'picked': True,
                    'cantidad_conos': line.cantidad_conos,
                    'cono_id': line.cono_id.id,
                    'package_type_id': line.package_type_id.id,
                    'tara_bolsa': line.tara_bolsa,
                    'tara_cono': line.tara_cono,
                    'peso_bruto': line.peso_bruto,
                    'peso_neto': line.peso_neto,
                })

            self.env['stock.move.line'].with_context(
                skip_package_values_sync=True
            ).create(reversal_lines)
            reversal._action_done()