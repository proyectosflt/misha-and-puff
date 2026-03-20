# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_type_id = fields.Many2one('product.type', string='Clasificación de producto')
    weight = fields.Float(default=1.0)

    x_studio_title = fields.Char(string='Title', compute='_compute_studio_fields', store=True)
    x_studio_color_code = fields.Char(string='Color Code', compute='_compute_studio_fields', store=True)
    x_studio_color_name = fields.Char(string='Color Name', compute='_compute_studio_fields', store=True)
    color_family_id = fields.Many2one('color.family', string='Familia de Color', compute='_compute_studio_fields', store=True)
    default_code = fields.Char(compute='_compute_studio_fields', store=True)

    @api.depends('product_template_variant_value_ids',
                 'product_template_variant_value_ids.attribute_id.name',
                 'product_template_variant_value_ids.product_attribute_value_id.name',
                 'product_template_variant_value_ids.product_attribute_value_id.nombre',
                 'product_template_variant_value_ids.product_attribute_value_id.color_family_id',
                 'product_tmpl_id.attribute_line_ids',
                 'product_tmpl_id.attribute_line_ids.value_ids',
                 'product_tmpl_id.attribute_line_ids.value_ids.nombre',
                 'product_tmpl_id.attribute_line_ids.value_ids.color_family_id',
                 'product_tmpl_id.attribute_line_ids.attribute_id.name',
                 'name',
                 'product_tmpl_id.name')
    def _compute_studio_fields(self):
        for product in self:
            title = False
            color_code = False
            color_name = False
            color_family = False
            
            # First, check variant-specific values (for multi-variant attributes)
            ptavs = product.product_template_variant_value_ids
            for ptav in ptavs:
                attr_name = ptav.attribute_id.name and ptav.attribute_id.name.strip()
                if attr_name == 'Title':
                    title = ptav.product_attribute_value_id.name
                elif attr_name == 'Color':
                    val = ptav.product_attribute_value_id
                    color_family = val.color_family_id
                    color_code = val.name
                    color_name = val.nombre
            
            # Second, check template attribute lines for single-value attributes
            # (when there's only one value for an attribute, it's not in variant values)
            if product.product_tmpl_id:
                for attr_line in product.product_tmpl_id.attribute_line_ids:
                    attr_name = attr_line.attribute_id.name and attr_line.attribute_id.name.strip()
                    # Only use template values if we haven't found variant-specific ones
                    if attr_name == 'Title' and not title and len(attr_line.value_ids) == 1:
                        title = attr_line.value_ids[0].name
                    elif attr_name == 'Color' and not color_code and len(attr_line.value_ids) == 1:
                        val = attr_line.value_ids[0]
                        color_family = val.color_family_id
                        color_code = val.name
                        color_name = val.nombre
            
            product.x_studio_title = title
            product.x_studio_color_code = color_code
            product.x_studio_color_name = color_name
            product.color_family_id = color_family
            
            # Use product.name which delegates to template name
            # or fallback to product_tmpl_id.name directly
            prod_name = product.name or (product.product_tmpl_id and product.product_tmpl_id.name)
            
            if prod_name and color_code:
                product.default_code = "%s-%s" % (prod_name, color_code)
            else:
                product.default_code = False

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
        products._compute_studio_fields()
        return products

    @api.onchange('uom_id')
    def _onchange_uom_id_weight(self):
        if self.uom_id.name == 'kg' and self.weight == 0:
            self.weight = 1.0


