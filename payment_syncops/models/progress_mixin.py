# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError
import logging
import functools

_logger = logging.getLogger(__name__)

def track_progress(channel_prefix='job_progress', description='Job Progress', queue=False, notification_type=None):
    """
    Decorator to automatically handle progress tracking for a method.
    The decorated method must accept 'channel_name' as its first argument after 'self'.
    
    :param channel_prefix: Prefix for the bus channel
    :param description: Description of the job for notifications
    :param queue: If True, calling the method will automatically schedule it as a queue job
                  and return the progress configuration dict.
    :param notification_type: The event type to send to the bus (default: 'brand_sync_progress')
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check if we are in a job execution context
            # queue_job usually sets 'job_uuid' in context
            is_job_execution = self.env.context.get('job_uuid') or kwargs.get('is_job_execution')
            
            # If queue=True and we are NOT in a job, we schedule the job
            if queue and not is_job_execution:
                # Generate channel name
                channel_name = self._get_progress_channel()
                
                # Prepare arguments for the job
                # We assume the first argument is channel_name.
                # If the caller passed None or nothing, we inject the channel_name.
                new_args = list(args)
                if len(new_args) > 0:
                    # If first arg is None, replace it
                    if new_args[0] is None:
                        new_args[0] = channel_name
                else:
                    # If no args, prepend channel_name
                    new_args = [channel_name]
                
                # Schedule the job
                # We call the method by name on the delayed record to ensure queue_job intercepts it
                delayed_method = getattr(self.with_delay(channel='root', description=description), func.__name__)
                delayed_method(*new_args, **kwargs)
                
                # Return the frontend configuration
                return {
                    'success': True,
                    'channel': channel_name,
                    'total': len(self) if hasattr(self, '__len__') else 0,
                }

            # Execution Logic (Worker or Sync)
            
            # Determine channel_name from args
            if args:
                channel_name = args[0]
            else:
                channel_name = f'{channel_prefix}_{self.env.uid}_{self.env.cr.dbname}'
            
            # Initial notification
            self._send_progress_notification(channel_name, {
                'type': 'progress',
                'processed': 0,
                'total': len(self) if hasattr(self, '__len__') else 0,
                'message': f'Starting {description}...',
            }, notification_type=notification_type)
            
            try:
                result = func(self, *args, **kwargs)
                
                # Final notification
                total = len(self) if hasattr(self, '__len__') else 0
                self._send_progress_notification(channel_name, {
                    'type': 'complete',
                    'processed': total,
                    'total': total,
                    'message': f'{description} completed successfully!',
                }, notification_type=notification_type)
                return result
                
            except Exception as e:
                _logger.exception(f'{description} failed')
                self._send_progress_notification(channel_name, {
                    'type': 'error',
                    'message': str(e),
                }, notification_type=notification_type)
                raise e
        return wrapper
    return decorator


class ProgressMixin(models.AbstractModel):
    _name = 'progress.mixin'
    _description = 'Progress Tracking Mixin'

    def _send_progress_notification(self, channel_name, message, notification_type=None):
        """
        Sends a notification to the bus.
        message structure:
        {
            'type': 'progress' | 'complete' | 'error',
            'processed': int,
            'total': int,
            'message': str
        }
        """
        self.env['bus.bus']._sendone(channel_name, notification_type, message)
        # Commit is often needed to ensure the bus notification is sent immediately
        # especially in long-running jobs
        if not self.env.context.get('no_commit'):
            self.env.cr.commit()

    def _get_progress_channel(self):
        """Helper to generate a unique channel name for the current user/session"""
        return f'progress_{self.env.uid}_{self.env.cr.dbname}'

    def track_iterator(self, collection, channel_name, description='Processing', notification_type=None):
        """
        Iterates over a collection and sends progress updates automatically.
        Usage:
            for line in self.track_iterator(lines, channel_name, 'Syncing'):
                # do work
        """
        total = len(collection)
        processed = 0
        
        for item in collection:

            yield item
            processed += 1
            
            # Send update
            self._send_progress_notification(channel_name, {
                'type': 'progress',
                'processed': processed,
                'total': total,
                'message': f'{description} ({processed}/{total})...',
            }, notification_type=notification_type)
