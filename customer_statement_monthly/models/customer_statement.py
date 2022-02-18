# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

import calendar
from datetime import datetime, date


class CustomerStatement(models.Model):
    _name = 'customer.statement'
    _description = 'monthly customer statement'
    _order = 'from_date desc,name'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'), compute='_compute_name', store=True)
    month_list = [
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ]
    month = fields.Selection(month_list, string='Month', required=True,
                             default=month_list[int(datetime.now().strftime('%m')) - 1][0])
    year = fields.Integer(required=True, default=datetime.now().strftime('%Y'))
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    opening_balance = fields.Float(compute='_compute_opening_balance', string='Opening Balance')
    total_debit = fields.Float(compute='_compute_total_debit', string='Total Debit')
    total_credit = fields.Float(compute='_compute_total_credit', string='Total Credit')
    closing_balance = fields.Float(compute='_compute_closing_balance', string='Closing Balance')
    statement_lines = fields.One2many('customer.statement.line', 'statement_id', string='Statements')

    @api.depends('month', 'year')
    def _compute_name(self):
        count = 1
        name = ''
        for rec in self:
            if rec.month in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                name = 'MCS/' + str(rec.year) + '/0' + str(rec.month) + '/' + format(count, '04d')
            else:
                name = 'MCS/' + str(rec.year) + '/' + str(rec.month) + '/' + format(count, '04d')
            name = self.check_name(name, count)
            rec.name = name
            return rec

    def check_name(self, name, count):
        for rec in self:
            statements = self.env['customer.statement'].search([('name', '=', name)])
            if statements:
                for statement in statements:
                    count += 1
                if rec.month in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    name = 'MCS/' + str(rec.year) + '/0' + str(rec.month) + '/' + format(count, '04d')
                else:
                    name = 'MCS/' + str(rec.year) + '/' + str(rec.month) + '/' + format(count, '04d')
                name = self.check_name(name, count)
                return name
            else:
                return name

    @api.onchange('month', 'year')
    def onchange_month(self):
        if self.month:
            month_date = date(self.year, int(self.month), 1)
            self.from_date = month_date.replace(day=1)
            self.to_date = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])

    @api.depends('month', 'year')
    def _compute_opening_balance(self):
        for rec in self:
            opening_balance = 0
            invoice_ids = self.env['account.move'].search(
                [('invoice_date', '<', rec.from_date), ('state', '=', 'posted'),
                 ('partner_id', '=', rec.partner_id.id), ('move_type', '=', 'out_invoice')], order='invoice_date')
            invoice_total = 0
            for invoice in invoice_ids:
                invoice_total = invoice_total + invoice.amount_total
            credit_note_ids = self.env['account.move'].search(
                [('invoice_date', '<', rec.from_date), ('state', '=', 'posted'),
                 ('partner_id', '=', rec.partner_id.id), ('move_type', '=', 'out_refund')], order='invoice_date')
            credit_note_total = 0
            for credit_note in credit_note_ids:
                credit_note_total = credit_note_total + credit_note.amount_total
            payment_ids = self.env['account.payment'].search(
                [('date', '<', rec.from_date), ('state', '=', 'posted'),
                 ('partner_id', '=', rec.partner_id.id), ('partner_type', '=', 'customer')], order='date')
            receive_payment_total = 0
            send_payment_total = 0
            for payment in payment_ids:
                if payment.payment_type == 'inbound':
                    for move in payment.move_id.line_ids:
                        if move.account_id.user_type_id.type == 'receivable':
                            receive_payment_total = receive_payment_total + move.credit
                else:
                    for move in payment.move_id.line_ids:
                        if move.account_id.user_type_id.type == 'receivable':
                            send_payment_total = send_payment_total + move.debit
            opening_balance = (invoice_total +  send_payment_total) - (credit_note_total + receive_payment_total)
            rec.opening_balance = opening_balance
            return rec

    def create_line(self):
        for rec in self:
            rec.statement_lines.unlink()
            from_date = rec.from_date
            to_date = rec.to_date
            customer = rec.partner_id
            invoice_ids = self.env['account.move'].search(
                [('invoice_date', '>=', from_date), ('invoice_date', '<=', to_date), ('partner_id', '=', customer.id),
                 ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')], order='invoice_date')
            for invoice in invoice_ids:
                statement = self.env['customer.statement.line'].create({
                    'statement_id': rec.id,
                    'partner_id': customer.id,
                    'date': invoice.invoice_date,
                    'name': invoice.name,
                    'debit': invoice.amount_total,
                    'credit': 0,
                    'move_id': invoice.id
                })

            credit_note_ids = self.env['account.move'].search(
                [('invoice_date', '>=', from_date), ('invoice_date', '<=', to_date), ('partner_id', '=', customer.id),
                 ('state', '=', 'posted'), ('move_type', '=', 'out_refund')], order='invoice_date')
            for credit_note in credit_note_ids:
                statement = self.env['customer.statement.line'].create({
                    'statement_id': rec.id,
                    'partner_id': customer.id,
                    'date': credit_note.invoice_date,
                    'name': credit_note.name,
                    'debit': 0,
                    'credit': credit_note.amount_total,
                    'move_id': credit_note.id
                })

            payment_ids = self.env['account.payment'].search(
                [('date', '>=', from_date), ('date', '<=', to_date), ('state', '=', 'posted'),
                 ('partner_id', '=', customer.id), ('partner_type', '=', 'customer')], order='date')
            for payment in payment_ids:
                for line in payment.move_id.line_ids:
                    if line.debit != 0.0:
                        statement = self.env['customer.statement.line'].create({
                            'statement_id': rec.id,
                            'partner_id': customer.id,
                            'date': payment.date,
                            'name': payment.name,
                            'debit': 0,
                            'credit': line.debit,
                            'payment_id': payment.id
                        })
            return rec

    @api.depends('opening_balance', 'statement_lines')
    def _compute_closing_balance(self):
        for rec in self:
            closing_balance = rec.opening_balance
            if rec.statement_lines:
                debit = 0
                credit = 0
                for statement in rec.statement_lines:
                    debit += statement.debit
                    credit += statement.credit
                closing_balance = closing_balance + debit - credit
                rec.closing_balance = closing_balance
            else:
                rec.closing_balance = rec.opening_balance
            return rec

    @api.depends('statement_lines')
    def _compute_total_debit(self):
        for rec in self:
            total_debit = 0
            if rec.statement_lines:
                for statement in rec.statement_lines:
                    total_debit += statement.debit
                rec.total_debit = total_debit
            else:
                rec.total_debit = total_debit
            return rec

    @api.depends('statement_lines')
    def _compute_total_credit(self):
        for rec in self:
            total_credit = 0
            if rec.statement_lines:
                for statement in rec.statement_lines:
                    total_credit += statement.credit
                rec.total_credit = total_credit
            else:
                rec.total_credit = total_credit
            return rec

    @api.model
    def run_scheduler_daily(self):
        today = date.today()
        inv_partner = self.env['account.move'].search(
            [('state', '=', 'posted'), ('invoice_date', '=', today),
             ('move_type', 'in', ['out_invoice', 'out_refund'])]).mapped('partner_id.id')
        if inv_partner:
            partner_id = self.env['res.partner'].search([('id', 'in', inv_partner)])
            if partner_id:
                for partner in partner_id:
                    msc_id = self.env['customer.statement'].search(
                        [('from_date', '<=', today), ('to_date', '>=', today), ('partner_id', '=', partner.id)])
                    if msc_id:
                        msc_id.create_line()
                    else:
                        new_msc = self.env['customer.statement'].create({
                            'partner_id': partner.id,
                        })
                        new_msc.onchange_month()
                        new_msc.create_line()

    @api.model
    def run_scheduler_onetime(self):
        start_year = self.env['account.move'].search([], order="invoice_date asc", limit=1)
        year = []
        for i in range(int(start_year.invoice_date.strftime('%Y')), int(datetime.now().strftime('%Y'))+1):
            year.append(i)
        inv_partner = self.env['account.move'].search(
            [('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'out_refund'])]).mapped(
            'partner_id.id')
        if inv_partner:
            partner_id = self.env['res.partner'].search([('id', 'in', inv_partner)])
            if partner_id:
                for partner in partner_id:
                    inv_date = self.env['account.move'].search(
                        [('state', '=', 'posted'), ('partner_id', '=', partner.id), ('move_type', 'in',
                                                                                     ['out_invoice', 'out_refund'])])
                    if inv_date:
                        for inv in inv_date:
                            m = str(inv.invoice_date.month)
                            y = str(inv.invoice_date.year)
                            msc_id = self.env['customer.statement'].search(
                                [('month', '=', m), ('year', '=', y), ('partner_id', '=', partner.id)])
                            if msc_id:
                                msc_id.create_line()
                            else:
                                new_msc = self.env['customer.statement'].create({
                                    'partner_id': partner.id,
                                    'month': m,
                                    'year': y,
                                      })
                                new_msc.onchange_month()
                                new_msc.create_line()
                        # self._cr.commit()


class CustomerStatementLine(models.Model):
    _name = 'customer.statement.line'
    _description = 'customer statement lines'
    _order = 'date'

    statement_id = fields.Many2one('customer.statement', string='Statement')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    date = fields.Date(string='Date')
    name = fields.Char(string='Name')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    move_id = fields.Many2one('account.move', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')
