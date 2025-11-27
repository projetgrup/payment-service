from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class EscrowSync(models.TransientModel):
    _name = 'escrow.sync'
    _description = 'Escrow Sync Wizard'

    def confirm(self):
        company = self.env.company
        result, message = self.env['syncops.connector'].sudo()._execute('other_get_vpic_brand', reference=str(self.id), params={},company=company,  message=True)
        if not result:
            raise Exception(message)
        for brand in result:
            self.env['escrow.brand.sync.line'].create({
                'wizard_id': self.id,
                'escrow_car_brand_name': brand.get('brand'),
                'escrow_car_brand_id': brand.get('brand_id'),
            })
        try:
            tree_view_id = self.env.ref('payment_escrow.escrow_brand_sync_line_view').id
        except Exception:
            tree_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'escrow.brand.sync.line',
            'view_mode': 'tree',
            'target': 'new',
            'views': [(tree_view_id, 'tree')],
            'context': {'default_wizard_id': self.id},
        }

    escrow_brand_line_ids = fields.One2many('escrow.brand.sync.line', 'wizard_id', string='Lines')
    
    @api.model
    def action_sync(self):
        self.env['escrow.brand.sync.line'].search([]).unlink()
        return self.confirm()


class EscrowBrandSyncLine(models.TransientModel):
    _name = 'escrow.brand.sync.line'
    _description = 'Escrow Brand Sync Line'

    wizard_id = fields.Many2one('escrow.sync', string='Wizard')
    escrow_car_brand_name = fields.Char(string='Brand Name')
    escrow_car_brand_id = fields.Integer(string='Brand ID')


    def action_sync_brand(self):
        for line in self:
            existing_brand = self.env['escrow.car.brand'].search([
                ('name', '=', line.escrow_car_brand_name)
            ], limit=1)
            
            if not existing_brand:
                brand_vals = {
                    'name': line.escrow_car_brand_name,
                    'brand_id': line.escrow_car_brand_id,
                    'active': True,
                }
                self.env['escrow.car.brand'].create(brand_vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'{len(self)} brand(s) synced successfully!',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_sync_brand_async(self):
        total = len(self)
        if total == 0:
            return {'success': False, 'message': 'No records selected'}
        
        channel_name = f'escrow_brand_sync_{self.env.uid}_{self.env.cr.dbname}'
        self.with_delay(channel='root', description='Brand Sync Job')._process_sync_job(channel_name, self.ids)
        
        return {
            'success': True,
            'channel': channel_name,
            'total': total,
        }

    def _process_sync_job(self, channel_name, line_ids):
        import time
        
        lines = self.browse(line_ids).exists()
        total = len(lines)
        processed = 0

        self._send_bus_notification(channel_name, {
            'type': 'progress',
            'processed': 0,
            'total': total,
            'message': 'Starting brand sync...',
        })
        
        try:
            brand_model = self.env['escrow.car.brand'].sudo()
            for line in lines:
                time.sleep(10)
                
                existing_brand = brand_model.search([
                    ('name', '=', line.escrow_car_brand_name)
                ], limit=1)
                
                if not existing_brand:
                    brand_vals = {
                        'name': line.escrow_car_brand_name,
                        'brand_id': line.escrow_car_brand_id,
                        'active': True,
                    }
                    brand_model.create(brand_vals)
                
                processed += 1
                
                if processed % 1 == 0 or processed == total:
                    self._send_bus_notification(channel_name, {
                        'type': 'progress',
                        'processed': processed,
                        'total': total,
                        'message': f'Processed {processed}/{total} brands...',
                    })
                    self.env.cr.commit()
            
            self._send_bus_notification(channel_name, {
                'type': 'complete',
                'processed': total,
                'total': total,
                'message': f'{total} brand(s) synced successfully!',
            })
            
        except Exception as e:
            _logger.exception('Brand sync job failed')
            self._send_bus_notification(channel_name, {
                'type': 'error',
                'message': str(e),
            })

    def _send_bus_notification(self, channel_name, message):
        self.env['bus.bus']._sendone(channel_name, 'brand_sync_progress', message)
        self.env.cr.commit()