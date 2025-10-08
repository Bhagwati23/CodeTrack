"""
Study Group Matching Algorithm for CodeTrack Pro
Matches users to appropriate study groups based on skill level, interests, and compatibility
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User profile for matching"""
    user_id: int
    skill_level: str  # beginner, intermediate, advanced
    interests: List[str]
    coding_hours_per_week: int
    preferred_schedule: str
    timezone: str
    platform_stats: Dict[str, Any]
    learning_goals: List[str]
    join_date: datetime

@dataclass
class StudyGroupProfile:
    """Study group profile for matching"""
    group_id: int
    name: str
    topic: str
    skill_level: str
    current_size: int
    max_size: int
    activity_level: float  # 0-1 scale
    member_skill_distribution: Dict[str, int]
    average_coding_hours: float
    preferred_schedule: str
    created_date: datetime

class StudyGroupMatcher:
    """Study group matching algorithm"""
    
    def __init__(self):
        self.skill_level_weights = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3
        }
        
        self.topic_similarity_matrix = {
            'algorithms': ['data_structures', 'problem_solving', 'competitive_programming'],
            'data_structures': ['algorithms', 'problem_solving', 'interview_prep'],
            'system_design': ['architecture', 'scalability', 'distributed_systems'],
            'web_development': ['frontend', 'backend', 'full_stack'],
            'mobile_development': ['ios', 'android', 'react_native'],
            'machine_learning': ['ai', 'data_science', 'deep_learning'],
            'competitive_programming': ['algorithms', 'data_structures', 'problem_solving'],
            'interview_preparation': ['algorithms', 'data_structures', 'system_design']
        }
    
    def find_best_matches(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Find the best study group matches for a user"""
        
        try:
            # Get user profile
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                logger.error(f"Could not create user profile for user {user_id}")
                return []
            
            # Get available study groups
            available_groups = self._get_available_study_groups()
            
            # Calculate compatibility scores
            matches = []
            for group in available_groups:
                group_profile = self._get_group_profile(group)
                if not group_profile:
                    continue
                
                compatibility_score = self._calculate_compatibility(user_profile, group_profile)
                
                if compatibility_score > 0.3:  # Minimum compatibility threshold
                    matches.append({
                        'group_id': group_profile.group_id,
                        'group_name': group_profile.name,
                        'topic': group_profile.topic,
                        'skill_level': group_profile.skill_level,
                        'current_size': group_profile.current_size,
                        'max_size': group_profile.max_size,
                        'compatibility_score': compatibility_score,
                        'match_reasons': self._get_match_reasons(user_profile, group_profile),
                        'activity_level': group_profile.activity_level
                    })
            
            # Sort by compatibility score
            matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error finding study group matches: {e}")
            return []
    
    def create_optimal_group(self, user_id: int, topic: str, skill_level: str, 
                           max_members: int = 8) -> Optional[Dict[str, Any]]:
        """Create an optimal study group for a user"""
        
        try:
            # Get user profile
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                return None
            
            # Find compatible users for the group
            compatible_users = self._find_compatible_users(user_profile, topic, skill_level, max_members - 1)
            
            if len(compatible_users) < 2:  # Need at least 3 members total
                logger.info(f"Not enough compatible users found for group creation")
                return None
            
            # Create group with optimal settings
            group_data = {
                'name': f"{topic.title()} Study Group",
                'topic': topic,
                'skill_level': skill_level,
                'max_members': max_members,
                'description': f"A focused study group for {topic} at {skill_level} level",
                'created_by': user_id,
                'suggested_members': compatible_users[:max_members - 1]
            }
            
            return group_data
            
        except Exception as e:
            logger.error(f"Error creating optimal group: {e}")
            return None
    
    def _get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile for matching"""
        
        try:
            from models import User, PlatformStats
            
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Get platform statistics
            platform_stats = {}
            total_problems = 0
            for ps in user.platform_stats:
                platform_stats[ps.platform] = {
                    'total_problems': ps.total_problems,
                    'easy_solved': ps.easy_solved,
                    'medium_solved': ps.medium_solved,
                    'hard_solved': ps.hard_solved,
                    'streak': ps.streak
                }
                total_problems += ps.total_problems
            
            # Determine skill level based on problems solved
            skill_level = self._determine_skill_level(total_problems, platform_stats)
            
            # Extract interests from learning goals
            interests = self._extract_interests_from_goals(user.learning_goals or '')
            
            # Estimate coding hours per week (simplified)
            coding_hours_per_week = min(total_problems * 0.5, 40)  # Rough estimate
            
            return UserProfile(
                user_id=user_id,
                skill_level=skill_level,
                interests=interests,
                coding_hours_per_week=coding_hours_per_week,
                preferred_schedule=user.preferred_schedule or 'flexible',
                timezone='UTC',  # Simplified - would need timezone detection
                platform_stats=platform_stats,
                learning_goals=self._parse_learning_goals(user.learning_goals or ''),
                join_date=user.created_at
            )
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return None
    
    def _get_available_study_groups(self) -> List[Dict[str, Any]]:
        """Get available study groups"""
        
        try:
            from models import StudyGroup, StudyGroupMember
            
            # Get active groups with space
            groups = StudyGroup.query.filter_by(is_active=True).all()
            
            available_groups = []
            for group in groups:
                member_count = len(group.members)
                if member_count < group.max_members:
                    available_groups.append({
                        'id': group.id,
                        'name': group.name,
                        'topic': group.topic,
                        'skill_level': group.skill_level,
                        'current_size': member_count,
                        'max_size': group.max_members,
                        'created_by': group.created_by,
                        'created_at': group.created_at,
                        'members': group.members
                    })
            
            return available_groups
            
        except Exception as e:
            logger.error(f"Error getting available study groups: {e}")
            return []
    
    def _get_group_profile(self, group_data: Dict[str, Any]) -> Optional[StudyGroupProfile]:
        """Create study group profile for matching"""
        
        try:
            # Calculate member skill distribution
            member_skill_distribution = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
            total_coding_hours = 0
            member_count = len(group_data['members'])
            
            for member in group_data['members']:
                user_profile = self._get_user_profile(member.user_id)
                if user_profile:
                    member_skill_distribution[user_profile.skill_level] += 1
                    total_coding_hours += user_profile.coding_hours_per_week
            
            # Calculate activity level based on group age and member activity
            days_since_creation = (datetime.now() - group_data['created_at']).days
            activity_level = min(1.0, max(0.1, 1.0 - (days_since_creation / 365.0)))
            
            # Calculate average coding hours
            average_coding_hours = total_coding_hours / max(member_count, 1)
            
            return StudyGroupProfile(
                group_id=group_data['id'],
                name=group_data['name'],
                topic=group_data['topic'],
                skill_level=group_data['skill_level'],
                current_size=group_data['current_size'],
                max_size=group_data['max_size'],
                activity_level=activity_level,
                member_skill_distribution=member_skill_distribution,
                average_coding_hours=average_coding_hours,
                preferred_schedule='flexible',  # Simplified
                created_date=group_data['created_at']
            )
            
        except Exception as e:
            logger.error(f"Error creating group profile: {e}")
            return None
    
    def _calculate_compatibility(self, user_profile: UserProfile, 
                               group_profile: StudyGroupProfile) -> float:
        """Calculate compatibility score between user and study group"""
        
        try:
            scores = []
            
            # Skill level compatibility (40% weight)
            skill_score = self._calculate_skill_compatibility(
                user_profile.skill_level, 
                group_profile.skill_level,
                group_profile.member_skill_distribution
            )
            scores.append(('skill_level', skill_score, 0.4))
            
            # Interest compatibility (25% weight)
            interest_score = self._calculate_interest_compatibility(
                user_profile.interests,
                group_profile.topic
            )
            scores.append(('interests', interest_score, 0.25))
            
            # Schedule compatibility (15% weight)
            schedule_score = self._calculate_schedule_compatibility(
                user_profile.preferred_schedule,
                group_profile.preferred_schedule
            )
            scores.append(('schedule', schedule_score, 0.15))
            
            # Activity level compatibility (10% weight)
            activity_score = self._calculate_activity_compatibility(
                user_profile.coding_hours_per_week,
                group_profile.average_coding_hours
            )
            scores.append(('activity', activity_score, 0.1))
            
            # Group size preference (10% weight)
            size_score = self._calculate_size_compatibility(
                group_profile.current_size,
                group_profile.max_size
            )
            scores.append(('size', size_score, 0.1))
            
            # Calculate weighted average
            total_score = sum(score * weight for _, score, weight in scores)
            
            return min(1.0, max(0.0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")
            return 0.0
    
    def _calculate_skill_compatibility(self, user_skill: str, group_skill: str, 
                                     member_distribution: Dict[str, int]) -> float:
        """Calculate skill level compatibility"""
        
        # Exact match
        if user_skill == group_skill:
            return 1.0
        
        # Adjacent skill levels (e.g., beginner-intermediate)
        skill_levels = ['beginner', 'intermediate', 'advanced']
        user_index = skill_levels.index(user_skill)
        group_index = skill_levels.index(group_skill)
        
        if abs(user_index - group_index) == 1:
            return 0.7
        
        # Different skill levels
        if abs(user_index - group_index) == 2:
            return 0.3
        
        # Check member distribution for diversity bonus
        total_members = sum(member_distribution.values())
        if total_members > 0:
            user_skill_ratio = member_distribution.get(user_skill, 0) / total_members
            if user_skill_ratio < 0.5:  # Not over-represented
                return min(1.0, 0.8 + 0.2 * (1 - user_skill_ratio))
        
        return 0.5
    
    def _calculate_interest_compatibility(self, user_interests: List[str], group_topic: str) -> float:
        """Calculate interest compatibility"""
        
        if not user_interests:
            return 0.5
        
        # Direct match
        if group_topic.lower() in [interest.lower() for interest in user_interests]:
            return 1.0
        
        # Related topics
        related_topics = self.topic_similarity_matrix.get(group_topic.lower(), [])
        for interest in user_interests:
            if any(related in interest.lower() for related in related_topics):
                return 0.8
        
        # Partial match
        for interest in user_interests:
            if group_topic.lower() in interest.lower() or interest.lower() in group_topic.lower():
                return 0.6
        
        return 0.3
    
    def _calculate_schedule_compatibility(self, user_schedule: str, group_schedule: str) -> float:
        """Calculate schedule compatibility"""
        
        if user_schedule == 'flexible' or group_schedule == 'flexible':
            return 0.8
        
        if user_schedule == group_schedule:
            return 1.0
        
        # Similar schedules (e.g., morning-evening)
        schedule_groups = {
            'morning': ['morning', 'early_morning'],
            'afternoon': ['afternoon', 'lunch_time'],
            'evening': ['evening', 'night'],
            'weekend': ['weekend', 'saturday', 'sunday']
        }
        
        for group, schedules in schedule_groups.items():
            if user_schedule in schedules and group_schedule in schedules:
                return 0.7
        
        return 0.4
    
    def _calculate_activity_compatibility(self, user_hours: int, group_avg_hours: float) -> float:
        """Calculate activity level compatibility"""
        
        if group_avg_hours == 0:
            return 0.5
        
        # Calculate ratio
        ratio = user_hours / group_avg_hours
        
        # Ideal range is 0.7 to 1.5
        if 0.7 <= ratio <= 1.5:
            return 1.0
        elif 0.5 <= ratio <= 2.0:
            return 0.8
        elif 0.3 <= ratio <= 3.0:
            return 0.6
        else:
            return 0.3
    
    def _calculate_size_compatibility(self, current_size: int, max_size: int) -> float:
        """Calculate group size compatibility"""
        
        # Prefer groups that are not too empty or too full
        fill_ratio = current_size / max_size
        
        if 0.3 <= fill_ratio <= 0.7:  # Ideal range
            return 1.0
        elif 0.2 <= fill_ratio <= 0.8:  # Good range
            return 0.8
        elif 0.1 <= fill_ratio <= 0.9:  # Acceptable range
            return 0.6
        else:
            return 0.3
    
    def _determine_skill_level(self, total_problems: int, platform_stats: Dict[str, Any]) -> str:
        """Determine user skill level based on problems solved"""
        
        if total_problems >= 200:
            return 'advanced'
        elif total_problems >= 50:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _extract_interests_from_goals(self, learning_goals: str) -> List[str]:
        """Extract interests from learning goals text"""
        
        if not learning_goals:
            return []
        
        interests = []
        learning_goals_lower = learning_goals.lower()
        
        # Map keywords to interests
        keyword_mapping = {
            'algorithm': 'algorithms',
            'data structure': 'data_structures',
            'system design': 'system_design',
            'web development': 'web_development',
            'mobile': 'mobile_development',
            'machine learning': 'machine_learning',
            'ai': 'machine_learning',
            'competitive': 'competitive_programming',
            'interview': 'interview_preparation'
        }
        
        for keyword, interest in keyword_mapping.items():
            if keyword in learning_goals_lower:
                interests.append(interest)
        
        return interests
    
    def _parse_learning_goals(self, learning_goals: str) -> List[str]:
        """Parse learning goals into a list"""
        
        if not learning_goals:
            return []
        
        # Split by common delimiters
        goals = []
        for delimiter in [',', ';', '\n', '.']:
            if delimiter in learning_goals:
                goals = [goal.strip() for goal in learning_goals.split(delimiter) if goal.strip()]
                break
        
        if not goals:
            goals = [learning_goals.strip()]
        
        return goals
    
    def _find_compatible_users(self, user_profile: UserProfile, topic: str, 
                             skill_level: str, max_users: int) -> List[int]:
        """Find compatible users for group creation"""
        
        try:
            from models import User, StudyGroupMember
            
            # Get users not already in groups
            users_in_groups = db.session.query(StudyGroupMember.user_id).distinct().all()
            users_in_groups = [user_id[0] for user_id in users_in_groups]
            
            available_users = User.query.filter(
                User.id.notin_(users_in_groups),
                User.id != user_profile.user_id,
                User.role == 'student'
            ).all()
            
            # Calculate compatibility scores
            compatible_users = []
            for user in available_users:
                candidate_profile = self._get_user_profile(user.id)
                if not candidate_profile:
                    continue
                
                # Simple compatibility check
                if (candidate_profile.skill_level == skill_level and
                    any(topic.lower() in interest.lower() for interest in candidate_profile.interests)):
                    
                    compatible_users.append(user.id)
            
            return compatible_users[:max_users]
            
        except Exception as e:
            logger.error(f"Error finding compatible users: {e}")
            return []
    
    def _get_match_reasons(self, user_profile: UserProfile, 
                          group_profile: StudyGroupProfile) -> List[str]:
        """Get reasons why this group is a good match"""
        
        reasons = []
        
        # Skill level match
        if user_profile.skill_level == group_profile.skill_level:
            reasons.append(f"Same skill level ({user_profile.skill_level})")
        
        # Interest match
        if any(group_profile.topic.lower() in interest.lower() for interest in user_profile.interests):
            reasons.append(f"Interested in {group_profile.topic}")
        
        # Activity level
        if abs(user_profile.coding_hours_per_week - group_profile.average_coding_hours) <= 5:
            reasons.append("Similar activity level")
        
        # Group size
        if group_profile.current_size < group_profile.max_size * 0.7:
            reasons.append("Group has available spots")
        
        return reasons

# Global instance
study_group_matcher = StudyGroupMatcher()
