{
    'name': 'RealEstate',
    'sequence': -100,
    'depends': ['base', 'mail'],
    'data': ['security/ir.model.access.csv',
             'views/estate_view.xml',
             'views/property_type.xml',
             'views/user.xml',
             'data/data.xml',
             'report/report.xml',
             'report/property_card.xml'],
    'installable': True,
    'application': 'True'
}
