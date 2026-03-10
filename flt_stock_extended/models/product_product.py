# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    weight = fields.Float(default=1.0)

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if 'uom_id' in vals or 'weight' in vals:
            for product in self:
                if product.uom_id.name == 'kg' and product.weight != 1:
                    raise ValidationError("El peso del producto no puede ser diferente de 1 si la unidad de medida es kilogramos.")
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'uom_id' in vals:
                uom = self.env['uom.uom'].browse(vals['uom_id'])
                if uom.name == 'kg' and vals.get('weight', 0) == 0:
                    vals['weight'] = 1.0
        products = super(ProductProduct, self).create(vals_list)
        return products

    @api.onchange('uom_id')
    def _onchange_uom_id_weight(self):
        if self.uom_id.name == 'kg' and self.weight == 0:
            self.weight = 1.0


