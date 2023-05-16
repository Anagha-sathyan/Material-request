from odoo import models, fields, api, Command


class MaterialRequest(models.Model):
    _name = 'material.request'
    _inherit = 'mail.thread'
    _description = 'request for materials'

    name = fields.Char(string='Request No', copy=False, default='New')
    request_date = fields.Date('Request Date', default=fields.Datetime.today())
    partner_id = fields.Many2one('res.users', "Ordered By", default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting for Approval'),
                              ('to_approve', 'To Approve'), ('confirm', 'Confirm'), ('cancelled', 'Cancelled')],
                             string='Status', default="draft", copy=False, tracking=1, )
    request_line_ids = fields.One2many('request.lines', 'request_id',
                                       string="Lines", copy=True, auto_join=True)
    po_count = fields.Integer(string='Purchase Order Count', compute='compute_po_count')
    transfer_count = fields.Integer(string='Transfer Count', compute='compute_transfer_count')

    @api.model
    def create(self, vals):
        """to generate sequence in material request"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'material.request') or 'New'
        return super(MaterialRequest, self).create(vals)

    def action_send_to_manager(self):
        """send request to manager for approval"""
        self.write({'state': 'waiting_for_approval'})

    def action_approval_manager(self):
        """send request to head by manager for approval"""
        self.write({'state': 'to_approve'})

    def action_approval(self):
        """Approve material request and creating purchase order and internal transfer for the product"""
        for record in self.request_line_ids:
            if record.get_by == 'purchase_order':
                # if select purchase order, create RFQ for multiple vendors
                for seller in record.product_id.seller_ids:
                    order_lines_vals = {'product_id': record.product_id.id,
                                        'name': record.product_id.name,
                                        'product_uom': record.product_id.uom_po_id.id,
                                        'product_uom_qty': record.quantity,
                                        'price_unit': seller.price, }
                    order = self.env['purchase.order'].sudo().create({
                        'partner_id': seller.partner_id.id,
                        'origin': self.name,
                        'order_line': [Command.create(order_lines_vals)],
                    })
                    order.button_confirm()
            else:
                # if product get by internal transfer,stock transfer from source to destination location
                stock_vals = {
                    'product_id': record.product_id.id,
                    'name': record.product_id.name,
                    'product_uom_qty': record.quantity,
                    'product_uom': record.product_id.uom_id.id,
                    'reserved_availability': record.quantity,
                    'location_id': record.source_loc.id,
                    'location_dest_id': record.dest_loc.id,
                }
                picking = self.env['stock.picking'].sudo().create({
                    'partner_id': self.env.user.id,
                    'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                    'location_id': record.source_loc.id,
                    'location_dest_id': record.dest_loc.id,
                    'origin': self.name,
                    'move_ids': [Command.create(stock_vals)]})
                picking.action_confirm()
            self.write({'state': 'confirm'})

    def action_view_purchase_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'PO',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('origin', '=', self.name)],
            'context': "{'create': False}",
        }

    def action_view_transfer(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('origin', '=', self.name)],
            'context': "{'create': False}",
        }

    def action_reject(self):
        # to reject the request
        self.write({'state': 'cancelled'})

    @api.depends('po_count', )
    def compute_po_count(self):
        """compute count of purchase order"""
        self.po_count = self.env['purchase.order'].search_count(
            [('origin', '=', self.name)])

    @api.depends('transfer_count', )
    def compute_transfer_count(self):
        """compute count of internal transfers"""
        self.transfer_count = self.env['stock.picking'].search_count(
            [('origin', '=', self.name)])
