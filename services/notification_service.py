"""
Comprehensive Notification Management System for CodeTrack Pro
Handles contest notifications, forum alerts, study group messages, and system notifications
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Notification types"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class NotificationCategory(Enum):
    """Notification categories"""
    CONTEST = "contest"
    FORUM = "forum"
    STUDY_GROUP = "study_group"
    SYSTEM = "system"
    ACHIEVEMENT = "achievement"

@dataclass
class NotificationTemplate:
    """Notification template structure"""
    title: str
    message: str
    type: NotificationType
    category: NotificationCategory
    icon: str
    action_url: Optional[str] = None

class NotificationService:
    """Main notification service"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, NotificationTemplate]:
        """Initialize notification templates"""
        
        templates = {
            # Contest notifications
            "contest_created": NotificationTemplate(
                title="New Contest Available!",
                message="A new coding contest '{contest_title}' has been created. Join now!",
                type=NotificationType.INFO,
                category=NotificationCategory.CONTEST,
                icon="trophy",
                action_url="/contest/{contest_id}/participate"
            ),
            "contest_24h_reminder": NotificationTemplate(
                title="Contest Starting Soon!",
                message="Contest '{contest_title}' starts in 24 hours. Prepare yourself!",
                type=NotificationType.WARNING,
                category=NotificationCategory.CONTEST,
                icon="clock",
                action_url="/contest/{contest_id}"
            ),
            "contest_5min_warning": NotificationTemplate(
                title="Contest Starting Now!",
                message="Contest '{contest_title}' starts in 5 minutes. Get ready!",
                type=NotificationType.WARNING,
                category=NotificationCategory.CONTEST,
                icon="alarm",
                action_url="/contest/{contest_id}/participate"
            ),
            "contest_ended": NotificationTemplate(
                title="Contest Results Available",
                message="Contest '{contest_title}' has ended. Check your results!",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.CONTEST,
                icon="chart-bar",
                action_url="/contest/{contest_id}/leaderboard"
            ),
            
            # Forum notifications
            "forum_question_posted": NotificationTemplate(
                title="New Question in Forum",
                message="A new question '{question_title}' has been posted in the forum.",
                type=NotificationType.INFO,
                category=NotificationCategory.FORUM,
                icon="question-circle",
                action_url="/forum/question/{question_id}"
            ),
            "forum_answer_received": NotificationTemplate(
                title="Answer Received",
                message="Someone answered your question '{question_title}'.",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.FORUM,
                icon="reply",
                action_url="/forum/question/{question_id}"
            ),
            "forum_ai_answer": NotificationTemplate(
                title="AI Answer Generated",
                message="An AI answer has been generated for your question '{question_title}'.",
                type=NotificationType.INFO,
                category=NotificationCategory.FORUM,
                icon="robot",
                action_url="/forum/question/{question_id}"
            ),
            
            # Study group notifications
            "study_group_joined": NotificationTemplate(
                title="Joined Study Group",
                message="You have successfully joined the study group '{group_name}'.",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.STUDY_GROUP,
                icon="users",
                action_url="/study/groups/{group_id}/chat"
            ),
            "study_group_message": NotificationTemplate(
                title="New Group Message",
                message="New message in study group '{group_name}' from {sender_name}.",
                type=NotificationType.INFO,
                category=NotificationCategory.STUDY_GROUP,
                icon="message",
                action_url="/study/groups/{group_id}/chat"
            ),
            "study_group_question": NotificationTemplate(
                title="Group Question Posted",
                message="A new question has been posted in your study group '{group_name}'.",
                type=NotificationType.INFO,
                category=NotificationCategory.STUDY_GROUP,
                icon="question-circle",
                action_url="/study/groups/{group_id}/questions"
            ),
            
            # System notifications
            "system_maintenance": NotificationTemplate(
                title="Scheduled Maintenance",
                message="System will be under maintenance from {start_time} to {end_time}.",
                type=NotificationType.WARNING,
                category=NotificationCategory.SYSTEM,
                icon="wrench",
                action_url=None
            ),
            "system_update": NotificationTemplate(
                title="System Update Available",
                message="New features and improvements have been added to CodeTrack Pro!",
                type=NotificationType.INFO,
                category=NotificationCategory.SYSTEM,
                icon="download",
                action_url="/about"
            ),
            "profile_sync_complete": NotificationTemplate(
                title="Profile Sync Complete",
                message="Your {platform} profile has been successfully synchronized.",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.SYSTEM,
                icon="sync",
                action_url="/coding"
            ),
            
            # Achievement notifications
            "streak_milestone": NotificationTemplate(
                title="Streak Milestone!",
                message="Congratulations! You've maintained a {days}-day coding streak!",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.ACHIEVEMENT,
                icon="fire",
                action_url="/dashboard"
            ),
            "problems_milestone": NotificationTemplate(
                title="Problem Solving Milestone!",
                message="Amazing! You've solved {count} problems on {platform}!",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.ACHIEVEMENT,
                icon="medal",
                action_url="/coding"
            ),
            "contest_rank_achievement": NotificationTemplate(
                title="Great Contest Performance!",
                message="You ranked #{rank} in contest '{contest_title}'!",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.ACHIEVEMENT,
                icon="trophy",
                action_url="/contest/{contest_id}/leaderboard"
            )
        }
        
        return templates
    
    def create_notification(self, template_key: str, user_id: int, 
                          context: Optional[Dict[str, Any]] = None,
                          contest_id: Optional[int] = None,
                          forum_post_id: Optional[int] = None,
                          study_group_id: Optional[int] = None) -> bool:
        """Create a notification using a template"""
        
        try:
            if template_key not in self.templates:
                logger.error(f"Unknown notification template: {template_key}")
                return False
            
            template = self.templates[template_key]
            context = context or {}
            
            # Format message with context
            title = template.title.format(**context)
            message = template.message.format(**context)
            
            # Create action URL if specified
            action_url = None
            if template.action_url:
                action_url = template.action_url.format(
                    contest_id=contest_id,
                    question_id=forum_post_id,
                    group_id=study_group_id,
                    **context
                )
            
            # Save to database
            from models import Notification, db
            
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=template.type.value,
                category=template.category.value,
                contest_id=contest_id,
                forum_post_id=forum_post_id,
                study_group_id=study_group_id
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"Created notification for user {user_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return False
    
    def create_custom_notification(self, user_id: int, title: str, message: str,
                                 notification_type: str = "info", 
                                 category: str = "system",
                                 contest_id: Optional[int] = None,
                                 forum_post_id: Optional[int] = None,
                                 study_group_id: Optional[int] = None) -> bool:
        """Create a custom notification"""
        
        try:
            from models import Notification, db
            
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                category=category,
                contest_id=contest_id,
                forum_post_id=forum_post_id,
                study_group_id=study_group_id
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"Created custom notification for user {user_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom notification: {e}")
            return False
    
    def get_user_notifications(self, user_id: int, limit: int = 50, 
                             unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        
        try:
            from models import Notification
            
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "type": n.type,
                    "category": n.category,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                    "contest_id": n.contest_id,
                    "forum_post_id": n.forum_post_id,
                    "study_group_id": n.study_group_id
                }
                for n in notifications
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        
        try:
            from models import Notification, db
            
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if not notification:
                return False
            
            notification.is_read = True
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    def mark_all_notifications_read(self, user_id: int) -> bool:
        """Mark all notifications as read for a user"""
        
        try:
            from models import Notification, db
            
            Notification.query.filter_by(user_id=user_id, is_read=False).update(
                {"is_read": True}
            )
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")
            return False
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        
        try:
            from models import Notification
            
            count = Notification.query.filter_by(
                user_id=user_id, 
                is_read=False
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0
    
    def delete_old_notifications(self, days_old: int = 30) -> int:
        """Delete notifications older than specified days"""
        
        try:
            from models import Notification, db
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_notifications = Notification.query.filter(
                Notification.created_at < cutoff_date
            ).all()
            
            count = len(old_notifications)
            
            for notification in old_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            
            logger.info(f"Deleted {count} old notifications")
            return count
            
        except Exception as e:
            logger.error(f"Failed to delete old notifications: {e}")
            return 0
    
    def create_bulk_notifications(self, template_key: str, user_ids: List[int],
                                context: Optional[Dict[str, Any]] = None) -> int:
        """Create notifications for multiple users"""
        
        success_count = 0
        
        for user_id in user_ids:
            if self.create_notification(template_key, user_id, context):
                success_count += 1
        
        logger.info(f"Created {success_count}/{len(user_ids)} bulk notifications")
        return success_count
    
    def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        
        try:
            from models import Notification
            
            total_notifications = Notification.query.count()
            unread_notifications = Notification.query.filter_by(is_read=False).count()
            
            # Notifications by category
            categories = {}
            for category in NotificationCategory:
                count = Notification.query.filter_by(category=category.value).count()
                categories[category.value] = count
            
            # Notifications by type
            types = {}
            for notification_type in NotificationType:
                count = Notification.query.filter_by(type=notification_type.value).count()
                types[notification_type.value] = count
            
            return {
                "total_notifications": total_notifications,
                "unread_notifications": unread_notifications,
                "categories": categories,
                "types": types,
                "read_rate": ((total_notifications - unread_notifications) / total_notifications * 100) 
                           if total_notifications > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification statistics: {e}")
            return {}

# Global instance
notification_service = NotificationService()
