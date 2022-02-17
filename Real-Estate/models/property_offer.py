from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PropertyOffer(models.Model):
    _name = "estate.property.offer"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Property Offer"
    _order = "price desc"

    price = fields.Float(string="Price", tracking=True)
    status = fields.Selection(string="Status", selection=[('accepted', 'Accepted'), ('refused', 'Refused')], copy=False)
    partner_id = fields.Many2one('res.partner', required=True)
    property_id = fields.Many2one('test.model', required=True)
    property_type_id = fields.Many2one(related="property_id.property_type_id", store=True)
    create_date = fields.Datetime(default=fields.Datetime.now())
    validity = fields.Integer(string="Validity (days)", default="7")
    date_deadline = fields.Date(string="Deadline", compute="_compute_date", inverse="_inverse_date")

    _sql_constraints = [
        ('check_price', 'CHECK(price > 0)',
         'An offer price of a property should be greater than 0.'),
    ]

    @api.model
    def create(self, vals):
        if vals.get('price'):
            self.env['test.model'].browse(vals['property_id']).check_offer(vals.get('price'))
        return super(PropertyOffer, self).create(vals)

    @api.depends("validity")
    def _compute_date(self):
        for rec in self:
            rec.date_deadline = fields.Datetime.add(rec.create_date.date(), days=rec.validity)

    def _inverse_date(self):
        for rec in self:
            rec.validity = (rec.date_deadline - rec.create_date.date()).days

    def action_accept(self):
        refuse = self.env['test.model'].browse(self.property_id)
        refuse.refuse_offer(self.price)
        self.property_id.selling_price = self.price
        if self.property_id.selling_price != 0:
            self.status = 'accepted'
            self.property_id.buyer_id = self.partner_id
            self.property_id.state = 'offer_accepted'

    def action_reject(self):
        self.status = 'refused'
