# -*- coding: utf-8 -*-
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
        
        for user in group.users:
            self.env['mail.activity'].create({
                'res_id': self.id,
                'res_model_id': model_id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': title,
                'note': f'<p>{message}</p>',
                'user_id': user.id,
            })

    def button_validate(self):
        is_purchase_admin = self.env.user.has_group('purchase.group_purchase_manager')
        is_sales_admin = self.env.user.has_group('sales.group_sales_manager')
        
        # Verificar si es una recepción (albarán de entrada) y si el usuario NO es Administrador
        if self.picking_type_id.code == 'incoming' and not is_purchase_admin:
            for move in self.move_ids:
                tolerancia = move.purchase_line_id.tolerancia or 0.0
                max_allowed = move.product_uom_qty + tolerancia
                tolerancia_date = move.product_id.product_tmpl_id.fecha_minima_tolerancia_compra
                purchase_date_as_date = fields.Date.to_date(move.purchase_line_id.order_id.date_approve)
                
                if tolerancia_date and purchase_date_as_date and purchase_date_as_date < tolerancia_date:
                    continue 
                
                if move.quantity > max_allowed:
                    # Enviar notificación/actividad a Administradores de Compra
                    msg_title = "Validación de Recepción en Exceso"
                    msg_body = (
                        f"El usuario {self.env.user.name} está intentando recibir unidades en exceso "
                        f"para el producto <b>{move.product_id.display_name}</b> en el traslado <b>{self.name}</b>.<br/>"
                        f"Demanda: {move.product_uom_qty} | Tolerancia: {tolerancia} | Realizado: {move.quantity}.<br/>"
                        f"Por favor, revise este albarán directamente."
                    )
                    self._notify_administrators('purchase.group_purchase_manager', msg_title, msg_body)
                    
                    raise UserError(_(
                        "Se ha excedido la tolerancia permitida para el producto '%s'.\n"
                        "Se ha enviado una notificación automática a los Administradores de Compras para su revisión directamente en la plataforma."
                    ) % move.product_id.display_name)

        # Verificar si es una entrega (albarán de salida) y si el usuario NO es Administrador de Ventas
        if self.picking_type_id.code == 'outgoing' and not is_sales_admin:
            for move in self.move_ids:
                tolerancia = move.sale_line_id.tolerancia or 0.0
                max_allowed = move.product_uom_qty + tolerancia
                tolerancia_date = move.product_id.product_tmpl_id.fecha_minima_tolerancia_venta
                sale_date_as_date = fields.Date.to_date(move.sale_line_id.order_id.date_order)
                
                if tolerancia_date and sale_date_as_date and sale_date_as_date < tolerancia_date:
                    continue 
                
                if move.quantity > max_allowed:
                    # Enviar notificación/actividad a Administradores de Venta
                    msg_title = "Validación de Entrega en Exceso"
                    msg_body = (
                        f"El usuario {self.env.user.name} está intentando entregar unidades en exceso "
                        f"para el producto <b>{move.product_id.display_name}</b> en el traslado <b>{self.name}</b>.<br/>"
                        f"Demanda: {move.product_uom_qty} | Tolerancia: {tolerancia} | Realizado: {move.quantity}.<br/>"
                        f"Por favor, revise este albarán directamente."
                    )
                    self._notify_administrators('sales.group_sales_manager', msg_title, msg_body)

                    raise UserError(_(
                        "Se ha excedido la tolerancia permitida para el producto '%s'.\n"
                        "Se ha enviado una notificación automática a los Administradores de Ventas para su revisión directamente en la plataforma."
                    ) % move.product_id.display_name)
                    
        return super(StockPicking, self).button_validate()