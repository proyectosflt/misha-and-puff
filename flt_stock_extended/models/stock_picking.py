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

        # Verificar si es una recepción (albarán de entrada) y si el usuario NO es Administrador
        if self.picking_type_id.code == 'incoming' and not is_purchase_admin:
            for move in self.move_ids:
                # Comparar la cantidad hecha (quantity) con la demanda (product_uom_qty)
                if move.quantity > move.product_uom_qty:
                    raise UserError(_(
                        "No tienes permisos para recibir más unidades de las demandadas para el producto '%s'.\n"
                        "Demanda: %s | Realizado: %s\n"
                        "Solo los Administradores de Compras pueden validar recepciones en exceso."
                    ) % (move.product_id.display_name, move.product_uom_qty, move.quantity))
                    
        return super(StockPicking, self).button_validate()