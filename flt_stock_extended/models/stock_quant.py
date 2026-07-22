# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    cantidad_conos = fields.Integer(string="Conos")
    tara_cono = fields.Float(string="Tara cono unitaria", digits='Stock Weight')

    def _update_available_quantity(self, product_id, location_id, quantity=0, lot_id=None, package_id=None, owner_id=None, in_date=None, **kwargs):
        """Override to retrieve custom fields from context and update quant accordingly"""
        
        cantidad_conos = self.env.context.get('quant_cantidad_conos', 0)
        tara_cono = self.env.context.get('quant_tara_cono', 0.0)
        
        move_line_location_id = self.env.context.get('move_line_location_id')
        move_line_package_id = self.env.context.get('move_line_package_id')
        
        package_id_val = package_id.id if package_id else False
        is_source = (location_id.id == move_line_location_id and package_id_val == move_line_package_id)
        
        if is_source:
            cantidad_conos = -cantidad_conos
        
        res = super(StockQuant, self)._update_available_quantity(product_id, location_id, quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id, in_date=in_date, **kwargs)
        
        if quantity and ('quant_cantidad_conos' in self.env.context or 'quant_tara_cono' in self.env.context):
            self = self.sudo()
            quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
            if quants:
                quant = quants[0]
                quant.write({
                    'cantidad_conos': quant.cantidad_conos + cantidad_conos,
                    'tara_cono': tara_cono or quant.tara_cono,
                })
        
        return res

    def _get_inventory_fields_create(self):
        inventory_fields_create = super()._get_inventory_fields_create()
        inventory_fields_create += ['cantidad_conos', 'tara_cono']
        return inventory_fields_create
