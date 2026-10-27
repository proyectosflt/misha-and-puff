from odoo import models, fields, api

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    nombre = fields.Char(string='Nombre')
    color_family_id = fields.Many2one('color.family', string='Familia de Color')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_color_attribute') and 'attribute_id' not in res:
            color_attr = self.env['product.attribute'].search([('name', '=', 'Color')], limit=1)
            if color_attr:
                res['attribute_id'] = color_attr.id
        return res


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    def _get_combination_name(self):
        """
        Overridden to append the custom 'nombre' field to the variant name
        ONLY if the attribute is a color attribute.
        """ 
        # 1. Fetch filtered values following Odoo 18 native rules
        ptavs = self._without_no_variant_attributes().with_prefetch(self._prefetch_ids)
        ptavs = ptavs._filter_single_value_lines().with_prefetch(self._prefetch_ids)
        
        combination_names = []
        
        # 2. Build the display name segments
        for ptav in ptavs:
            pav = ptav.product_attribute_value_id
            
            # Check if this attribute is specifically a Color type
            is_color = ptav.attribute_id.display_type == 'color' or ptav.attribute_id.name == 'Color'
            
            if is_color and pav.nombre:
                # Concatenate only for colors with a filled 'nombre' field (e.g., "53113-SKULL")
                combination_names.append(f"{ptav.name}-{pav.nombre}")
            else:
                # Standard formatting for sizes, materials, or colors without a custom nombre
                combination_names.append(ptav.name)
                
        return ", ".join(combination_names)