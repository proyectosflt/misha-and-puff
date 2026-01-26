# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'uom_id' in vals:
                uom = self.env['uom.uom'].browse(vals['uom_id'])
                if uom.name == 'kg' and vals.get('weight', 0) == 0:
                    vals['weight'] = 1.0
        return super(ProductTemplate, self).create(vals_list)

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        # Trigger recomputation on variants when template is updated
        self.product_variant_ids._compute_studio_fields()
        return res

    @api.onchange('uom_id')
    def _onchange_uom_id_weight(self):
        if self.uom_id.name == 'kg' and self.weight == 0:
            self.weight = 1.0

