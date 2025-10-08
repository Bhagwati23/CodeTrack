"""
Enhanced AI Tutoring Service for CodeTrack Pro
Interactive chatbot with conversation history and context awareness
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from services.ai_providers import ai_provider

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """Represents a message in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    message_type: str = 'text'  # 'text', 'code', 'explanation', 'hint'
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TutoringSession:
    """Represents a tutoring session with context"""
    session_id: str
    user_id: int
    topic: Optional[str] = None
    difficulty_level: str = 'beginner'
    learning_goals: List[str] = None
    conversation_history: List[ConversationMessage] = None
    session_start: datetime = None
    last_activity: datetime = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.learning_goals is None:
            self.learning_goals = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.session_start is None:
            self.session_start = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.context is None:
            self.context = {}

class EnhancedAITutor:
    """Enhanced AI tutoring service with conversation management"""
    
    def __init__(self):
        self.active_sessions: Dict[str, TutoringSession] = {}
        self.session_timeout = timedelta(hours=2)  # Sessions expire after 2 hours
        
        # Predefined conversation starters and hints
        self.conversation_starters = [
            "I want to learn about data structures",
            "Help me understand algorithms",
            "I'm preparing for coding interviews",
            "Explain a programming concept",
            "Give me practice problems",
            "Help me debug my code",
            "Create a study plan for me"
        ]
        
        self.hints_and_tips = {
            'array': [
                "Think about the time complexity of your solution",
                "Consider using two pointers technique",
                "Hash maps can help optimize array problems"
            ],
            'linked_list': [
                "Use dummy nodes to simplify edge cases",
                "Consider the fast and slow pointer technique",
                "Be careful about updating pointers in the correct order"
            ],
            'tree': [
                "Think recursively for tree problems",
                "Consider both DFS and BFS approaches",
                "Use stack for iterative solutions"
            ],
            'dynamic_programming': [
                "Identify the subproblem first",
                "Think about the recurrence relation",
                "Consider space optimization techniques"
            ]
        }
    
    def start_session(self, user_id: int, topic: Optional[str] = None, 
                     difficulty_level: str = 'beginner') -> TutoringSession:
        """Start a new tutoring session"""
        session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = TutoringSession(
            session_id=session_id,
            user_id=user_id,
            topic=topic,
            difficulty_level=difficulty_level
        )
        
        self.active_sessions[session_id] = session
        
        # Add welcome message
        welcome_message = self._generate_welcome_message(topic, difficulty_level)
        self._add_message(session, 'assistant', welcome_message, 'text')
        
        logger.info(f"Started new tutoring session {session_id} for user {user_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[TutoringSession]:
        """Get an active session by ID"""
        session = self.active_sessions.get(session_id)
        if session and datetime.now() - session.last_activity < self.session_timeout:
            return session
        elif session:
            # Session expired
            del self.active_sessions[session_id]
        return None
    
    def send_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Send a message to the AI tutor and get response"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found or expired"}
        
        # Add user message to history
        self._add_message(session, 'user', user_message, 'text')
        
        # Generate AI response
        ai_response = self._generate_ai_response(session, user_message)
        
        # Add AI response to history
        self._add_message(session, 'assistant', ai_response['content'], 
                         ai_response.get('message_type', 'text'), ai_response.get('metadata'))
        
        # Update session activity
        session.last_activity = datetime.now()
        
        return {
            "response": ai_response['content'],
            "message_type": ai_response.get('message_type', 'text'),
            "metadata": ai_response.get('metadata'),
            "session_id": session_id,
            "conversation_length": len(session.conversation_history)
        }
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "message_type": msg.message_type,
                "metadata": msg.metadata
            }
            for msg in session.conversation_history
        ]
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a tutoring session and return summary"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Generate session summary
        summary = self._generate_session_summary(session)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        logger.info(f"Ended tutoring session {session_id}")
        
        return {
            "session_id": session_id,
            "duration": (datetime.now() - session.session_start).total_seconds(),
            "messages_exchanged": len(session.conversation_history),
            "summary": summary
        }
    
    def get_suggested_topics(self, user_level: str) -> List[Dict[str, str]]:
        """Get suggested topics based on user level"""
        topics_by_level = {
            'beginner': [
                {"topic": "Variables and Data Types", "description": "Learn about different data types"},
                {"topic": "Control Structures", "description": "If statements, loops, and conditions"},
                {"topic": "Functions", "description": "How to create and use functions"},
                {"topic": "Arrays Basics", "description": "Introduction to arrays and basic operations"}
            ],
            'intermediate': [
                {"topic": "Data Structures", "description": "Stacks, queues, linked lists"},
                {"topic": "Sorting Algorithms", "description": "Bubble sort, merge sort, quick sort"},
                {"topic": "Searching Algorithms", "description": "Linear search, binary search"},
                {"topic": "String Manipulation", "description": "Advanced string operations"}
            ],
            'advanced': [
                {"topic": "Dynamic Programming", "description": "Memoization and tabulation"},
                {"topic": "Graph Algorithms", "description": "DFS, BFS, shortest paths"},
                {"topic": "Tree Algorithms", "description": "BST operations, traversals"},
                {"topic": "System Design", "description": "Designing scalable systems"}
            ]
        }
        
        return topics_by_level.get(user_level, topics_by_level['beginner'])
    
    def get_hints(self, topic: str) -> List[str]:
        """Get hints for a specific topic"""
        topic_lower = topic.lower()
        
        # Find matching hints
        hints = []
        for key, topic_hints in self.hints_and_tips.items():
            if key in topic_lower:
                hints.extend(topic_hints)
        
        # Add general hints if no specific ones found
        if not hints:
            hints = [
                "Break the problem down into smaller parts",
                "Think about edge cases",
                "Consider the time and space complexity",
                "Try to solve it step by step"
            ]
        
        return hints[:3]  # Return top 3 hints
    
    def _add_message(self, session: TutoringSession, role: str, content: str, 
                    message_type: str = 'text', metadata: Optional[Dict] = None):
        """Add a message to the conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            metadata=metadata
        )
        session.conversation_history.append(message)
    
    def _generate_welcome_message(self, topic: Optional[str], difficulty_level: str) -> str:
        """Generate a personalized welcome message"""
        if topic:
            return f"""Hello! I'm your AI coding tutor. I see you want to learn about **{topic}** at the **{difficulty_level}** level. 

I'm here to help you understand concepts, solve problems, and improve your coding skills. You can:
- Ask me to explain any programming concept
- Request practice problems
- Get hints when you're stuck
- Review your code and get feedback
- Create a personalized study plan

What would you like to start with?"""
        else:
            return f"""Hello! I'm your AI coding tutor. I'm here to help you learn programming and improve your coding skills.

You can ask me about:
- **Data structures** (arrays, linked lists, trees, graphs)
- **Algorithms** (sorting, searching, dynamic programming)
- **Problem-solving techniques** and strategies
- **Code review** and debugging help
- **Interview preparation** and practice problems
- **Study plans** tailored to your goals

What would you like to learn about today?"""
    
    def _generate_ai_response(self, session: TutoringSession, user_message: str) -> Dict[str, Any]:
        """Generate AI response based on conversation context"""
        # Build context-aware prompt
        context_prompt = self._build_context_prompt(session, user_message)
        
        # Get response from AI provider
        response = ai_provider.generate_response(context_prompt)
        
        if "error" in response:
            return {
                "content": "I'm having trouble connecting right now. Please try again in a moment.",
                "message_type": "text",
                "metadata": {"error": response["error"]}
            }
        
        # Analyze response to determine message type and metadata
        content = response["content"]
        message_type = "text"
        metadata = {"provider": response.get("provider", "Unknown")}
        
        # Detect code in response
        if "```" in content:
            message_type = "code_explanation"
            metadata["has_code"] = True
        
        # Detect if it's a hint
        if any(keyword in content.lower() for keyword in ["hint:", "tip:", "try this:", "consider:"]):
            message_type = "hint"
            metadata["is_hint"] = True
        
        # Detect if it's asking for clarification
        if content.endswith("?") or "what" in content.lower()[:10]:
            message_type = "question"
            metadata["is_question"] = True
        
        return {
            "content": content,
            "message_type": message_type,
            "metadata": metadata
        }
    
    def _build_context_prompt(self, session: TutoringSession, user_message: str) -> str:
        """Build a context-aware prompt for the AI"""
        prompt_parts = [
            "You are CodeTrack Pro AI Tutor, an expert programming instructor helping students learn coding.",
            f"Student level: {session.difficulty_level}",
            f"Current topic focus: {session.topic or 'General programming'}",
            f"Learning goals: {', '.join(session.learning_goals) if session.learning_goals else 'Not specified'}",
            "",
            "Conversation history:"
        ]
        
        # Add recent conversation history (last 6 messages)
        recent_messages = session.conversation_history[-6:] if len(session.conversation_history) > 6 else session.conversation_history
        
        for msg in recent_messages:
            role_name = "Student" if msg.role == "user" else "Tutor"
            prompt_parts.append(f"{role_name}: {msg.content}")
        
        prompt_parts.extend([
            "",
            f"Current student message: {user_message}",
            "",
            "Instructions:",
            "- Provide clear, educational explanations",
            "- Give practical examples when helpful",
            "- Ask clarifying questions if needed",
            "- Offer hints rather than direct answers when appropriate",
            "- Encourage learning and problem-solving",
            "- Be encouraging and supportive",
            "- If the message contains code, provide constructive feedback",
            "- Keep responses concise but comprehensive"
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_session_summary(self, session: TutoringSession) -> Dict[str, Any]:
        """Generate a summary of the tutoring session"""
        user_messages = [msg for msg in session.conversation_history if msg.role == 'user']
        assistant_messages = [msg for msg in session.conversation_history if msg.role == 'assistant']
        
        # Extract topics discussed
        topics_discussed = set()
        for msg in session.conversation_history:
            content_lower = msg.content.lower()
            if 'array' in content_lower:
                topics_discussed.add('Arrays')
            if 'linked list' in content_lower:
                topics_discussed.add('Linked Lists')
            if 'tree' in content_lower:
                topics_discussed.add('Trees')
            if 'algorithm' in content_lower:
                topics_discussed.add('Algorithms')
            if 'dynamic programming' in content_lower or 'dp' in content_lower:
                topics_discussed.add('Dynamic Programming')
        
        return {
            "duration_minutes": round((datetime.now() - session.session_start).total_seconds() / 60, 1),
            "messages_exchanged": len(session.conversation_history),
            "topics_discussed": list(topics_discussed),
            "session_topic": session.topic,
            "difficulty_level": session.difficulty_level,
            "learning_progress": "Good engagement" if len(user_messages) > 3 else "Limited interaction"
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session.last_activity > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up expired session {session_id}")
        
        return len(expired_sessions)

# Global instance
ai_tutor = EnhancedAITutor()
