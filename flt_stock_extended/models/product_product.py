# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_type_id = fields.Many2one('product.type', string='Clasificación de producto')
    tara_cono = fields.Float(string='Tara Cono')
    color_family_id = fields.Many2one('color.family', string='Familia de Color', compute='_compute_color_family_id', store=True)
    weight = fields.Float(default=1.0)

    x_studio_title = fields.Char(string='Title', compute='_compute_studio_fields', store=True)
    x_studio_color_code = fields.Char(string='Color Code', compute='_compute_studio_fields', store=True)
    x_studio_color_name = fields.Char(string='Color Name', compute='_compute_studio_fields', store=True)
    default_code = fields.Char(compute='_compute_studio_fields', store=True)

    @api.depends('product_template_variant_value_ids',
                 'product_template_variant_value_ids.attribute_id.name',
                 'product_template_variant_value_ids.product_attribute_value_id.name',
                 'name',
                 'product_tmpl_id.name')
    def _compute_studio_fields(self):
        for product in self:
            title = False
            color_code = False
            color_name = False
            
            # Access the many2many field safely
            ptavs = product.product_template_variant_value_ids
            for ptav in ptavs:
                attr_name = ptav.attribute_id.name and ptav.attribute_id.name.strip()
                if attr_name == 'Title':
                    title = ptav.product_attribute_value_id.name
                elif attr_name == 'Color':
                    val = ptav.product_attribute_value_id.name
                    if val:
                        parts = val.split('-', 1)
                        color_code = parts[0].strip()
                        if len(parts) > 1:
                            color_name = parts[1].strip()
            
            product.x_studio_title = title
            product.x_studio_color_code = color_code
            product.x_studio_color_name = color_name
            
            # Use product.name which delegates to template name
            # or fallback to product_tmpl_id.name directly
            prod_name = product.name or (product.product_tmpl_id and product.product_tmpl_id.name)
            
            if prod_name and color_code:
                product.default_code = "%s-%s" % (prod_name, color_code)
            else:
                product.default_code = False

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
        products = super(ProductProduct, self).create(vals_list)
        products._compute_studio_fields()
        return products

    @api.onchange('uom_id')
    def _onchange_uom_id_weight(self):
        if self.uom_id.name == 'kg' and self.weight == 0:
            self.weight = 1.0


