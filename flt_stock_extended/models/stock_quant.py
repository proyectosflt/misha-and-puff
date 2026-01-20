# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    cantidad_conos = fields.Integer(string="Conos")
    peso_bruto = fields.Float(string="Peso bruto")
    peso_neto = fields.Float(string="Peso neto")

    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None, cantidad_conos=0, peso_bruto=0.0, peso_neto=0.0, **kwargs):
        res = super(StockQuant, self)._update_available_quantity(product_id, location_id, quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id, in_date=in_date, **kwargs)
        
        if cantidad_conos or peso_bruto or peso_neto:
            self = self.sudo()
            quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
            if lot_id and quantity > 0:
                quants = quants.filtered(lambda q: q.lot_id)
            
            if quants:
                # Use the logic from _update_available_quantity to pick one, or just pick the first one as they should be aggregated.
                quant = quants[0]
                quant.write({
                    'cantidad_conos': quant.cantidad_conos + cantidad_conos,
                    'peso_bruto': quant.peso_bruto + peso_bruto,
                    'peso_neto': quant.peso_neto + peso_neto,
                })
        
        return res
