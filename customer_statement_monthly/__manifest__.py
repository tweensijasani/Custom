# -*- coding: utf-8 -*-

{
    'name': 'Customer Statement Monthly',
    'version': '14.0.0.1.0',
    'sequence': 0,
    'summary': 'Track monthly customer statements',
    'description': """

    """,
    'depends': ['base', 'account', 'utm'],
    'data': [
        'data/customer_statement_scheduler.xml',
        'security/ir.model.access.csv',
        'security/statement_security.xml',
        'views/customer_statement.xml',
        'report/customer_statement_report.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
