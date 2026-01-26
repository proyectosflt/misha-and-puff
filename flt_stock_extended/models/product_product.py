# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_type_id = fields.Many2one('product.type', string='Clasificación de producto')
    tara_cono = fields.Float(string='Tara Cono')
    color_family_id = fields.Many2one('color.family', string='Familia de Color', compute='_compute_color_family_id', store=True)
    weight = fields.Float(default=1.0)

    @api.depends('product_template_variant_value_ids.product_attribute_value_id.color_family_id', 'product_template_variant_value_ids.attribute_id.name')
    def _compute_color_family_id(self):
        for product in self:
            color_family = False
            for ptav in product.product_template_variant_value_ids:
                if ptav.attribute_id.name == 'Color':
                    color_family = ptav.product_attribute_value_id.color_family_id
                    break
            product.color_family_id = color_family

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        for product in self:
            if product.uom_id.name == 'kg' and product.weight == 0:
                raise ValidationError("El peso del producto no puede ser 0.")
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'uom_id' in vals:
                uom = self.env['uom.uom'].browse(vals['uom_id'])
                if uom.name == 'kg' and vals.get('weight', 0) == 0:
                    vals['weight'] = 1.0
        return super(ProductProduct, self).create(vals_list)

    @api.onchange('uom_id')
    def _onchange_uom_id_weight(self):
        if self.uom_id.name == 'kg' and self.weight == 0:
            self.weight = 1.0


