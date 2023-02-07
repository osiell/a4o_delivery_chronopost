# -*- coding: utf-8 -*-
# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo.addons.base.tests.common import TransactionCase

class TestChronopostCommon(TransactionCase):
    ''' Setup with chronopost test configuration. '''
    @classmethod
    def setUpClass(cls):
        super(TestChronopostCommon, cls).setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'partner_a',
            'street': '8 rue germain nouveau',
            'street2': '10 rue jean daret',
            'city': 'Aix en provence',
            'zip': '13090',
            'country_id': cls.env['res.country'].search([ 
                ('code','=', 'FR'),]).id,
            'company_id': False,
        })
        cls.product_service_delivery = cls.env['product.product'].search([
                ('name','=', 'Chronopost Relay (Chrono Relay 13)'),
            ])
        cls.delivery_carrier = cls.env['delivery.carrier'].search([
                ('name','=', 'Chronopost Express'),
            ])
        cls.package = cls.env['product.packaging'].search([
                ('name','=', 'Chronopost Custom Parcel'),
            ])
        cls.company_data = {
            # Pricelist
            'default_pricelist': cls.env['product.pricelist'].create({
                'name': 'default_pricelist',
                'currency_id': cls.env.company.currency_id.id,
            }),
            # Product category
            'product_category': cls.env['product.category'].create({
                'name': 'Test category',
            }),
        }
        cls.company_data.update({
            'product_order_no': cls.env['product.product'].create({
                'name': 'product_order_no',
                'categ_id': cls.company_data['product_category'].id,
                'standard_price': 235.0,
                'list_price': 280.0,
                'type': 'consu',
                'weight': 0.01,
                'uom_id': cls.env.ref('uom.product_uom_unit').id,
                'uom_po_id': cls.env.ref('uom.product_uom_unit').id,
                'default_code': 'FURN_9999',
                'invoice_policy': 'order',
                'expense_policy': 'no',
                'taxes_id': [(6, 0, [])],
                'supplier_taxes_id': [(6, 0, [])],
            }),
        })