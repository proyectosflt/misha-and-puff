# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for template in self:
            if template.uom_id.name == 'kg' and template.weight == 0:
                raise ValidationError("El peso del producto no puede ser 0.")
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'uom_id' in vals:
                uom = self.env['uom.uom'].browse(vals['uom_id'])
                if uom.name == 'kg' and vals.get('weight', 0) == 0:
                    vals['weight'] = 1.0
        return super(ProductTemplate, self).create(vals_list)

    @api.onchange('uom_id')

    def _onchange_uom_id_weight(self):
        if self.uom_id.name == 'kg' and self.weight == 0:
            self.weight = 1.0

