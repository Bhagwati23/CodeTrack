"""
AI Flashcard Generator Service for CodeTrack Pro
Generates flashcards using AI providers with topic-based categorization
"""

import logging
from typing import List, Dict, Optional, Any
from services.ai_providers import ai_provider

logger = logging.getLogger(__name__)

class AIFlashcardGenerator:
    """AI-powered flashcard generation service"""
    
    def __init__(self):
        self.topic_templates = {
            'algorithms': {
                'prompt_template': """
                Generate {count} flashcards about {topic} algorithms for {difficulty} level programmers.
                
                Each flashcard should have:
                - A clear, specific question
                - A detailed answer with examples
                - Relevant complexity information when applicable
                
                Topics to cover: {subtopics}
                
                Return as JSON array:
                [
                    {{
                        "question": "What is the time complexity of...",
                        "answer": "The time complexity is O(n)...",
                        "category": "algorithms",
                        "difficulty": "{difficulty}",
                        "subtopic": "sorting"
                    }}
                ]
                """,
                'subtopics': [
                    'sorting algorithms', 'searching algorithms', 'graph algorithms',
                    'dynamic programming', 'greedy algorithms', 'divide and conquer'
                ]
            },
            'data_structures': {
                'prompt_template': """
                Generate {count} flashcards about {topic} data structures for {difficulty} level programmers.
                
                Each flashcard should cover:
                - Structure definition and purpose
                - Time/space complexity of operations
                - When to use each structure
                - Implementation details
                
                Topics to cover: {subtopics}
                
                Return as JSON array:
                [
                    {{
                        "question": "What is the main advantage of...",
                        "answer": "The main advantage is...",
                        "category": "data_structures",
                        "difficulty": "{difficulty}",
                        "subtopic": "arrays"
                    }}
                ]
                """,
                'subtopics': [
                    'arrays', 'linked lists', 'stacks', 'queues', 'trees', 'graphs',
                    'hash tables', 'heaps', 'tries'
                ]
            },
            'programming_concepts': {
                'prompt_template': """
                Generate {count} flashcards about {topic} programming concepts for {difficulty} level programmers.
                
                Each flashcard should explain:
                - Core concepts and definitions
                - Practical applications
                - Common pitfalls and best practices
                
                Topics to cover: {subtopics}
                
                Return as JSON array:
                [
                    {{
                        "question": "What is the difference between...",
                        "answer": "The key difference is...",
                        "category": "programming_concepts",
                        "difficulty": "{difficulty}",
                        "subtopic": "oop"
                    }}
                ]
                """,
                'subtopics': [
                    'object-oriented programming', 'functional programming', 'recursion',
                    'memory management', 'concurrency', 'design patterns'
                ]
            },
            'system_design': {
                'prompt_template': """
                Generate {count} flashcards about {topic} system design for {difficulty} level programmers.
                
                Each flashcard should cover:
                - Design principles and patterns
                - Scalability considerations
                - Real-world examples
                
                Topics to cover: {subtopics}
                
                Return as JSON array:
                [
                    {{
                        "question": "How would you design a system to...",
                        "answer": "The system would include...",
                        "category": "system_design",
                        "difficulty": "{difficulty}",
                        "subtopic": "load_balancing"
                    }}
                ]
                """,
                'subtopics': [
                    'load balancing', 'caching strategies', 'database design',
                    'microservices', 'distributed systems', 'security'
                ]
            },
            'interview_preparation': {
                'prompt_template': """
                Generate {count} flashcards for {topic} interview preparation at {difficulty} level.
                
                Each flashcard should prepare for:
                - Common interview questions
                - Problem-solving approaches
                - Technical explanations
                
                Topics to cover: {subtopics}
                
                Return as JSON array:
                [
                    {{
                        "question": "How would you approach this problem...",
                        "answer": "I would start by...",
                        "category": "interview_preparation",
                        "difficulty": "{difficulty}",
                        "subtopic": "problem_solving"
                    }}
                ]
                """,
                'subtopics': [
                    'problem solving', 'coding challenges', 'system design',
                    'behavioral questions', 'technical discussions'
                ]
            }
        }
    
    def generate_flashcards(self, topic: str, difficulty: str = 'medium', 
                          count: int = 5, subtopic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate flashcards for a specific topic and difficulty"""
        
        try:
            # Determine the topic category
            topic_category = self._categorize_topic(topic)
            
            if topic_category not in self.topic_templates:
                logger.warning(f"Unknown topic category: {topic_category}")
                return self._generate_generic_flashcards(topic, difficulty, count)
            
            # Get template and subtopics
            template_config = self.topic_templates[topic_category]
            subtopics = [subtopic] if subtopic else template_config['subtopics']
            
            # Build the prompt
            prompt = template_config['prompt_template'].format(
                count=count,
                topic=topic,
                difficulty=difficulty,
                subtopics=', '.join(subtopics[:3])  # Limit to first 3 subtopics
            )
            
            # Generate flashcards using AI
            response = ai_provider.generate_response(prompt)
            
            if 'error' in response:
                logger.error(f"AI generation failed: {response['error']}")
                return self._generate_fallback_flashcards(topic, difficulty, count)
            
            # Parse the response
            flashcards = self._parse_ai_response(response['content'])
            
            # Validate and enhance flashcards
            validated_flashcards = []
            for card in flashcards[:count]:
                validated_card = self._validate_flashcard(card, topic_category, difficulty)
                if validated_card:
                    validated_flashcards.append(validated_card)
            
            # Fill remaining slots with fallback cards if needed
            while len(validated_flashcards) < count:
                fallback_card = self._generate_single_fallback_card(
                    topic, difficulty, topic_category
                )
                if fallback_card:
                    validated_flashcards.append(fallback_card)
            
            logger.info(f"Generated {len(validated_flashcards)} flashcards for topic: {topic}")
            return validated_flashcards
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            return self._generate_fallback_flashcards(topic, difficulty, count)
    
    def generate_flashcards_from_text(self, text: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate flashcards from a given text or article"""
        
        try:
            prompt = f"""
            Analyze the following text and generate {count} flashcards that test understanding of the key concepts:
            
            Text: {text}
            
            Each flashcard should:
            - Test comprehension of important concepts
            - Have clear, specific questions
            - Provide detailed, accurate answers
            - Include relevant examples when applicable
            
            Return as JSON array:
            [
                {{
                    "question": "Based on the text, what is...",
                    "answer": "According to the text...",
                    "category": "text_analysis",
                    "difficulty": "medium",
                    "subtopic": "key_concept"
                }}
            ]
            """
            
            response = ai_provider.generate_response(prompt)
            
            if 'error' in response:
                logger.error(f"Text-based generation failed: {response['error']}")
                return []
            
            flashcards = self._parse_ai_response(response['content'])
            
            # Validate flashcards
            validated_flashcards = []
            for card in flashcards:
                validated_card = self._validate_flashcard(card, 'text_analysis', 'medium')
                if validated_card:
                    validated_flashcards.append(validated_card)
            
            return validated_flashcards[:count]
            
        except Exception as e:
            logger.error(f"Error generating flashcards from text: {e}")
            return []
    
    def generate_flashcards_from_problem(self, problem_title: str, problem_description: str,
                                       solution_approach: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate flashcards from a coding problem and its solution"""
        
        try:
            prompt = f"""
            Based on this coding problem, generate {count} flashcards to help understand the solution approach:
            
            Problem: {problem_title}
            Description: {problem_description}
            Solution Approach: {solution_approach}
            
            Create flashcards that test:
            - Understanding of the problem
            - Key concepts and algorithms used
            - Time and space complexity
            - Edge cases and considerations
            
            Return as JSON array:
            [
                {{
                    "question": "What is the main challenge in this problem?",
                    "answer": "The main challenge is...",
                    "category": "problem_analysis",
                    "difficulty": "medium",
                    "subtopic": "problem_understanding"
                }}
            ]
            """
            
            response = ai_provider.generate_response(prompt)
            
            if 'error' in response:
                logger.error(f"Problem-based generation failed: {response['error']}")
                return []
            
            flashcards = self._parse_ai_response(response['content'])
            
            # Validate flashcards
            validated_flashcards = []
            for card in flashcards:
                validated_card = self._validate_flashcard(card, 'problem_analysis', 'medium')
                if validated_card:
                    validated_flashcards.append(validated_card)
            
            return validated_flashcards[:count]
            
        except Exception as e:
            logger.error(f"Error generating flashcards from problem: {e}")
            return []
    
    def _categorize_topic(self, topic: str) -> str:
        """Categorize a topic into predefined categories"""
        
        topic_lower = topic.lower()
        
        # Algorithm-related keywords
        if any(keyword in topic_lower for keyword in [
            'algorithm', 'sorting', 'searching', 'graph', 'tree', 'dp', 'dynamic programming',
            'greedy', 'divide', 'conquer', 'recursion'
        ]):
            return 'algorithms'
        
        # Data structure keywords
        elif any(keyword in topic_lower for keyword in [
            'data structure', 'array', 'linked list', 'stack', 'queue', 'heap',
            'hash', 'map', 'set', 'tree', 'graph', 'trie'
        ]):
            return 'data_structures'
        
        # System design keywords
        elif any(keyword in topic_lower for keyword in [
            'system design', 'scalability', 'load balancing', 'caching', 'database',
            'microservice', 'distributed', 'architecture'
        ]):
            return 'system_design'
        
        # Interview preparation keywords
        elif any(keyword in topic_lower for keyword in [
            'interview', 'preparation', 'coding interview', 'technical interview'
        ]):
            return 'interview_preparation'
        
        # Default to programming concepts
        else:
            return 'programming_concepts'
    
    def _parse_ai_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse AI response and extract flashcards"""
        
        import json
        
        try:
            # Try to parse as JSON directly
            if content.strip().startswith('['):
                return json.loads(content)
            
            # Look for JSON array in the content
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # If no JSON found, try to extract individual cards
            return self._extract_cards_from_text(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return self._extract_cards_from_text(content)
    
    def _extract_cards_from_text(self, content: str) -> List[Dict[str, Any]]:
        """Extract flashcards from plain text response"""
        
        cards = []
        lines = content.split('\n')
        
        current_card = {}
        for line in lines:
            line = line.strip()
            
            if line.startswith('Question:') or line.startswith('Q:'):
                if current_card:
                    cards.append(current_card)
                current_card = {
                    'question': line.split(':', 1)[1].strip(),
                    'category': 'general',
                    'difficulty': 'medium'
                }
            elif line.startswith('Answer:') or line.startswith('A:'):
                if current_card:
                    current_card['answer'] = line.split(':', 1)[1].strip()
            elif line.startswith('Category:'):
                if current_card:
                    current_card['category'] = line.split(':', 1)[1].strip()
            elif line.startswith('Difficulty:'):
                if current_card:
                    current_card['difficulty'] = line.split(':', 1)[1].strip()
        
        # Add the last card if exists
        if current_card and 'answer' in current_card:
            cards.append(current_card)
        
        return cards
    
    def _validate_flashcard(self, card: Dict[str, Any], default_category: str, 
                          default_difficulty: str) -> Optional[Dict[str, Any]]:
        """Validate and enhance a flashcard"""
        
        # Check required fields
        if not card.get('question') or not card.get('answer'):
            return None
        
        # Clean and validate question
        question = str(card['question']).strip()
        if len(question) < 10 or len(question) > 500:
            return None
        
        # Clean and validate answer
        answer = str(card['answer']).strip()
        if len(answer) < 10 or len(answer) > 1000:
            return None
        
        # Set defaults for optional fields
        validated_card = {
            'question': question,
            'answer': answer,
            'category': card.get('category', default_category),
            'difficulty': card.get('difficulty', default_difficulty),
            'subtopic': card.get('subtopic', 'general'),
            'is_ai_generated': True
        }
        
        return validated_card
    
    def _generate_generic_flashcards(self, topic: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
        """Generate generic flashcards when topic category is unknown"""
        
        generic_prompt = f"""
        Generate {count} educational flashcards about {topic} for {difficulty} level learners.
        
        Each flashcard should have:
        - A clear, specific question
        - A detailed answer
        - Appropriate difficulty level
        
        Return as JSON array with question, answer, category, and difficulty fields.
        """
        
        try:
            response = ai_provider.generate_response(generic_prompt)
            if 'error' not in response:
                return self._parse_ai_response(response['content'])
        except Exception as e:
            logger.error(f"Generic flashcard generation failed: {e}")
        
        return self._generate_fallback_flashcards(topic, difficulty, count)
    
    def _generate_fallback_flashcards(self, topic: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
        """Generate fallback flashcards when AI generation fails"""
        
        fallback_cards = [
            {
                'question': f'What are the key concepts in {topic}?',
                'answer': f'The key concepts in {topic} include fundamental principles, best practices, and common applications. Understanding these concepts is essential for mastering {topic}.',
                'category': 'general',
                'difficulty': difficulty,
                'subtopic': 'concepts',
                'is_ai_generated': True
            },
            {
                'question': f'How would you explain {topic} to a beginner?',
                'answer': f'{topic} can be explained as a fundamental concept in computer science that involves specific principles and applications. It is important to understand the basics before moving to advanced topics.',
                'category': 'general',
                'difficulty': difficulty,
                'subtopic': 'explanation',
                'is_ai_generated': True
            },
            {
                'question': f'What are some practical applications of {topic}?',
                'answer': f'Practical applications of {topic} include real-world scenarios where these concepts are used to solve problems efficiently and effectively.',
                'category': 'general',
                'difficulty': difficulty,
                'subtopic': 'applications',
                'is_ai_generated': True
            }
        ]
        
        return fallback_cards[:count]
    
    def _generate_single_fallback_card(self, topic: str, difficulty: str, category: str) -> Dict[str, Any]:
        """Generate a single fallback flashcard"""
        
        return {
            'question': f'What is the importance of understanding {topic}?',
            'answer': f'Understanding {topic} is important because it provides fundamental knowledge that can be applied to solve complex problems and build efficient solutions.',
            'category': category,
            'difficulty': difficulty,
            'subtopic': 'importance',
            'is_ai_generated': True
        }

# Global instance
ai_flashcard_generator = AIFlashcardGenerator()
