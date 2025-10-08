"""
Spaced Repetition Learning System for CodeTrack Pro
Implements SM-2 algorithm for optimal flashcard review scheduling
"""

import math
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QualityRating(Enum):
    """Quality ratings for SM-2 algorithm"""
    AGAIN = 0  # Complete blackout - wrong response
    HARD = 1   # Incorrect response; correct one remembered
    GOOD = 2   # Correct response after hesitation
    EASY = 3   # Perfect response
    PERFECT = 4  # Instant recall

@dataclass
class ReviewResult:
    """Result of a flashcard review"""
    card_id: int
    quality: int
    previous_interval: int
    new_interval: int
    previous_ease_factor: float
    new_ease_factor: float
    repetitions: int
    next_review: datetime
    review_count: int

class SM2Algorithm:
    """Implementation of SM-2 spaced repetition algorithm"""
    
    def __init__(self):
        # SM-2 algorithm constants
        self.min_ease_factor = 1.3
        self.max_ease_factor = 4.0
        self.default_ease_factor = 2.5
        self.default_interval = 1
        self.minimum_interval = 1
        
        # Quality thresholds
        self.quality_thresholds = {
            QualityRating.AGAIN: 0,
            QualityRating.HARD: 1,
            QualityRating.GOOD: 2,
            QualityRating.EASY: 3,
            QualityRating.PERFECT: 4
        }
    
    def calculate_next_review(self, card_data: Dict[str, Any], quality: int) -> ReviewResult:
        """Calculate next review date and update card parameters using SM-2 algorithm"""
        
        # Extract current card parameters
        ease_factor = card_data.get('ease_factor', self.default_ease_factor)
        interval = card_data.get('interval', self.default_interval)
        repetitions = card_data.get('repetition_count', 0)
        review_count = card_data.get('review_count', 0)
        
        # Validate quality rating
        if quality < 0 or quality > 4:
            quality = 0  # Default to lowest quality
        
        # SM-2 Algorithm implementation
        if quality < 3:  # Quality rating below 3 (Good)
            # Failed recall - reset repetitions
            repetitions = 0
            interval = 1
        else:
            # Successful recall
            repetitions += 1
            
            if repetitions == 1:
                interval = 1
            elif repetitions == 2:
                interval = 6
            else:
                # Calculate new interval based on ease factor
                interval = int(interval * ease_factor)
        
        # Update ease factor
        new_ease_factor = self._update_ease_factor(ease_factor, quality)
        
        # Calculate next review date
        next_review = datetime.now() + timedelta(days=interval)
        
        return ReviewResult(
            card_id=card_data.get('id', 0),
            quality=quality,
            previous_interval=card_data.get('interval', 1),
            new_interval=interval,
            previous_ease_factor=ease_factor,
            new_ease_factor=new_ease_factor,
            repetitions=repetitions,
            next_review=next_review,
            review_count=review_count + 1
        )
    
    def _update_ease_factor(self, current_ease_factor: float, quality: int) -> float:
        """Update ease factor based on quality rating"""
        
        # SM-2 ease factor formula
        new_ease_factor = current_ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Ensure ease factor stays within bounds
        new_ease_factor = max(self.min_ease_factor, min(self.max_ease_factor, new_ease_factor))
        
        return round(new_ease_factor, 2)
    
    def get_interval_progression(self, ease_factor: float, max_repetitions: int = 10) -> List[int]:
        """Get the interval progression for a given ease factor"""
        
        intervals = []
        current_interval = 1
        
        for i in range(max_repetitions):
            intervals.append(current_interval)
            
            if i == 0:
                current_interval = 1
            elif i == 1:
                current_interval = 6
            else:
                current_interval = int(current_interval * ease_factor)
        
        return intervals

class SpacedRepetitionManager:
    """Manager for spaced repetition learning system"""
    
    def __init__(self):
        self.sm2 = SM2Algorithm()
        self.review_sessions: Dict[str, Dict[str, Any]] = {}
    
    def start_review_session(self, user_id: int, category: Optional[str] = None,
                           max_cards: int = 20) -> Dict[str, Any]:
        """Start a new review session for a user"""
        
        session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Import here to avoid circular imports
            from models import Flashcard
            
            # Get cards due for review
            due_cards = self._get_due_cards(user_id, category, max_cards)
            
            if not due_cards:
                return {
                    "session_id": session_id,
                    "cards": [],
                    "message": "No cards due for review right now!",
                    "total_due": 0
                }
            
            # Create session
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": datetime.now(),
                "cards": due_cards,
                "current_card_index": 0,
                "reviewed_cards": [],
                "category": category,
                "max_cards": max_cards
            }
            
            self.review_sessions[session_id] = session_data
            
            logger.info(f"Started review session {session_id} with {len(due_cards)} cards")
            
            return {
                "session_id": session_id,
                "cards": due_cards,
                "total_cards": len(due_cards),
                "current_card": 0,
                "category": category
            }
            
        except Exception as e:
            logger.error(f"Failed to start review session: {e}")
            return {"error": str(e)}
    
    def review_card(self, session_id: str, quality: int) -> Dict[str, Any]:
        """Review a card and get the next card in the session"""
        
        if session_id not in self.review_sessions:
            return {"error": "Session not found"}
        
        session = self.review_sessions[session_id]
        
        if session["current_card_index"] >= len(session["cards"]):
            return {"error": "No more cards in session"}
        
        try:
            # Get current card
            current_card = session["cards"][session["current_card_index"]]
            
            # Calculate next review using SM-2 algorithm
            review_result = self.sm2.calculate_next_review(current_card, quality)
            
            # Update card in database
            self._update_card_in_database(review_result)
            
            # Record review in session
            session["reviewed_cards"].append({
                "card_id": current_card["id"],
                "quality": quality,
                "review_time": datetime.now(),
                "new_interval": review_result.new_interval,
                "new_ease_factor": review_result.new_ease_factor
            })
            
            # Move to next card
            session["current_card_index"] += 1
            
            # Check if session is complete
            if session["current_card_index"] >= len(session["cards"]):
                return self._complete_session(session_id)
            
            # Return next card
            next_card = session["cards"][session["current_card_index"]]
            
            return {
                "status": "continue",
                "current_card": next_card,
                "progress": {
                    "completed": session["current_card_index"],
                    "total": len(session["cards"]),
                    "remaining": len(session["cards"]) - session["current_card_index"]
                },
                "review_result": {
                    "quality": quality,
                    "new_interval": review_result.new_interval,
                    "new_ease_factor": review_result.new_ease_factor,
                    "next_review": review_result.next_review.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to review card: {e}")
            return {"error": str(e)}
    
    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """Get progress of a review session"""
        
        if session_id not in self.review_sessions:
            return {"error": "Session not found"}
        
        session = self.review_sessions[session_id]
        
        return {
            "session_id": session_id,
            "progress": {
                "completed": session["current_card_index"],
                "total": len(session["cards"]),
                "remaining": len(session["cards"]) - session["current_card_index"]
            },
            "start_time": session["start_time"].isoformat(),
            "duration_minutes": (datetime.now() - session["start_time"]).total_seconds() / 60,
            "category": session.get("category")
        }
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get spaced repetition statistics for a user"""
        
        try:
            from models import Flashcard
            
            # Get all user's flashcards
            user_cards = Flashcard.query.filter_by(user_id=user_id).all()
            
            if not user_cards:
                return {"message": "No flashcards found for user"}
            
            # Calculate statistics
            total_cards = len(user_cards)
            due_cards = len([card for card in user_cards if self._is_card_due(card)])
            
            # Average ease factor
            ease_factors = [card.ease_factor for card in user_cards if card.ease_factor]
            avg_ease_factor = sum(ease_factors) / len(ease_factors) if ease_factors else 2.5
            
            # Cards by category
            categories = {}
            for card in user_cards:
                cat = card.category or "Uncategorized"
                categories[cat] = categories.get(cat, 0) + 1
            
            # Cards by difficulty
            difficulties = {}
            for card in user_cards:
                diff = card.difficulty or "Medium"
                difficulties[diff] = difficulties.get(diff, 0) + 1
            
            # Recent review activity
            recent_reviews = len([
                card for card in user_cards 
                if card.last_reviewed and 
                (datetime.now() - card.last_reviewed).days <= 7
            ])
            
            return {
                "total_cards": total_cards,
                "due_cards": due_cards,
                "average_ease_factor": round(avg_ease_factor, 2),
                "categories": categories,
                "difficulties": difficulties,
                "recent_reviews_7_days": recent_reviews,
                "retention_rate": self._calculate_retention_rate(user_cards),
                "streak_days": self._calculate_review_streak(user_cards)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            return {"error": str(e)}
    
    def create_ai_flashcards(self, topic: str, difficulty: str, count: int = 5) -> List[Dict[str, str]]:
        """Create AI-generated flashcards for a topic"""
        
        try:
            from services.ai_providers import ai_provider
            
            flashcards = ai_provider.generate_flashcards(topic, difficulty)
            
            # Limit to requested count
            return flashcards[:count]
            
        except Exception as e:
            logger.error(f"Failed to create AI flashcards: {e}")
            return []
    
    def get_due_cards_count(self, user_id: int, category: Optional[str] = None) -> int:
        """Get count of cards due for review"""
        
        try:
            from models import Flashcard
            
            query = Flashcard.query.filter_by(user_id=user_id)
            
            if category:
                query = query.filter_by(category=category)
            
            all_cards = query.all()
            due_cards = [card for card in all_cards if self._is_card_due(card)]
            
            return len(due_cards)
            
        except Exception as e:
            logger.error(f"Failed to get due cards count: {e}")
            return 0
    
    def _get_due_cards(self, user_id: int, category: Optional[str] = None, 
                      max_cards: int = 20) -> List[Dict[str, Any]]:
        """Get cards due for review"""
        
        try:
            from models import Flashcard
            
            query = Flashcard.query.filter_by(user_id=user_id)
            
            if category:
                query = query.filter_by(category=category)
            
            all_cards = query.all()
            due_cards = []
            
            for card in all_cards:
                if self._is_card_due(card):
                    due_cards.append({
                        "id": card.id,
                        "topic": card.topic,
                        "question": card.question,
                        "answer": card.answer,
                        "category": card.category,
                        "difficulty": card.difficulty,
                        "ease_factor": card.ease_factor,
                        "interval": card.interval,
                        "repetition_count": card.repetition_count,
                        "review_count": card.review_count,
                        "is_ai_generated": card.is_ai_generated
                    })
            
            # Sort by priority (overdue cards first, then by ease factor)
            due_cards.sort(key=lambda x: (
                x.get('next_review', datetime.min) < datetime.now(),
                x.get('ease_factor', 2.5)
            ))
            
            return due_cards[:max_cards]
            
        except Exception as e:
            logger.error(f"Failed to get due cards: {e}")
            return []
    
    def _is_card_due(self, card) -> bool:
        """Check if a card is due for review"""
        
        if not card.next_review:
            return True  # New card
        
        return datetime.now() >= card.next_review
    
    def _update_card_in_database(self, review_result: ReviewResult):
        """Update card in database with review results"""
        
        try:
            from models import Flashcard, db
            
            card = Flashcard.query.get(review_result.card_id)
            if not card:
                logger.error(f"Card {review_result.card_id} not found")
                return
            
            # Update card parameters
            card.ease_factor = review_result.new_ease_factor
            card.interval = review_result.new_interval
            card.repetition_count = review_result.repetitions
            card.review_count = review_result.review_count
            card.last_reviewed = datetime.now()
            card.next_review = review_result.next_review
            
            db.session.commit()
            
            logger.info(f"Updated card {review_result.card_id} with new interval {review_result.new_interval}")
            
        except Exception as e:
            logger.error(f"Failed to update card in database: {e}")
    
    def _complete_session(self, session_id: str) -> Dict[str, Any]:
        """Complete a review session and return summary"""
        
        session = self.review_sessions[session_id]
        
        # Calculate session statistics
        total_cards = len(session["reviewed_cards"])
        quality_scores = [card["quality"] for card in session["reviewed_cards"]]
        avg_quality = sum(quality_scores) / total_cards if total_cards > 0 else 0
        
        # Calculate session duration
        duration_minutes = (datetime.now() - session["start_time"]).total_seconds() / 60
        
        # Remove session from active sessions
        del self.review_sessions[session_id]
        
        logger.info(f"Completed review session {session_id}")
        
        return {
            "status": "completed",
            "session_id": session_id,
            "summary": {
                "total_cards_reviewed": total_cards,
                "average_quality": round(avg_quality, 2),
                "duration_minutes": round(duration_minutes, 1),
                "category": session.get("category"),
                "start_time": session["start_time"].isoformat(),
                "end_time": datetime.now().isoformat()
            },
            "quality_breakdown": {
                "again": quality_scores.count(0),
                "hard": quality_scores.count(1),
                "good": quality_scores.count(2),
                "easy": quality_scores.count(3),
                "perfect": quality_scores.count(4)
            }
        }
    
    def _calculate_retention_rate(self, cards) -> float:
        """Calculate retention rate based on ease factors"""
        
        if not cards:
            return 0.0
        
        # Cards with ease factor > 2.0 are considered "retained"
        retained_cards = len([card for card in cards if card.ease_factor > 2.0])
        total_cards = len(cards)
        
        return (retained_cards / total_cards) * 100 if total_cards > 0 else 0.0
    
    def _calculate_review_streak(self, cards) -> int:
        """Calculate current review streak in days"""
        
        if not cards:
            return 0
        
        # Find the most recent review date
        recent_reviews = [card.last_reviewed for card in cards if card.last_reviewed]
        if not recent_reviews:
            return 0
        
        most_recent = max(recent_reviews)
        current_date = datetime.now().date()
        
        # Calculate streak (simplified - would need more complex logic for actual streaks)
        days_since_last_review = (current_date - most_recent.date()).days
        
        return max(0, 7 - days_since_last_review)  # Simple approximation
    
    def cleanup_expired_sessions(self):
        """Clean up expired review sessions"""
        
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.review_sessions.items():
            # Sessions expire after 2 hours of inactivity
            if (current_time - session["start_time"]).total_seconds() > 7200:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.review_sessions[session_id]
            logger.info(f"Cleaned up expired review session {session_id}")
        
        return len(expired_sessions)

# Global instance
spaced_repetition_manager = SpacedRepetitionManager()
