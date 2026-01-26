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

    @api.onchange('uom_id')
    def _onchange_uom_id_weight(self):
        if self.uom_id.name == 'kg' and self.weight == 0:
            self.weight = 1.0

