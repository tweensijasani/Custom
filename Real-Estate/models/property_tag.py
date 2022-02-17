from odoo import fields, models


class PropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Property Tag"
    _order = "name"

    name = fields.Char(string="Name", required=True, tracking=True)
    color = fields.Integer()

    _sql_constraints = [
        ('check_name', 'UNIQUE(name)',
         'Property tag name must be unique.')
    ]
