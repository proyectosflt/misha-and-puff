from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    tolerancia = fields.Float(
        string='Tolerancia',
        compute='_compute_tolerancia',
        store=True,
        readonly=False,
        copy=False,
        help='Tolerancia de compra tomada del producto'
    )

    @api.depends('product_id')
    def _compute_tolerancia(self):
        for line in self:
            if line.product_id:
                line.tolerancia = line.product_id.tolerancia_compra
            else:
                line.tolerancia = 0.0
                
    materia_prima_id = fields.Many2one(
        'product.product',
        string='Materia Prima',
        domain=[('type', '=', 'consu')],
        help="Raw material required for subcontracting this product."
    )

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        # 1. Prepare references for Routes and BoMs
        Route = self.env['stock.route']
        Bom = self.env['mrp.bom']
        
        # Look for the standard "Resupply Subcontractor on Order" route
        resupply_route = self.env.ref('mrp_subcontracting.route_resupply_subcontractor_mto', raise_if_not_found=False)
        if not resupply_route:
            # Fallback search if the XML ID was modified in the database
            resupply_route = Route.search([('name', 'ilike', 'Resupply Subcontractor on Order')], limit=1)

        for order in self:
            for line in order.order_line:
                if line.materia_prima_id:
                    product = line.product_id
                    materia_prima = line.materia_prima_id
                    vendor = order.partner_id

                    # 2. Ensure the "Resupply Subcontractor on Order" route is selected on the finished product
                    if resupply_route and resupply_route.id not in product.route_ids.ids:
                        product.write({'route_ids': [(4, resupply_route.id)]})

                    # 3. Search for an existing Subcontracting BoM with this exact materia prima component
                    boms = Bom.search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('type', '=', 'subcontract'),
                        ('bom_line_ids.product_id', '=', materia_prima.id)
                    ])

                    if boms:
                        # BoM found: Ensure vendor is listed as a subcontractor
                        target_bom = boms[0]
                        if vendor.id not in target_bom.subcontractor_ids.ids:
                            target_bom.write({'subcontractor_ids': [(4, vendor.id)]})
                    else:
                        # 4. No BoM found: Create a new one
                        target_bom = Bom.create({
                            'product_tmpl_id': product.product_tmpl_id.id,
                            'product_id': product.id if product.product_variant_count > 1 else False,
                            'product_uom_id': product.uom_id.id, # Explicitly set finished product UoM
                            'type': 'subcontract',
                            'subcontractor_ids': [(4, vendor.id)],
                            'bom_line_ids': [(0, 0, {
                                'product_id': materia_prima.id,
                                'product_qty': 1.1,
                                'product_uom_id': materia_prima.uom_id.id, # CRITICAL FIX: Explicitly set component UoM
                            })]
                        })

                    # 5. Force the new or found BoM to have the first sequence (highest priority)
                    target_bom.write({'sequence': 1})
                    
                    # Shift sequences of any competing BoMs to ensure our target is strictly first
                    competing_boms = Bom.search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('id', '!=', target_bom.id),
                        ('sequence', '<=', 1)
                    ])
                    for ob in competing_boms:
                        ob.write({'sequence': ob.sequence + 1})

        # 6. Proceed with standard Odoo confirmation (this will trigger the delivery transfers)
        return super(PurchaseOrder, self).button_confirm()