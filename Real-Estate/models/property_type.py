from odoo import api, fields, models


class PropertyType(models.Model):
    _name = "estate.property.type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Property Type"
    _order = "sequence,name"

    name = fields.Char(string="Property Type", required=True, tracking=True)
    property_ids = fields.One2many("test.model", "property_type_id")
    sequence = fields.Integer('Sequence', default=1)
    offer_ids = fields.One2many("estate.property.offer", "property_type_id")
    offer_count = fields.Integer(compute="_compute_offers", default=0)

    _sql_constraints = [
        ('check_name', 'UNIQUE(name)',
         'Property type name must be unique.')
    ]

    @api.depends("offer_ids")
    def _compute_offers(self):
        self.offer_count = len(self.offer_ids)
