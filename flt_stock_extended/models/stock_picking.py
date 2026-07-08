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

    def button_validate(self):
        # CORRECCIÓN: Usamos self.env.user.has_group() para verificar el grupo correctamente
        is_purchase_admin = self.env.user.has_group('purchase.group_purchase_manager')
        is_sales_admin = self.env.user.has_group('sales.group_sales_manager')
        

        # Verificar si es una recepción (albarán de entrada) y si el usuario NO es Administrador
        if self.picking_type_id.code == 'incoming' and not is_purchase_admin:
            for move in self.move_ids:
                # Comparar la cantidad hecha (quantity) con la demanda (product_uom_qty)
                # Considerar la tolerancia de compra del producto
                tolerancia = move.purchase_line_id.tolerancia or 0.0
                max_allowed = move.product_uom_qty + tolerancia
                tolerancia_date = move.product_id.product_tmpl_id.fecha_minima_tolerancia_compra
                purchase_date_as_date = fields.Date.to_date(move.purchase_line_id.order_id.date_approve)
                
                if tolerancia_date and purchase_date_as_date and purchase_date_as_date < tolerancia_date:
                    continue  # Ignorar la validación de tolerancia si la fecha de compra es anterior a la fecha mínima de tolerancia
                
                if move.quantity > max_allowed:
                    raise UserError(_(
                        "No tienes permisos para recibir más unidades de las demandadas para el producto '%s'.\n"
                        "Demanda: %s | Tolerancia: %s | Máximo permitido: %s | Realizado: %s\n"
                        "Solo los Administradores de Compras pueden validar recepciones en exceso."
                    ) % (move.product_id.display_name, move.product_uom_qty, tolerancia, max_allowed, move.quantity))

        # Verificar si es una entrega (albarán de salida) y si el usuario NO es Administrador de Ventas
        if self.picking_type_id.code == 'outgoing' and not is_sales_admin:
            for move in self.move_ids:
                # Comparar la cantidad hecha (quantity) con la demanda (product_uom_qty)
                # Considerar la tolerancia de venta del producto
                tolerancia = move.sale_line_id.tolerancia or 0.0
                max_allowed = move.product_uom_qty + tolerancia
                tolerancia_date = move.product_id.product_tmpl_id.fecha_minima_tolerancia_venta
                sale_date_as_date = fields.Date.to_date(move.sale_line_id.order_id.date_order)
                
                if tolerancia_date and sale_date_as_date and sale_date_as_date < tolerancia_date:
                    continue  # Ignorar la validación de tolerancia si la fecha de venta es anterior a la fecha mínima de tolerancia
                
                if move.quantity > max_allowed:
                    raise UserError(_(
                        "No tienes permisos para entregar más unidades de las demandadas para el producto '%s'.\n"
                        "Demanda: %s | Tolerancia: %s | Máximo permitido: %s | Realizado: %s\n"
                        "Solo los Administradores de Ventas pueden validar entregas en exceso."
                    ) % (move.product_id.display_name, move.product_uom_qty, tolerancia, max_allowed, move.quantity))
                    
        return super(StockPicking, self).button_validate()