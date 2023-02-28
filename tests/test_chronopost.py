# -*- coding: utf-8 -*-
# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo.tests import tagged
from .common import TestChronopostCommon


@tagged('post_install', '-at_install')
class TestChronopost(TestChronopostCommon):
    """Test the order of a sale with a chronopost shipping method.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        SaleOrder = cls.env['sale.order'].with_context(tracking_disable=True)
        # create a generic Sale Order with all classical products
        cls.sale_order = SaleOrder.create({
            'partner_id': cls.partner.id,
            'partner_invoice_id': cls.partner.id,
            'partner_shipping_id': cls.partner.id,
            'pricelist_id': cls.company_data['default_pricelist'].id,
        })
        cls.sol_product_order = cls.env['sale.order.line'].create({
            'name': cls.company_data['product_order_no'].name,
            'product_id': cls.company_data['product_order_no'].id,
            'product_uom_qty': 2,
            'product_uom': cls.company_data['product_order_no'].uom_id.id,
            'price_unit': cls.company_data['product_order_no'].list_price,
            'order_id': cls.sale_order.id,
            'tax_id': False,
        })

    def test_shipping(self):
        """ Test the flow of sales orders through to shipment with
            the chronopost carrier
        """
        self.sale_order.order_line.read(
            ['name', 'price_unit', 'product_uom_qty', 'price_total'])
        self.sale_order.carrier_id = self.delivery.id
        self.assertEqual(self.sale_order.amount_total,
            560.0, 'Sale: total amount is wrong')

        # confirm quotation
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.picking_ids,
            'Sale Stock: no picking created for "invoice on delivery"'
                'storable products')
        self.assertTrue(self.sale_order.state == 'sale')
        self.assertTrue(self.sale_order.invoice_status == 'to invoice')

        # order delivery
        self.assertEqual(self.sale_order.delivery_count,
            1.0, 'Delivery: the number of deliveries is wrong')
        self.assertEqual(self.sale_order.picking_ids.carrier_id.name,
            'Chronopost Express', 'Delivery: the delivery carrier is wrong')
        self.assertTrue(self.sale_order.picking_ids.state == 'assigned')

        # pack the order
        pack = self.sale_order.picking_ids.action_put_in_pack()
        pack['context'].update({
            # Packaging Chronopost
            'shipping_weight': 5.0,
            'delivery_packaging_id': self.package,
            'picking_ids': self.sale_order.picking_ids,
        })
        wiz_pack = self.env['choose.delivery.package'].with_context(
            pack['context']).create({})
        wiz_pack.action_put_in_pack()
        self.assertTrue(self.sale_order.picking_ids.package_ids,
            'Picking: no packages ready to this shipment')
        self.assertEqual(len(self.sale_order.picking_ids.package_ids),
            1.0, 'Picking: number of package made is wrong')

        # validate the delivery
        self.sale_order.picking_ids.button_validate()
        self.assertTrue(self.sale_order.picking_ids.state == 'done')
        self.assertTrue(self.sale_order.picking_ids.carrier_tracking_ref,
            'Tracking number: No tracking number for this shipment')

    def test_shipping_relaypoint(self):
        """ Test the flow of sales orders through to shipment with
            the chronopost carrier in relaypoint (2shop) in France
        """
        self.sale_order.order_line.read(
            ['name', 'price_unit', 'product_uom_qty', 'price_total'])
        self.sale_order.carrier_id = self.relaypoint_delivery.id
        self.assertEqual(self.sale_order.amount_total,
            560.0, 'Sale: total amount is wrong')

        # confirm quotation
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.picking_ids,
            'Sale Stock: no picking created for "invoice on delivery"'
                'storable products')
        self.assertTrue(self.sale_order.state == 'sale')
        self.assertTrue(self.sale_order.invoice_status == 'to invoice')

        # order delivery
        self.assertEqual(self.sale_order.delivery_count,
            1.0, 'Delivery: the number of deliveries is wrong')
        self.assertEqual(self.sale_order.picking_ids.carrier_id.name,
            'Chronopost Express Relais',
            'Delivery: the delivery carrier is wrong')
        self.assertTrue(self.sale_order.picking_ids.state == 'assigned')

        # pack the order
        pack = self.sale_order.picking_ids.action_put_in_pack()
        pack['context'].update({
            # Packaging Chronopost
            'shipping_weight': 5.0,
            'delivery_packaging_id': self.package,
            'picking_ids': self.sale_order.picking_ids,
        })
        wiz_pack = self.env['choose.delivery.package'].with_context(
            pack['context']).create({})
        wiz_pack.action_put_in_pack()
        self.assertTrue(self.sale_order.picking_ids.package_ids,
            'Picking: no packages ready to this shipment')
        self.assertEqual(len(self.sale_order.picking_ids.package_ids),
            1.0, 'Picking: number of package made is wrong')

        # choose a relaypoint
        wiz = self.sale_order.picking_ids.action_get_relaypoint()
        relaypoint = self.env['delivery.carrier.relaypoint'].with_context(
            wiz['context']).create({})
        relaypoint.get_relaypoint()
        relaypoint = relaypoint.lines[0].set_destination()
        self.sale_order.picking_ids.relaypoint_delivery = relaypoint

        # validate the delivery
        self.sale_order.picking_ids.button_validate()
        self.assertTrue(self.sale_order.picking_ids.state == 'done')
        self.assertTrue(self.sale_order.picking_ids.carrier_tracking_ref,
            'Tracking number: No tracking number for this shipment')

