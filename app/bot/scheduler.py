"""
IRCTC Tatkal Automation Bot - Scheduling Logic
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import ntplib
import logging
from utils.logging import setup_logger
from bot.irctc_automation import IRCTCBot

class TatkalScheduler:
    """Scheduler for Tatkal booking automation"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.logger = setup_logger('tatkal_scheduler')
        self.scheduled_jobs = {}
        self.is_running = False
        
        # Start the scheduler
        self.start()
        
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            self.logger.info("Tatkal scheduler started")
            
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            self.logger.info("Tatkal scheduler stopped")
            
    def schedule_booking(self, booking_config, booking_time):
        """
        Schedule a Tatkal booking
        
        Args:
            booking_config (dict): Booking configuration
            booking_time (datetime): When to start booking
            
        Returns:
            str: Job ID
        """
        try:
            # Sync with NTP server for accurate timing
            accurate_time = self._get_accurate_time(booking_time)
            
            # Create job ID
            job_id = f"tatkal_{int(time.time())}"
            
            # Schedule the job
            job = self.scheduler.add_job(
                func=self._execute_booking,
                trigger=DateTrigger(run_date=accurate_time),
                args=[booking_config, job_id],
                id=job_id,
                name=f"Tatkal booking: {booking_config['from_station']} to {booking_config['to_station']}"
            )
            
            # Store job info
            self.scheduled_jobs[job_id] = {
                'job': job,
                'config': booking_config,
                'scheduled_time': accurate_time,
                'status': 'scheduled'
            }
            
            self.logger.info(f"Booking scheduled with job ID: {job_id} at {accurate_time}")
            
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error scheduling booking: {str(e)}")
            raise
            
    def cancel_booking(self, job_id):
        """Cancel a scheduled booking"""
        try:
            if job_id in self.scheduled_jobs:
                self.scheduler.remove_job(job_id)
                self.scheduled_jobs[job_id]['status'] = 'cancelled'
                self.logger.info(f"Cancelled booking job: {job_id}")
                return True
            else:
                self.logger.warning(f"Job not found: {job_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error cancelling booking: {str(e)}")
            return False
            
    def get_scheduled_bookings(self):
        """Get list of scheduled bookings"""
        return {
            job_id: {
                'scheduled_time': info['scheduled_time'],
                'status': info['status'],
                'from_station': info['config']['from_station'],
                'to_station': info['config']['to_station'],
                'journey_date': info['config']['journey_date'],
                'travel_class': info['config']['travel_class']
            }
            for job_id, info in self.scheduled_jobs.items()
        }
        
    def _execute_booking(self, booking_config, job_id):
        """Execute the actual booking"""
        try:
            self.logger.info(f"Starting booking execution for job: {job_id}")
            
            # Update job status
            if job_id in self.scheduled_jobs:
                self.scheduled_jobs[job_id]['status'] = 'running'
            
            # Create bot instance and start booking
            bot = IRCTCBot(config=booking_config)
            bot.start_booking()
            
            # Update job status based on result
            if bot.booking_result:
                if bot.booking_result['status'] == 'success':
                    self.scheduled_jobs[job_id]['status'] = 'completed'
                else:
                    self.scheduled_jobs[job_id]['status'] = 'failed'
            else:
                self.scheduled_jobs[job_id]['status'] = 'unknown'
                
        except Exception as e:
            self.logger.error(f"Booking execution failed for job {job_id}: {str(e)}")
            if job_id in self.scheduled_jobs:
                self.scheduled_jobs[job_id]['status'] = 'error'
                
    def _get_accurate_time(self, target_time):
        """Get accurate time synchronized with NTP server"""
        try:
            # Connect to NTP server
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request('pool.ntp.org', version=3)
            
            # Calculate time difference
            ntp_time = datetime.fromtimestamp(response.tx_time)
            local_time = datetime.now()
            time_diff = ntp_time - local_time
            
            # Adjust target time
            accurate_time = target_time + time_diff
            
            self.logger.info(f"Time synchronized with NTP. Difference: {time_diff.total_seconds()} seconds")
            
            return accurate_time
            
        except Exception as e:
            self.logger.warning(f"NTP sync failed: {str(e)}. Using local time.")
            return target_time
            
    def calculate_tatkal_time(self, journey_date, travel_class):
        """
        Calculate Tatkal booking opening time
        
        Args:
            journey_date (str): Journey date in YYYY-MM-DD format
            travel_class (str): Travel class code
            
        Returns:
            datetime: Tatkal booking opening time
        """
        journey_dt = datetime.strptime(journey_date, '%Y-%m-%d')
        
        # Tatkal booking opens 1 day before journey
        booking_date = journey_dt - timedelta(days=1)
        
        # AC classes: 10:00 AM, Non-AC classes: 11:00 AM
        if travel_class in ['1A', '2A', '3A', 'CC', 'EC']:
            booking_time = booking_date.replace(hour=10, minute=0, second=0, microsecond=0)
        else:
            booking_time = booking_date.replace(hour=11, minute=0, second=0, microsecond=0)
            
        return booking_time
        
    def get_time_until_tatkal(self, journey_date, travel_class):
        """Get time remaining until Tatkal booking opens"""
        tatkal_time = self.calculate_tatkal_time(journey_date, travel_class)
        now = datetime.now()
        
        if now >= tatkal_time:
            return timedelta(0)  # Tatkal time has passed
        else:
            return tatkal_time - now
            
    def is_tatkal_time_passed(self, journey_date, travel_class):
        """Check if Tatkal booking time has passed"""
        time_until = self.get_time_until_tatkal(journey_date, travel_class)
        return time_until.total_seconds() <= 0

class BookingQueue:
    """Queue system for managing multiple booking requests"""
    
    def __init__(self, max_concurrent=1):
        self.queue = []
        self.running_jobs = {}
        self.max_concurrent = max_concurrent
        self.logger = setup_logger('booking_queue')
        
    def add_to_queue(self, booking_config, priority=0):
        """Add booking to queue"""
        queue_item = {
            'id': f"queue_{int(time.time())}",
            'config': booking_config,
            'priority': priority,
            'added_at': datetime.now(),
            'status': 'queued'
        }
        
        # Insert based on priority
        inserted = False
        for i, item in enumerate(self.queue):
            if priority > item['priority']:
                self.queue.insert(i, queue_item)
                inserted = True
                break
                
        if not inserted:
            self.queue.append(queue_item)
            
        self.logger.info(f"Added booking to queue: {queue_item['id']}")
        return queue_item['id']
        
    def process_queue(self):
        """Process items in the queue"""
        while len(self.running_jobs) < self.max_concurrent and self.queue:
            item = self.queue.pop(0)
            self._start_booking_job(item)
            
    def _start_booking_job(self, queue_item):
        """Start a booking job from queue"""
        try:
            # Create bot and start in thread
            bot = IRCTCBot(config=queue_item['config'])
            
            def booking_thread():
                try:
                    bot.start_booking()
                    queue_item['status'] = 'completed'
                except Exception as e:
                    queue_item['status'] = 'failed'
                    self.logger.error(f"Booking failed: {str(e)}")
                finally:
                    # Remove from running jobs
                    if queue_item['id'] in self.running_jobs:
                        del self.running_jobs[queue_item['id']]
                    # Process next item in queue
                    self.process_queue()
            
            # Start thread
            thread = threading.Thread(target=booking_thread)
            thread.daemon = True
            thread.start()
            
            # Track running job
            self.running_jobs[queue_item['id']] = {
                'thread': thread,
                'bot': bot,
                'started_at': datetime.now(),
                'item': queue_item
            }
            
            queue_item['status'] = 'running'
            
        except Exception as e:
            queue_item['status'] = 'error'
            self.logger.error(f"Error starting booking job: {str(e)}")
            
    def get_queue_status(self):
        """Get current queue status"""
        return {
            'queued': len(self.queue),
            'running': len(self.running_jobs),
            'queue_items': [
                {
                    'id': item['id'],
                    'status': item['status'],
                    'added_at': item['added_at'].isoformat(),
                    'from_station': item['config']['from_station'],
                    'to_station': item['config']['to_station']
                }
                for item in self.queue
            ],
            'running_jobs': [
                {
                    'id': job_id,
                    'started_at': job_info['started_at'].isoformat(),
                    'from_station': job_info['item']['config']['from_station'],
                    'to_station': job_info['item']['config']['to_station']
                }
                for job_id, job_info in self.running_jobs.items()
            ]
        }