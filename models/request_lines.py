from odoo import models, fields, api


class RequestLines(models.Model):
    _name = 'request.lines'
    _order = 'request_id'
    _description = 'material request lines'

    request_id = fields.Many2one('material.request', "Request Reference",
                                 required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product', string='Material/Product')
    get_by = fields.Selection([('purchase_order', 'Purchase Order'), ('internal_transfer', 'Internal Transfer')],
                              "Get by", required=True)
    quantity = fields.Float("Quantity", default=1)
    source_loc = fields.Many2one('stock.location', "Source Location", store=True,)
    dest_loc = fields.Many2one('stock.location', "Destination Location",store=True,)
