from odoo import models, fields


class TestModel(models.Model):
    _inherit = "test.model"

    invoice_id = fields.Many2one('account.move', string="Invoice ID", copy=False)

    def action_sold(self):

        price = 0.06*self.selling_price

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal().id,
            'partner_id': self.buyer_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'quantity': 1,
                'price_unit': price,
            }), (0, 0, {
                'name': 'Administrative fees',
                'quantity': 1,
                'price_unit': 100,
            })],
        })
        self.invoice_id = invoice.id
        return super().action_sold()

    def action_view_invoice(self):
        action = {
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.invoice_id.id
        }
        return action
