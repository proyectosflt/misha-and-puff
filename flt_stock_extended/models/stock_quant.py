# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    cantidad_conos = fields.Integer(string="Conos")
    peso_bruto = fields.Float(string="Peso bruto")
    peso_neto = fields.Float(string="Peso neto")

    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None, cantidad_conos=None, peso_bruto=None, peso_neto=None, **kwargs):
        """ Override to also track cantidad_conos, peso_bruto, and peso_neto """
        
        # Handle default values
        if cantidad_conos is None:
            cantidad_conos = 0
        if peso_bruto is None:
            peso_bruto = 0.0
        if peso_neto is None:
            peso_neto = 0.0
        
        # Call parent to handle standard quantity logic
        res = super(StockQuant, self)._update_available_quantity(product_id, location_id, quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id, in_date=in_date, **kwargs)
        
        # Now update our custom fields
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
        if quants:
            quant = quants[0]
            quant.write({
                'cantidad_conos': quant.cantidad_conos + cantidad_conos,
                'peso_bruto': quant.peso_bruto + peso_bruto,
                'peso_neto': quant.peso_neto + peso_neto,
            })
        
        return res

    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`. """
        inventory_fields_create = super()._get_inventory_fields_create()
        inventory_fields_create += ['cantidad_conos', 'peso_bruto', 'peso_neto']
        return inventory_fields_create
