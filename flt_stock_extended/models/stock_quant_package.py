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
            # 1. Handle empty packages or packages without a custom 'codificacion'
            if not package.quant_ids or not package.quant_ids[0].product_id.product_tmpl_id.codificacion:
                # Keep original name or fallback if it's empty
                if not package.name:
                    package.name = f"PACK-{str(package.id).zfill(8)}"
                continue
                
            # 2. Extract the prefix from the first product
            prefix = package.quant_ids[0].product_id.product_tmpl_id.codificacion
            
            # 3. Check if this package ALREADY belongs to this prefix series
            # This prevents it from consuming a new sequence number every time a minor quant change occurs
            if package.name and package.name.startswith(f"{prefix}-"):
                continue

            # 4. Generate or find the dedicated ir.sequence for this specific prefix
            seq_code = f"stock.quant.package.custom.{prefix.lower()}"
            sequence_obj = self.env['ir.sequence'].sudo()
            
            existing_seq = sequence_obj.search([('code', '=', seq_code)], limit=1)
            
            if not existing_seq:
                # If a sequence for this prefix doesn't exist yet, build it on the fly starting at 1
                existing_seq = sequence_obj.create({
                    'name': f"Package Sequence for {prefix}",
                    'code': seq_code,
                    'implementation': 'standard',
                    'padding': 8,
                    'number_increment': 1,
                    'number_next': 1,
                    'use_date_range': False
                })
            
            # 5. Fetch the next unique 8-digit correlative for this prefix
            correlative = existing_seq.next_by_id()
            
            # 6. Assign the format: PREFIX-00000001
            package.name = f"{prefix}-{correlative}"
            
    @api.depends('quant_ids', 'quant_ids.cantidad_conos', 'quant_ids.peso_bruto', 'quant_ids.peso_neto')
    def _compute_totals(self):
        for package in self:
            conos = 0
            bruto = 0.0
            neto = 0.0
            for quant in package.quant_ids:
                conos += quant.cantidad_conos
                bruto += quant.peso_bruto
                neto += quant.peso_neto
            package.cantidad_conos = conos
            package.peso_bruto = bruto
            package.peso_neto = neto
