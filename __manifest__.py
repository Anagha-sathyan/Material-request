{
    'name': "Material Request",
    'version': '16.0.1.0.0',
    'depends': ['hr', 'purchase', 'stock', 'base'],
    'author': "Cybrosys",
    'summary': 'Material request',
    'description': """
    Request for products
    """,
    'auto_install': False,
    'installable': True,
    'application': True,
    'data': ['security/material_req_security.xml',
             'security/ir.model.access.csv',
             'views/material_request_views.xml',
             'data/material_request_sequence.xml',
             ],

    'license': 'LGPL-3',
}
