# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_type_id = fields.Many2one('product.type', string='Clasificación de producto')
    tara_cono = fields.Float(string='Tara Cono')
    color_family_id = fields.Many2one('color.family', string='Familia de Color', compute='_compute_color_family_id', store=True)

    @api.depends('product_template_variant_value_ids.product_attribute_value_id.color_family_id', 'product_template_variant_value_ids.attribute_id.name')
    def _compute_color_family_id(self):
        for product in self:
            color_family = False
            for ptav in product.product_template_variant_value_ids:
                if ptav.attribute_id.name == 'Color':
                    color_family = ptav.product_attribute_value_id.color_family_id
                    break
            product.color_family_id = color_family

