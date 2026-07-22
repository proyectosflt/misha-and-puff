from odoo import models, api, _

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    @api.model
    def search_packages_by_product(self, barcode_or_ref):
        """
        Busca un producto por código de barras o referencia
        y devuelve todos los paquetes internos donde está ubicado.
        """
        if not barcode_or_ref:
            return {'error': _('Ingrese un código de producto válido.')}

        # Buscar producto
        product = self.env['product.product'].search([
            '|', '|',
            ('barcode', '=', barcode_or_ref),
            ('default_code', '=', barcode_or_ref),
            ('name', 'ilike', barcode_or_ref)
        ], limit=1)

        if not product:
            return {'error': _('No se encontró ningún producto con el código: %s') % barcode_or_ref}

        # Buscar quants con paquete en ubicaciones internas
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('quantity', '>', 0),
            ('package_id', '!=', False),
            ('location_id.usage', '=', 'internal')
        ])

        packages_dict = {}
        for quant in quants:
            pkg = quant.package_id
            if pkg.id not in packages_dict:
                packages_dict[pkg.id] = {
                    'id': pkg.id,
                    'name': pkg.name,
                    'barcode': pkg.name,
                    'location_name': quant.location_id.display_name,
                    'quantity': quant.quantity,
                    'scanned': False
                }
            else:
                packages_dict[pkg.id]['quantity'] += quant.quantity

        return {
            'product': {
                'id': product.id,
                'name': product.display_name,
                'barcode': product.barcode or '',
            },
            'packages': list(packages_dict.values())
        }