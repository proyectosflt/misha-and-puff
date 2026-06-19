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
        # Verificar si es una recepción (albarán de entrada)
        # y si el usuario NO es Administrador de Compras
        if self.picking_type_id.code == 'incoming' and not self.user_has_groups('purchase.group_purchase_manager'):
            for move in self.move_ids:
                # Comparar la cantidad hecha (quantity) con la demanda (product_uom_qty)
                if move.quantity > move.product_uom_qty:
                    raise UserError(_(
                        "No tienes permisos para recibir más unidades de las demandadas para el producto '%s'.\n"
                        "Demanda: %s | Realizado: %s\n"
                        "Solo los Administradores de Compras pueden validar recepciones en exceso."
                    ) % (move.product_id.display_name, move.product_uom_qty, move.quantity))
                    
        return super(StockPicking, self).button_validate()