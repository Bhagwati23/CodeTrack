"""
Background Notification Scheduler for CodeTrack Pro
Runs every 5 minutes to check for scheduled notifications
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from threading import Thread, Event
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Background scheduler for notifications"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.stop_event = Event()
        
        # Setup scheduled jobs
        self._setup_scheduled_jobs()
    
    def start(self):
        """Start the notification scheduler"""
        
        if self.is_running:
            logger.warning("Notification scheduler is already running")
            return
        
        try:
            self.scheduler.start()
            self.is_running = True
            logger.info("Notification scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start notification scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the notification scheduler"""
        
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Notification scheduler stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop notification scheduler: {e}")
    
    def _setup_scheduled_jobs(self):
        """Setup all scheduled notification jobs"""
        
        # Check for upcoming contests every 5 minutes
        self.scheduler.add_job(
            func=self._check_upcoming_contests,
            trigger=IntervalTrigger(minutes=5),
            id='check_upcoming_contests',
            name='Check for upcoming contests',
            replace_existing=True
        )
        
        # Check for unanswered forum questions every 5 minutes
        self.scheduler.add_job(
            func=self._check_unanswered_questions,
            trigger=IntervalTrigger(minutes=5),
            id='check_unanswered_questions',
            name='Check for unanswered forum questions',
            replace_existing=True
        )
        
        # Check for study reminders daily at 9 AM
        self.scheduler.add_job(
            func=self._send_study_reminders,
            trigger=CronTrigger(hour=9, minute=0),
            id='send_study_reminders',
            name='Send daily study reminders',
            replace_existing=True
        )
        
        # Clean up old notifications daily at midnight
        self.scheduler.add_job(
            func=self._cleanup_old_notifications,
            trigger=CronTrigger(hour=0, minute=0),
            id='cleanup_old_notifications',
            name='Clean up old notifications',
            replace_existing=True
        )
        
        # Update user streaks daily at midnight
        self.scheduler.add_job(
            func=self._update_user_streaks,
            trigger=CronTrigger(hour=0, minute=5),
            id='update_user_streaks',
            name='Update user coding streaks',
            replace_existing=True
        )
        
        logger.info("Scheduled notification jobs configured")
    
    def _check_upcoming_contests(self):
        """Check for upcoming contests and send notifications"""
        
        try:
            from models import Contest, User, db
            from services.notification_service import notification_service
            
            current_time = datetime.now()
            
            # Find contests starting in the next 5 minutes (5-minute warning)
            five_minutes_from_now = current_time + timedelta(minutes=5)
            five_minute_contests = Contest.query.filter(
                Contest.start_date <= five_minutes_from_now,
                Contest.start_date > current_time,
                Contest.is_active == True
            ).all()
            
            for contest in five_minute_contests:
                # Get all participants
                participants = User.query.join(Contest.participants).filter(
                    Contest.id == contest.id
                ).all()
                
                # Send 5-minute warning notification
                notification_service.create_bulk_notifications(
                    template_key="contest_5min_warning",
                    user_ids=[p.id for p in participants],
                    context={"contest_title": contest.title},
                    contest_id=contest.id
                )
            
            # Find contests starting in 24 hours (24-hour reminder)
            twenty_four_hours_from_now = current_time + timedelta(hours=24)
            twenty_four_hour_contests = Contest.query.filter(
                Contest.start_date <= twenty_four_hours_from_now,
                Contest.start_date > current_time + timedelta(hours=23, minutes=55),
                Contest.is_active == True
            ).all()
            
            for contest in twenty_four_hour_contests:
                # Get all users (not just participants, as they might want to join)
                all_users = User.query.filter_by(role='student').all()
                
                # Send 24-hour reminder notification
                notification_service.create_bulk_notifications(
                    template_key="contest_24h_reminder",
                    user_ids=[u.id for u in all_users],
                    context={"contest_title": contest.title},
                    contest_id=contest.id
                )
            
            logger.info(f"Checked upcoming contests: {len(five_minute_contests)} 5-min, {len(twenty_four_hour_contests)} 24-hr")
            
        except Exception as e:
            logger.error(f"Error checking upcoming contests: {e}")
    
    def _check_unanswered_questions(self):
        """Check for unanswered forum questions and generate AI answers"""
        
        try:
            from models import ForumPost, ForumAnswer, db
            from services.ai_providers import ai_provider
            from services.notification_service import notification_service
            
            current_time = datetime.now()
            
            # Find questions that are 24 hours old and have no human answers
            twenty_four_hours_ago = current_time - timedelta(hours=24)
            
            unanswered_questions = ForumPost.query.filter(
                ForumPost.created_at <= twenty_four_hours_ago,
                ForumPost.ai_answer_deadline <= current_time,
                ForumPost.is_solved == False
            ).all()
            
            for question in unanswered_questions:
                # Check if AI answer already exists
                existing_ai_answer = ForumAnswer.query.filter_by(
                    post_id=question.id,
                    is_ai_generated=True
                ).first()
                
                if not existing_ai_answer:
                    # Generate AI answer
                    ai_response = ai_provider.generate_response(
                        f"Answer this programming question: {question.title}\n\n{question.content}"
                    )
                    
                    if "error" not in ai_response:
                        # Create AI answer
                        ai_answer = ForumAnswer(
                            post_id=question.id,
                            content=ai_response["content"],
                            is_ai_generated=True,
                            is_anonymous=True
                        )
                        
                        db.session.add(ai_answer)
                        db.session.commit()
                        
                        # Notify the question author
                        notification_service.create_notification(
                            template_key="forum_ai_answer",
                            user_id=question.author_id,
                            context={"question_title": question.title},
                            forum_post_id=question.id
                        )
                        
                        logger.info(f"Generated AI answer for question {question.id}")
            
            logger.info(f"Checked unanswered questions: {len(unanswered_questions)} processed")
            
        except Exception as e:
            logger.error(f"Error checking unanswered questions: {e}")
    
    def _send_study_reminders(self):
        """Send daily study reminders to users"""
        
        try:
            from models import User, DailyCodingHours, db
            from services.notification_service import notification_service
            from services.spaced_repetition import spaced_repetition_manager
            
            yesterday = datetime.now().date() - timedelta(days=1)
            
            # Find users who didn't code yesterday
            users_without_coding = db.session.query(User).filter(
                ~User.id.in_(
                    db.session.query(DailyCodingHours.user_id).filter(
                        DailyCodingHours.date == yesterday
                    )
                ),
                User.role == 'student'
            ).all()
            
            for user in users_without_coding:
                # Check if they have flashcards due
                due_flashcards = spaced_repetition_manager.get_due_cards_count(user.id)
                
                if due_flashcards > 0:
                    notification_service.create_custom_notification(
                        user_id=user.id,
                        title="Study Reminder",
                        message=f"You have {due_flashcards} flashcards due for review. Keep up your learning streak!",
                        notification_type="info",
                        category="system"
                    )
                else:
                    notification_service.create_custom_notification(
                        user_id=user.id,
                        title="Daily Coding Challenge",
                        message="Ready for today's coding challenge? Solve some problems and maintain your streak!",
                        notification_type="info",
                        category="system"
                    )
            
            logger.info(f"Sent study reminders to {len(users_without_coding)} users")
            
        except Exception as e:
            logger.error(f"Error sending study reminders: {e}")
    
    def _cleanup_old_notifications(self):
        """Clean up old notifications"""
        
        try:
            from services.notification_service import notification_service
            
            deleted_count = notification_service.delete_old_notifications(days_old=30)
            logger.info(f"Cleaned up {deleted_count} old notifications")
            
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {e}")
    
    def _update_user_streaks(self):
        """Update user coding streaks"""
        
        try:
            from models import User, DailyCodingHours, db
            from services.notification_service import notification_service
            
            all_users = User.query.filter_by(role='student').all()
            
            for user in all_users:
                # Calculate current streak
                current_streak = self._calculate_coding_streak(user.id)
                
                # Update platform stats
                for platform_stat in user.platform_stats:
                    old_streak = platform_stat.streak
                    platform_stat.streak = current_streak
                    
                    # Check for streak milestones
                    if current_streak > 0 and current_streak % 7 == 0 and current_streak != old_streak:
                        # Weekly streak milestone
                        notification_service.create_notification(
                            template_key="streak_milestone",
                            user_id=user.id,
                            context={"days": current_streak}
                        )
            
            db.session.commit()
            logger.info("Updated user coding streaks")
            
        except Exception as e:
            logger.error(f"Error updating user streaks: {e}")
    
    def _calculate_coding_streak(self, user_id: int) -> int:
        """Calculate current coding streak for a user"""
        
        try:
            from models import DailyCodingHours
            
            # Get last 30 days of coding activity
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            
            coding_days = DailyCodingHours.query.filter(
                DailyCodingHours.user_id == user_id,
                DailyCodingHours.date >= thirty_days_ago,
                DailyCodingHours.hours > 0
            ).order_by(DailyCodingHours.date.desc()).all()
            
            if not coding_days:
                return 0
            
            # Calculate streak
            streak = 0
            current_date = datetime.now().date()
            
            for coding_day in coding_days:
                if coding_day.date == current_date - timedelta(days=streak):
                    streak += 1
                else:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating coding streak: {e}")
            return 0
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
            
            return {
                "is_running": self.is_running,
                "jobs": jobs,
                "job_count": len(jobs)
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {"is_running": False, "jobs": [], "job_count": 0}
    
    def trigger_job_manually(self, job_id: str) -> bool:
        """Manually trigger a scheduled job"""
        
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"Manually triggered job: {job_id}")
                return True
            else:
                logger.warning(f"Job not found: {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering job {job_id}: {e}")
            return False

# Global instance
notification_scheduler = NotificationScheduler()
