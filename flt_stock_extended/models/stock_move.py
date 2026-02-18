# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_studio_title = fields.Char(related='product_id.x_studio_title', string="Title", readonly=True)
    descripcion = fields.Text(related='product_id.product_tmpl_id.descripcion', string="Descripción", readonly=True)
    x_studio_color_code = fields.Char(related='product_id.x_studio_color_code', string="Color Code", readonly=True)
    x_studio_color_name = fields.Char(related='product_id.x_studio_color_name', string="Color Name", readonly=True)
    color_family_id = fields.Many2one(related='product_id.color_family_id', string="Familia de Color", readonly=True)

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
                    move.allowed_product_ids = [(6, 0, [])]
            else:
                # Not from a purchase order, allow all products
                move.allowed_product_ids = [(6, 0, [])]

    @api.depends('move_line_ids', 'move_line_ids.cantidad_conos', 'move_line_ids.peso_bruto')
    def _compute_detailed_metrics(self):
        for move in self:
            move.paquetes = len(move.move_line_ids)
            move.conos = sum(move.move_line_ids.mapped('cantidad_conos'))
            move.cantidad_bruto = sum(move.move_line_ids.mapped('peso_bruto'))

    @api.depends('quantity', 'neto_prov', 'product_uom_qty')
    def _compute_diferencias(self):
        for move in self:
            move.diferencia_prov = move.quantity - move.neto_prov
            move.diferencia_demanda = move.quantity - move.product_uom_qty

