# -*- coding: utf-8 -*-
# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def chronopost_get_delivery_relaypoint(self):
        if self.carrier_id.product_code == '86':
            return True
        return False

    def cpst_get_names(self, partner_id, original_id=None):
        names = {'name1': partner_id.name, 'name2': ''}
        if partner_id.code_relaypoint:
            name2 = partner_id.parent_id.name
            if original_id:
                name2 = original_id.name
                if original_id.parent_id:
                    name2 = '%s (%s)' % (name2, original_id.parent_id.name)
            names.update({'name2': name2})
        else:
            if partner_id.parent_id.is_company:
                names.update({
                    'name1': partner_id.parent_id.name,
                    'name2': partner_id.name,
                    })
        return names
