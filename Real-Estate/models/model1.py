from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
# from openerp import tools


class TestModel(models.Model):
    _name = "test.model"  # estate.property
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Test Model"
    _order = "id desc"

    name = fields.Char(string="Title", required=True, tracking=True)
    reference = fields.Char(string="Reference", required=True, readonly=True, copy=False, default=lambda self: _('New'))
    description = fields.Text(string='Description')
    postcode = fields.Char(string='Postcode')
    date_availability = fields.Date(string='Available From', copy=False, default=lambda self: fields.Datetime.add(fields.Datetime.now(),months=3))
    expected_price = fields.Float(required=True, string='Expected Price', tracking=True)
    selling_price = fields.Float(string='Selling Price', readonly=True, copy=False, help="Selling price is automatically set when an offer is accepted")
    bedrooms = fields.Integer(default=2, string='Bedrooms')
    living_area = fields.Integer(string='Living Area (sqm)')
    facades = fields.Integer(string='Facades')
    garage = fields.Boolean(string='Garage')
    garden = fields.Boolean(string='Garden')
    garden_area = fields.Integer(string='Garden Area (sqm)')
    garden_orientation = fields.Selection(string='Garden Orientation', selection=[('north', 'North'), ('south', 'South'), ('east', 'East'),('west', 'West')])
    state = fields.Selection(string="Status", selection=[('new', 'New'), ('offer_received', 'Offer Received'), ('offer_accepted', 'Offer Accepted'), ('sold', 'Sold'), ('cancelled', 'Cancelled')], default='new', tracking=True)
    active = fields.Boolean(string="Active", default=True)
    tag_ids = fields.Many2many(comodel_name="estate.property.tag", string="Tags")
    property_type_id = fields.Many2one("estate.property.type", string="Type")
    seller_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=True, default=lambda self: self.env.user)
    buyer_id = fields.Many2one('res.partner', string='Buyer', tracking=True, copy=False)
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    total_area = fields.Float(compute="_compute_total", string="Total Area (sqm)")
    best_price = fields.Float(compute="_compute_price", string="Best Offer")
    image = fields.Binary(string="Property Image")

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)',
         'The expected price of a property should be greater than 0.'),
        ('check_selling_price', 'CHECK(selling_price >= 0)',
         'The selling price of a property should be positive.')
    ]

    def action_sold(self):
        self.state = 'sold'

    def action_cancel(self):
        self.state = 'cancelled'

    @api.model
    def create(self, vals):
        if not vals.get('description'):
            vals['description'] = 'New Property'
        if vals.get('reference', _('New')):
            vals['reference'] = self.env['ir.sequence'].next_by_code('test.model') or _('New')
        # if 'image' in vals:
        #     # resize uploaded image into 250 X 250
        #     resize_image = tools.image_resize_image(vals['image'], size=(250, 250), avoid_if_small=True)
        #     vals['image'] = resize_image
        res = super(TestModel, self).create(vals)
        return res

    # @api.model
    # def write(self, vals):
    #     if 'image' in vals:
    #         # resize uploaded image into 250 X 250
    #         resize_image = tools.image_resize_image(vals['image'], size=(250, 250), avoid_if_small=True)
    #         vals['image'] = resize_image
    #         return super(TestModel, self).write(vals)

    def unlink(self):
        if self.state not in ('new', 'cancelled'):
            raise ValidationError("Action Invalid!! Can't delete property if it is not in New or Cancelled State.")
        for rec in self.offer_ids:
            rec.unlink()
        return super(TestModel, self).unlink()

    @api.depends('living_area', 'garden_area')
    def _compute_total(self):
        self.total_area = self.living_area + self.garden_area

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden is True:
            self.garden_area = 10
            self.garden_orientation = 'north'
        elif self.garden is False:
            self.garden_area = 0
            self.garden_orientation = ''

    @api.depends("offer_ids.partner_id")
    def _compute_price(self):
        for rec in self:
            if rec.offer_ids.partner_id:
                rec.best_price = max(i.price for i in rec.offer_ids)
            else:
                rec.best_price = 0

    def check_offer(self, price):
        # current = self.env['test.model'].browse(self._context.get('active_id')).offer_ids
        if price <= self.best_price:
            raise ValidationError("New offer price must be greater than present offers.")
        elif self.state == 'new':
            self.state = 'offer_received'
        return True

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for rec in self:
            if rec.selling_price != 0:
                value = 0.9 * rec.expected_price
                if rec.selling_price < value:
                    rec.selling_price = 0
                    raise ValidationError("The selling price should not be less than 90% of expected price.")

    def refuse_offer(self, price):
        # current = self.env['estate.property.offer'].browse(self._context.get('active_id')).offer_ids
        for rec in self.id.offer_ids:
            if rec.price == price:
                pass
            rec.action_reject()
        return True

    @api.onchange("offer_ids")
    def _onchange_offer_ids(self):
        if len(self.offer_ids) == 0:
            self.state = 'new'
