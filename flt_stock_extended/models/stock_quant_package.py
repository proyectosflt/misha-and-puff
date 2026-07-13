# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    cantidad_conos = fields.Integer(string="Conos", compute='_compute_totals', store=True)
    peso_bruto = fields.Float(string="Peso bruto", compute='_compute_totals', store=True, digits='Stock Weight')
    peso_neto = fields.Float(string="Peso neto", compute='_compute_totals', store=True, digits='Stock Weight')
    
    package_correlative = fields.Char(
        string='Package Correlative', 
        copy=False, 
        readonly=True, 
        default=lambda self: self.env['ir.sequence'].next_by_code('stock.quant.package.custom.seq')
    )

    # 2. Override the standard name field to make it computed
    name = fields.Char(
        string='Package Reference', 
        compute='_compute_dynamic_name', 
        store=True, 
        copy=False
    )

    # 3. Recompute whenever the stock quants inside the package change
    @api.depends('quant_ids.product_id.product_tmpl_id.codificacion', 'package_correlative')
    def _compute_dynamic_name(self):
        for package in self:
            # Fallback if the sequence hasn't generated yet (e.g., UI new record state)
            correlative = package.package_correlative or '00000000'
            
            # Default prefix for empty packages
            prefix = 'PACK' 
            
            # If the package contains stock, grab the first product's codificacion
            if package.quant_ids:
                first_product = package.quant_ids[0].product_id
                
                # Retrieve your custom field from the product template
                codificacion = first_product.product_tmpl_id.codificacion
                
                if codificacion:
                    prefix = codificacion
                    
            # Combine them (You can remove the hyphen if you want them directly attached)
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
