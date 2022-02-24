from odoo import models, fields
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        if self.state not in ('draft', 'sent'):
            raise ValidationError("You can only generate deliveries for orders in state Quotation or Quotation Sent.")
        else:
            return super().action_confirm()
