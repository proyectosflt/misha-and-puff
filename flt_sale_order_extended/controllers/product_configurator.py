from odoo.addons.sale.controllers.product_configurator import SaleProductConfiguratorController


class SaleProductConfiguratorControllerCustom(SaleProductConfiguratorController):

    def _get_product_information(
        self,
        product_template,
        combination,
        currency,
        pricelist,
        so_date,
        quantity=1,
        product_uom_id=None,
        parent_combination=None,
        show_packaging=True,
        **kwargs,
    ):
        values = super()._get_product_information(
            product_template,
            combination,
            currency,
            pricelist,
            so_date,
            quantity=quantity,
            product_uom_id=product_uom_id,
            parent_combination=parent_combination,
            show_packaging=show_packaging,
            **kwargs,
        )

        product_or_template = (
            self.env['product.product'].browse(values['id']) if values.get('id')
            else self.env['product.template'].browse(values['product_tmpl_id'])
        )

        for line in values['attribute_lines']:
            ptal = self.env['product.template.attribute.line'].browse(line['id'])
            # Sort attribute values alphabetically by name
            sorted_ptavs = ptal.product_template_value_ids.sorted('name')
            line['attribute_values'] = [
                dict(
                    **ptav.read(['name', 'html_color', 'image', 'is_custom'])[0],
                    price_extra=self._get_ptav_price_extra(
                        ptav, currency, so_date, product_or_template
                    ),
                ) for ptav in sorted_ptavs
                if ptav.ptav_active or (combination and ptav.id in combination.ids)
            ]

        return values