from odoo import api, fields, models


class Users(models.Model):
    _inherit = "res.users"

    estate_property_ids = fields.One2many("test.model", "seller_id", domain=([('state', '=', 'new')]))
