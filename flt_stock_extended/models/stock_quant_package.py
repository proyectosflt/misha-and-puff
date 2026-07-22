# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    cantidad_conos = fields.Integer(string="Conos", compute='_compute_totals', store=True)
    peso_bruto = fields.Float(string="Peso bruto", compute='_compute_totals', store=True, digits='Stock Weight')
    peso_neto = fields.Float(string="Peso neto", compute='_compute_totals', store=True, digits='Stock Weight')
    
    name = fields.Char(
        string='Package Reference', 
        compute='_compute_dynamic_name', 
        store=True, 
        copy=False
    )

    @api.depends('quant_ids.product_id.product_tmpl_id.codificacion')
    def _compute_dynamic_name(self):
        for package in self:
            if not package.quant_ids or not package.quant_ids[0].product_id.product_tmpl_id.codificacion:
                if not package.name:
                    package.name = f"PACK-{str(package.id).zfill(8)}"
                continue
                
            prefix = package.quant_ids[0].product_id.product_tmpl_id.codificacion
            
            if package.name and package.name.startswith(f"{prefix}-"):
                continue

            seq_code = f"stock.quant.package.custom.{prefix.lower()}"
            sequence_obj = self.env['ir.sequence'].sudo()
            
            existing_seq = sequence_obj.search([('code', '=', seq_code)], limit=1)
            
            if not existing_seq:
                existing_seq = sequence_obj.create({
                    'name': f"Package Sequence for {prefix}",
                    'code': seq_code,
                    'implementation': 'standard',
                    'padding': 8,
                    'number_increment': 1,
                    'number_next': 1,
                    'use_date_range': False
                })
            
            correlative = existing_seq.next_by_id()
            package.name = f"{prefix}-{correlative}"

    @api.depends('quant_ids.quantity', 'quant_ids.cantidad_conos', 'quant_ids.tara_cono', 'package_type_id.base_weight')
    def _compute_totals(self):
        for package in self:
            conos = sum(package.quant_ids.mapped('cantidad_conos'))
            # Net weight is directly the sum of stock quantity in the package
            neto = sum(package.quant_ids.mapped('quantity'))
            
            # Total cone tare for all quants inside
            total_tara_cono = sum(q.cantidad_conos * q.tara_cono for q in package.quant_ids)
            # Bag/Package tare applied once per package
            tara_bolsa = package.package_type_id.base_weight or 0.0
            
            package.cantidad_conos = conos
            package.peso_neto = neto
            package.peso_bruto = neto + total_tara_cono + tara_bolsa
