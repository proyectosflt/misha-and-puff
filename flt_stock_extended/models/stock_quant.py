# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    cantidad_conos = fields.Integer(string="Conos")
    peso_bruto = fields.Float(string="Peso bruto")
    peso_neto = fields.Float(string="Peso neto")

    def _update_available_quantity(self, product_id, location_id, quantity=0, lot_id=None, package_id=None, owner_id=None, in_date=None, **kwargs):
        """Override to retrieve custom fields from context and update quant accordingly"""
        
        # Get custom field values from context
        cantidad_conos = self.env.context.get('quant_cantidad_conos', 0)
        peso_bruto = self.env.context.get('quant_peso_bruto', 0.0)
        peso_neto = self.env.context.get('quant_peso_neto', 0.0)
        
        # If peso_neto is provided, use it as the quantity
        if peso_neto != 0.0:
            quantity = peso_neto
        
        # Call parent to handle standard quantity logic
        res = super(StockQuant, self)._update_available_quantity(product_id, location_id, quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id, in_date=in_date, **kwargs)
        
        # Update our custom fields if any value is set
        if cantidad_conos or peso_bruto or peso_neto:
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
