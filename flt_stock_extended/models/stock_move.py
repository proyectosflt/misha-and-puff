# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.tools.translate import _

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_studio_title = fields.Char(related='product_id.x_studio_title', string="Title", readonly=True)
    descripcion = fields.Text(related='product_id.product_tmpl_id.descripcion', string="Descripción", readonly=True)
    x_studio_color_code = fields.Char(related='product_id.x_studio_color_code', string="Color Code", readonly=True)
    x_studio_color_name = fields.Char(related='product_id.x_studio_color_name', string="Color Name", readonly=True)
    color_family_id = fields.Many2one(related='product_id.color_family_id', string="Familia de Color", readonly=True)
    item_number = fields.Integer(string="Item", compute='_compute_item_number')

    allowed_product_ids = fields.Many2many(
        'product.product',
        compute='_compute_allowed_product_ids',
        string='Productos Permitidos'
    )

    neto_prov = fields.Float(string="Neto prov")
    diferencia_prov = fields.Float(string="Dif prov", compute="_compute_diferencias", store=True)
    diferencia_demanda = fields.Float(string="Dif dem", compute="_compute_diferencias", store=True)

    paquetes = fields.Integer(string="Paquetes", compute="_compute_detailed_metrics", store=True)
    conos = fields.Integer(string="Conos", compute="_compute_detailed_metrics", store=True)
    cantidad_bruto = fields.Float(string="Cantidad bruto", compute="_compute_detailed_metrics", store=True)
    
    tolerancia_compra = fields.Float(related='purchase_line_id.tolerancia', string="Tolerancia", digits='Stock Weight', default=0.0)
    tolerancia_venta = fields.Float(related='sale_line_id.tolerancia', string="Tolerancia", digits='Stock Weight', default=0.0)

    validation_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('validated', 'Validado'),
    ], string="Validación", default='pending', copy=False, index=True, readonly=True)

    @api.depends('picking_id', 'picking_id.move_ids_without_package')
    def _compute_item_number(self):
        for move in self:
            if move.picking_id and move.picking_id.move_ids_without_package:
                moves = move.picking_id.move_ids_without_package
                if move in moves:
                    move.item_number = list(moves).index(move) + 1
                else:
                    move.item_number = 0
            else:
                move.item_number = 0

    @api.depends('picking_id', 'picking_id.origin', 'origin')
    def _compute_allowed_product_ids(self):
        """Compute allowed products based on purchase order origin"""
        for move in self:
            # Check if this move is from a purchase order
            origin = move.picking_id and move.picking_id.origin
            
            if origin and origin.startswith('P'):
                # Search for the purchase order
                purchase_order = self.env['purchase.order'].search([('name', '=', origin)], limit=1)
                
                if purchase_order:
                    # Get all product IDs from the purchase order lines
                    product_ids = purchase_order.order_line.mapped('product_id').ids
                    move.allowed_product_ids = [(6, 0, product_ids)]
                else:
                    # If PO not found, allow all products
                    move.allowed_product_ids = [(6, 0, self.env['product.product'].search([]).ids)]
            else:
                # Not from a purchase order, allow all products
                move.allowed_product_ids = [(6, 0, self.env['product.product'].search([]).ids)]

    @api.depends('move_line_ids', 'move_line_ids.cantidad_conos', 'move_line_ids.peso_bruto',
                 'move_line_ids.validation_state')
    def _compute_detailed_metrics(self):
        for move in self:
            lines = move.move_line_ids.filtered(lambda l: l.validation_state != 'cancel')
            move.paquetes = len(lines)
            move.conos = sum(lines.mapped('cantidad_conos'))
            move.cantidad_bruto = sum(lines.mapped('peso_bruto'))

    @api.depends('quantity', 'neto_prov', 'product_uom_qty')
    def _compute_diferencias(self):
        for move in self:
            move.diferencia_prov = move.quantity - move.neto_prov
            move.diferencia_demanda = move.quantity - move.product_uom_qty

    # -------------------------------------------------------------------------
    # Tolerancias
    # -------------------------------------------------------------------------
    def _get_tolerancia_info(self):
        """Datos del control de tolerancia del movimiento.

        Devuelve (tolerancia, group_xml_id, etiquetas) o False cuando no
        corresponde controlar: el usuario es administrador, el tipo de operación
        no es recepción/entrega, o el pedido es anterior a la fecha mínima de
        tolerancia configurada en el producto.
        """
        self.ensure_one()
        code = self.picking_id.picking_type_id.code or self.picking_type_id.code

        if code == 'incoming':
            if self.env.user.has_group('purchase.group_purchase_manager'):
                return False
            tolerancia_date = self.product_id.product_tmpl_id.fecha_minima_tolerancia_compra
            order_date = fields.Date.to_date(self.purchase_line_id.order_id.date_approve)
            if tolerancia_date and order_date and order_date < tolerancia_date:
                return False
            return (self.tolerancia_compra or 0.0, 'purchase.group_purchase_manager',
                    ('Recepción', 'recibir', 'Compras'))

        if code == 'outgoing':
            if self.env.user.has_group('sales.group_sales_manager'):
                return False
            tolerancia_date = self.product_id.product_tmpl_id.fecha_minima_tolerancia_venta
            order_date = fields.Date.to_date(self.sale_line_id.order_id.date_order)
            if tolerancia_date and order_date and order_date < tolerancia_date:
                return False
            return (self.tolerancia_venta or 0.0, 'sales.group_sales_manager',
                    ('Entrega', 'entregar', 'Ventas'))

        return False

    def _check_tolerancia(self, qty=None):
        """Verifica que `qty` (por defecto la cantidad del movimiento) no supere
        la demanda más la tolerancia. Notifica a los administradores y lanza un
        error cuando se excede."""
        for move in self:
            info = move._get_tolerancia_info()
            if not info:
                continue
            tolerancia, group_xml_id, labels = info
            qty_to_check = move.quantity if qty is None else qty
            max_allowed = move.product_uom_qty + tolerancia
            rounding = move.product_uom.rounding or 0.01
            if float_compare(qty_to_check, max_allowed, precision_rounding=rounding) <= 0:
                continue

            operacion, verbo, area = labels
            move._notify_tolerancia_exceeded(group_xml_id, operacion, verbo, tolerancia, qty_to_check)
            raise UserError(_(
                "Se ha excedido la tolerancia permitida para el producto '%(producto)s'.\n"
                "Demanda: %(demanda)s | Tolerancia: %(tolerancia)s | Máximo permitido: %(maximo)s | "
                "Se intenta procesar: %(cantidad)s.\n"
                "Se ha enviado una notificación automática a los Administradores de %(area)s "
                "para su revisión directamente en la plataforma."
            ) % {
                'producto': move.product_id.display_name,
                'demanda': move.product_uom_qty,
                'tolerancia': tolerancia,
                'maximo': max_allowed,
                'cantidad': qty_to_check,
                'area': area,
            })

    def _notify_tolerancia_exceeded(self, group_xml_id, operacion, verbo, tolerancia, qty):
        self.ensure_one()
        picking = self.picking_id
        if not picking:
            return
        msg_title = "Validación de %s en Exceso" % operacion
        msg_body = (
            f"El usuario {self.env.user.name} está intentando {verbo} unidades en exceso "
            f"para el producto <b>{self.product_id.display_name}</b> en el traslado <b>{picking.name}</b>.<br/>"
            f"Demanda: {self.product_uom_qty} | Tolerancia: {tolerancia} | Realizado: {qty}.<br/>"
            f"Por favor, revise este albarán directamente."
        )
        picking._notify_administrators(group_xml_id, msg_title, msg_body)

    # -------------------------------------------------------------------------
    # Validación por línea
    # -------------------------------------------------------------------------
    def _update_validation_state(self):
        """Marca como validados los movimientos cuyas líneas (sin contar las
        canceladas) están todas validadas y devuelve los albaranes que quedaron
        completamente validados."""
        pickings = self.env['stock.picking']
        for move in self:
            if move.state in ('done', 'cancel'):
                continue
            lines = move.move_line_ids
            pendientes = lines.filtered(lambda l: l.validation_state == 'pending')
            completo = bool(lines) and not pendientes
            if completo and move.validation_state != 'validated':
                move.validation_state = 'validated'
                if 'picked' in move._fields:
                    move.picked = True
            elif not completo and move.validation_state == 'validated':
                move.validation_state = 'pending'
            pickings |= move.picking_id
        return pickings.filtered(lambda p: p._is_fully_validated())
