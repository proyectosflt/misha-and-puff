# -*- coding: utf-8 -*-
from odoo import api, models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    cantidad_conos = fields.Integer(string="Conos")
    tara_bolsa = fields.Float(string="Tara bolsa", compute='_compute_tara_bolsa', store=True, readonly=False)
    tara_cono = fields.Float(string="Tara cono", compute='_compute_tara_cono', store=True, readonly=False)
    peso_bruto = fields.Float(string="Peso bruto")
    peso_neto = fields.Float(string="Peso neto")

    @api.depends('result_package_id.package_type_id.base_weight')
    def _compute_tara_bolsa(self):
        for record in self:
            if not record.tara_bolsa:
                record.tara_bolsa = record.result_package_id.package_type_id.base_weight or 0.0

    @api.depends('product_id.tara_cono')
    def _compute_tara_cono(self):
        for record in self:
            if not record.tara_cono:
                record.tara_cono = record.product_id.tara_cono or 0.0

    def action_calcular(self):
        for record in self:
            value = (record.peso_bruto or 0.0) - (record.tara_bolsa or 0.0) - ((record.tara_cono or 0.0) * (record.cantidad_conos or 0))
            record.peso_neto = value
            record.quantity = value

    @api.model_create_multi
    def create(self, vals_list):
        mls = super(StockMoveLine, self).create(vals_list)
        for ml in mls:
            if ml.state == 'done':
                self.env['stock.quant']._update_available_quantity(
                    ml.product_id, ml.location_id, 0, 
                    lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id,
                    cantidad_conos=-ml.cantidad_conos,
                    peso_bruto=-ml.peso_bruto,
                    peso_neto=-ml.peso_neto
                )
                self.env['stock.quant']._update_available_quantity(
                    ml.product_id, ml.location_dest_id, 0, 
                    lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id,
                    cantidad_conos=ml.cantidad_conos,
                    peso_bruto=ml.peso_bruto,
                    peso_neto=ml.peso_neto
                )
        return mls

    def write(self, vals):
        relevant_fields = ['cantidad_conos', 'peso_bruto', 'peso_neto']
        
        if not any(f in vals for f in relevant_fields) and 'state' not in vals:
            return super(StockMoveLine, self).write(vals)

        old_values_map = {}
        for ml in self:
            if ml.state == 'done':
                old_values_map[ml.id] = {
                    'cantidad_conos': ml.cantidad_conos,
                    'peso_bruto': ml.peso_bruto,
                    'peso_neto': ml.peso_neto,
                }
        
        res = super(StockMoveLine, self).write(vals)
        
        for ml in self:
            if ml.state == 'done':
                if ml.id not in old_values_map:
                    self.env['stock.quant']._update_available_quantity(
                        ml.product_id, ml.location_id, 0, 
                        lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id,
                        cantidad_conos=-ml.cantidad_conos,
                        peso_bruto=-ml.peso_bruto,
                        peso_neto=-ml.peso_neto
                    )
                    self.env['stock.quant']._update_available_quantity(
                        ml.product_id, ml.location_dest_id, 0, 
                        lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id,
                        cantidad_conos=ml.cantidad_conos,
                        peso_bruto=ml.peso_bruto,
                        peso_neto=ml.peso_neto
                    )
                else:
                    old_vals = old_values_map[ml.id]
                    diff_conos = ml.cantidad_conos - old_vals['cantidad_conos']
                    diff_bruto = ml.peso_bruto - old_vals['peso_bruto']
                    diff_neto = ml.peso_neto - old_vals['peso_neto']
                    
                    if diff_conos or diff_bruto or diff_neto:
                        self.env['stock.quant']._update_available_quantity(
                            ml.product_id, ml.location_id, 0, 
                            lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id,
                            cantidad_conos=-diff_conos,
                            peso_bruto=-diff_bruto,
                            peso_neto=-diff_neto
                        )
                        self.env['stock.quant']._update_available_quantity(
                            ml.product_id, ml.location_dest_id, 0, 
                            lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id,
                            cantidad_conos=diff_conos,
                            peso_bruto=diff_bruto,
                            peso_neto=diff_neto
                        )
        return res
