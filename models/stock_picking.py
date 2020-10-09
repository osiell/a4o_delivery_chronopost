# -*- coding: utf-8 -*-
# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cpst_product_code = fields.Char(
        'Product Code', related='carrier_id.product_code')

    @api.depends('partner_id')
    def cpst_get_names(self, parent=False):
        names = {
            'company': '',
            'name': (self.partner_id.name if not parent
                else self.partner_id.parent_id.name),
            }
        if self.partner_id.parent_id and self.partner_id.parent_id.is_company:
            # if link to company get company name.
            names.update({'company': self.partner_id.parent_id.name})
        return names
