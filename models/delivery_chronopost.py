# -*- coding: utf-8 -*-
# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
from odoo.tools import pdf
from .chronopost_request import ChronopostRequest
import re
import logging

_logger = logging.getLogger(__name__)

#class RelayPointChronopost(models.Model):
#    _inherit = 'delivery.carrier.relaypoint'
#    
#    cpst_url_google_maps = fields.Char(
#        string='URL Google Maps', groups="base.group_system")


class ProviderChronopost(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('chronopost', "Chronopost")])
    product_code = fields.Char(
        string='Product Code', groups="base.group_system", size=2,
        help="Product code defined on the contract signed with Chronopost")
    cpst_prod_account_number = fields.Char(
        string='Account Number (prod.)', groups="base.group_system", size=8,
        help="Production account number, will be used when this carrier has "
             "gone 'into production'.")
    cpst_prod_sub_account = fields.Char(
        string='Sub Account (prod.)', default='000', size=3,
        groups="base.group_system",
        help="Production sub-account number, can remain empty.")
    cpst_prod_passwd = fields.Char(
        string='Password (prod.)', groups="base.group_system", size=6,
        help="Production password, will be used when this carrier has gone "
             "'into production'.")
    cpst_test_account_number = fields.Char(
        string='Account Number (test)', groups="base.group_system", size=8,
        help="Test account number, will be used when this carrier has gone "
             "'into test'.")
    cpst_test_sub_account = fields.Char(
        string='Sub Account (test)', default='000', size=3,
        groups="base.group_system",
        help="Test sub-account number, can remain empty.")
    cpst_test_passwd = fields.Char(
        string='Password (test)', groups="base.group_system", size=6,
        help="Test password, will be used when this carrier has gone "
             "'into test'.")
    cpst_label_format = fields.Selection([
        ('PDF', 'PDF'),
        ('Z2D', 'Z2D'),
        ('ZPL300', 'ZPL300'),
    ], string="Label Format", required=True, default='PDF')
    cpst_remove_label = fields.Boolean(
        'Remove attached label', default=False,
        help="When canceling a shipment, remove the attached labels.")
    cpst_shipping_url = fields.Char(
        string='Shipping URL', groups="base.group_system",
        help="WSDL url for shipping.")
    cpst_tracking_url = fields.Char(
        string='Tracking URL', groups="base.group_system",
        help="WSDL url for tracking and cancelling.")
    cpst_relaypoint_url = fields.Char(
        string='Relay Point URL', groups="base.group_system",
        help="WSDL url for searching relay point.")
    cpst_max_point = fields.Integer(
        string="Relay Points Max", default=5,
        help="Max number of relay points returned by the search request.")
    cpst_distance_search = fields.Integer(
        string="Search distance", default=10,
        help="Maximum search distance of relay points in the request.")

    def _check_value(self, value, size):
        if re.search("[^0-9]", value):
            raise UserError(_('Only digit chars are authorised in this field!'))
        if len(value) != size:
            raise UserError(_('This field must have to %s characters!') % size)
        return value

    @api.onchange('cpst_prod_account_number')
    def onchange_cpst_prod_account_number(self):
        self.cpst_prod_account_number = self._check_value(
            self.cpst_prod_account_number, 8)
    
    @api.onchange('cpst_test_account_number')
    def onchange_cpst_test_account_number(self):
        self.cpst_test_account_number = self._check_value(
            self.cpst_test_account_number, 8)
    
    @api.onchange('cpst_prod_passwd')
    def onchange_cpst_prod_passwd(self):
        self.cpst_prod_passwd = self._check_value(
            self.cpst_prod_passwd, 6)
        
    @api.onchange('cpst_test_passwd')
    def onchange_cpst_test_passwd(self):
        self.cpst_test_passwd = self._check_value(
            self.cpst_test_passwd, 6)

    def chronopost_send_shipping(self, pickings):
        _logger.debug("chronopost_send_shipping: begin")
        res = []
        cpst = ChronopostRequest(self.prod_environment, self.log_xml)
        for picking in pickings:
            package_count = len(picking.package_ids) or 1
            _logger.debug(
                "chronopost_send_shipping: Pack. count: %s" % package_count)
            shipping = cpst.shipping_request(picking, self)
            carrier_tracking_ref = shipping['tracking_number']
            
            currency = (
                picking.sale_id.currency_id or picking.company_id.currency_id)
            if currency.name == shipping['currency']:
                carrier_price = float(shipping['price'])
            else:
                quote_currency = self.env['res.currency'].search([
                    ('name', '=', shipping['currency']),
                    ], limit=1)
                carrier_price = quote_currency._convert(
                    float(shipping['price']), currency, company,
                    picking.sale_id.date_order or fields.Date.today())
            
            package_labels = cpst.get_label()
            log_message = (
                _("Shipment created into Chronopost<br/> "
                    "<b>Tracking Numbers:</b> %s<br/>"
                    "<b>Packages:</b> %s") % (
                        carrier_tracking_ref,
                        ', '.join([pl[0] for pl in package_labels])))
            if self.cpst_label_format == 'PDF':
                attachments = [(
                        _('Label_Chronopost.pdf'),
                        pdf.merge_pdf([pl[1] for pl in package_labels]))]
            else:
                attachments = [(
                    _('Label_Chronopost-%s.%s') % (
                        pl[0], self.cpst_label_format),
                    pl[1]) for pl in package_labels]
            picking.message_post(body=log_message, attachments=attachments)
            shipping_data = {
                'exact_price': carrier_price,
                'tracking_number': carrier_tracking_ref,
                }
            res += [shipping_data]
        return res
    
    def chronopost_cancel_shipment(self, picking):
        cpst = ChronopostRequest(self.prod_environment, self.log_xml)
        result = cpst.cancel_request(picking, self)
        if result:
            # Remove attachment ...
            if self.cpst_remove_label:
                attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', picking._name),
                    ('res_id', '=', picking.id),
                    ('name', 'like', '_Chronopost'),
                    ])
                if attachments:
                    attachments.unlink()
            picking.message_post(
                body=_("Chronopost expedition with tracking number %s "
                    "canceled!") % (picking.carrier_tracking_ref))
            picking.write({
                'carrier_tracking_ref': '',
                'carrier_price': 0.0,
                })
    
    def chronopost_get_tracking_link(self, picking):
        lang = 'en'
        if self.env.context.get('lang') == 'fr_FR':
            lang = 'fr'
        return ('http://www.chronopost.fr/tracking-no-cms/suivi-page?langue=%s'
                '&listeNumerosLT=%s' % (lang, picking.carrier_tracking_ref))

    def chronopost_rate_shipment(self, order):
        res = {'success': False}
        if order.delivery_price:
            res.update({
                'success': True,
                'price': order.delivery_price,
                })
        else:
            # [TODO] Compute the price if ...
            pass
        return res

    def chronopost_select_relaypoint(self, pickings):
        _logger.debug('chronopost_select_relaypoint:' % pickings)
        relaypoints = []
        cpst = ChronopostRequest(self.prod_environment, self.log_xml)
        for picking in pickings:
            relaypoints += cpst.relaypoint_request(picking, self)
        return relaypoints
