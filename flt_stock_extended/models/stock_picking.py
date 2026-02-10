# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    total_paquetes = fields.Integer(compute='_compute_totals', string="Total Paquetes")
    total_conos = fields.Integer(compute='_compute_totals', string="Total Conos")
    total_cantidad_bruto = fields.Float(compute='_compute_totals', string="Total Cantidad Bruto")
    total_quantity = fields.Float(compute='_compute_totals', string="Total Cantidad Neto")
    total_neto_prov = fields.Float(compute='_compute_totals', string="Total Neto Prov")
    total_diferencia_prov = fields.Float(compute='_compute_totals', string="Total Diferencia Prov")
    total_diferencia_demanda = fields.Float(compute='_compute_totals', string="Total Diferencia Demanda")

    @api.depends('move_ids_without_package.paquetes', 
                 'move_ids_without_package.conos', 
                 'move_ids_without_package.cantidad_bruto', 
                 'move_ids_without_package.quantity', 
                 'move_ids_without_package.neto_prov', 
                 'move_ids_without_package.diferencia_prov', 
                 'move_ids_without_package.diferencia_demanda')
    def _compute_totals(self):
        for picking in self:
            moves = picking.move_ids_without_package
            picking.total_paquetes = sum(moves.mapped('paquetes'))
            picking.total_conos = sum(moves.mapped('conos'))
            picking.total_cantidad_bruto = sum(moves.mapped('cantidad_bruto'))
            picking.total_quantity = sum(moves.mapped('quantity'))
            picking.total_neto_prov = sum(moves.mapped('neto_prov'))
            picking.total_diferencia_prov = sum(moves.mapped('diferencia_prov'))
            picking.total_diferencia_demanda = sum(moves.mapped('diferencia_demanda'))
