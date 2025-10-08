"""
Multi-Provider AI System for CodeTrack Pro
Supports OpenAI, DeepSeek, Gemini, OpenRouter, Hugging Face with automatic fallback
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class AIProviderBase:
    """Base class for AI providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.name = "Base"
        
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.api_key is not None
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response from AI provider"""
        raise NotImplementedError
    
    def generate_study_plan(self, user_goals: str, skill_level: str) -> Dict[str, Any]:
        """Generate personalized study plan"""
        raise NotImplementedError
    
    def generate_problem_recommendation(self, user_stats: Dict, weak_areas: List[str]) -> Dict[str, Any]:
        """Generate problem recommendations"""
        raise NotImplementedError
    
    def generate_flashcards(self, topic: str, difficulty: str) -> List[Dict[str, str]]:
        """Generate flashcards for a topic"""
        raise NotImplementedError

class OpenAIProvider(AIProviderBase):
    """OpenAI GPT-4o Provider"""
    
    def __init__(self):
        super().__init__(os.environ.get('OPENAI_API_KEY'))
        self.name = "OpenAI GPT-4o"
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return {"error": "OpenAI API key not available"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are CodeTrack Pro AI tutor, helping students learn programming and competitive coding."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.7)
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return {
                "content": result['choices'][0]['message']['content'],
                "provider": self.name,
                "tokens_used": result.get('usage', {}).get('total_tokens', 0)
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"error": str(e)}
    
    def generate_study_plan(self, user_goals: str, skill_level: str) -> Dict[str, Any]:
        prompt = f"""
        Create a 4-week structured study plan for a {skill_level} programmer with these goals: {user_goals}
        
        Return a JSON object with this structure:
        {{
            "weeks": [
                {{
                    "week": 1,
                    "focus": "topic",
                    "topics": ["topic1", "topic2"],
                    "problems_per_day": 3,
                    "study_hours_per_day": 2,
                    "daily_schedule": [
                        {{"day": "Monday", "activities": ["warm-up", "main topic", "practice"]}},
                        {{"day": "Tuesday", "activities": ["review", "new concept", "coding challenge"]}}
                    ],
                    "milestones": ["milestone1", "milestone2"],
                    "resources": ["resource1", "resource2"]
                }}
            ],
            "assessment_plan": {{
                "weekly_quizzes": true,
                "mock_interviews": ["week2", "week4"],
                "project_deadlines": ["week3", "week4"]
            }}
        }}
        """
        
        response = self.generate_response(prompt)
        if "error" not in response:
            try:
                return json.loads(response["content"])
            except json.JSONDecodeError:
                return {"error": "Failed to parse study plan response"}
        return response
    
    def generate_problem_recommendation(self, user_stats: Dict, weak_areas: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Based on user stats: {json.dumps(user_stats)} and weak areas: {weak_areas},
        recommend 5 coding problems with explanations.
        
        Return JSON:
        {{
            "recommendations": [
                {{
                    "title": "Problem Title",
                    "platform": "leetcode",
                    "difficulty": "medium",
                    "category": "array",
                    "url": "problem_url",
                    "reason": "Why this problem helps",
                    "learning_objectives": ["objective1", "objective2"],
                    "estimated_time": "30-45 minutes"
                }}
            ],
            "focus_areas": ["area1", "area2"],
            "study_tips": ["tip1", "tip2"]
        }}
        """
        
        response = self.generate_response(prompt)
        if "error" not in response:
            try:
                return json.loads(response["content"])
            except json.JSONDecodeError:
                return {"error": "Failed to parse problem recommendation response"}
        return response
    
    def generate_flashcards(self, topic: str, difficulty: str) -> List[Dict[str, str]]:
        prompt = f"""
        Generate 5 flashcards for {topic} at {difficulty} level.
        
        Return JSON array:
        [
            {{
                "question": "What is...?",
                "answer": "Answer explanation",
                "category": "topic",
                "difficulty": "medium"
            }}
        ]
        """
        
        response = self.generate_response(prompt)
        if "error" not in response:
            try:
                return json.loads(response["content"])
            except json.JSONDecodeError:
                return []
        return []

class DeepSeekProvider(AIProviderBase):
    """DeepSeek Chat Provider (Free, coding-focused)"""
    
    def __init__(self):
        super().__init__(os.environ.get('DEEPSEEK_API_KEY'))
        self.name = "DeepSeek Chat"
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return {"error": "DeepSeek API key not available"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a coding tutor helping students learn programming."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.7)
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return {
                "content": result['choices'][0]['message']['content'],
                "provider": self.name,
                "tokens_used": result.get('usage', {}).get('total_tokens', 0)
            }
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return {"error": str(e)}

class GeminiProvider(AIProviderBase):
    """Google Gemini 2.5 Flash Provider (Free multimodal)"""
    
    def __init__(self):
        super().__init__(os.environ.get('GEMINI_API_KEY'))
        self.name = "Google Gemini 2.5 Flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return {"error": "Gemini API key not available"}
        
        try:
            url = f"{self.base_url}?key={self.api_key}"
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": f"You are a coding tutor. {prompt}"
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": kwargs.get('max_tokens', 1000),
                    "temperature": kwargs.get('temperature', 0.7)
                }
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            return {
                "content": content,
                "provider": self.name,
                "tokens_used": 0  # Gemini doesn't provide token count in response
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {"error": str(e)}

class OpenRouterProvider(AIProviderBase):
    """OpenRouter Provider (Free model access)"""
    
    def __init__(self):
        super().__init__(os.environ.get('OPENROUTER_API_KEY'))
        self.name = "OpenRouter"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return {"error": "OpenRouter API key not available"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://codetrackpro.com",
                "X-Title": "CodeTrack Pro"
            }
            
            data = {
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": "You are a helpful coding tutor."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get('max_tokens', 1000),
                "temperature": kwargs.get('temperature', 0.7)
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return {
                "content": result['choices'][0]['message']['content'],
                "provider": self.name,
                "tokens_used": result.get('usage', {}).get('total_tokens', 0)
            }
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return {"error": str(e)}

class HuggingFaceProvider(AIProviderBase):
    """Hugging Face Provider (Free inference)"""
    
    def __init__(self):
        super().__init__(os.environ.get('HUGGINGFACE_API_KEY'))
        self.name = "Hugging Face"
        self.base_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return {"error": "Hugging Face API key not available"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "inputs": f"Human: {prompt}\nAssistant:",
                "parameters": {
                    "max_length": kwargs.get('max_tokens', 1000),
                    "temperature": kwargs.get('temperature', 0.7),
                    "return_full_text": False
                }
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result[0]['generated_text'].replace("Assistant:", "").strip()
            
            return {
                "content": content,
                "provider": self.name,
                "tokens_used": 0
            }
            
        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            return {"error": str(e)}

class LocalFallbackProvider(AIProviderBase):
    """Local fallback with hardcoded responses"""
    
    def __init__(self):
        super().__init__("local")
        self.name = "Local Fallback"
        
        # Hardcoded responses for common queries
        self.responses = {
            "study_plan": {
                "weeks": [
                    {
                        "week": 1,
                        "focus": "Data Structures Basics",
                        "topics": ["Arrays", "Linked Lists"],
                        "problems_per_day": 3,
                        "study_hours_per_day": 2,
                        "daily_schedule": [
                            {"day": "Monday", "activities": ["Array basics", "Practice problems", "Review"]},
                            {"day": "Tuesday", "activities": ["Linked list concepts", "Implementation", "Coding challenges"]}
                        ],
                        "milestones": ["Complete 15 array problems", "Understand linked list operations"],
                        "resources": ["LeetCode Easy problems", "GeeksforGeeks tutorials"]
                    }
                ],
                "assessment_plan": {
                    "weekly_quizzes": True,
                    "mock_interviews": ["week2", "week4"],
                    "project_deadlines": ["week3", "week4"]
                }
            },
            "problem_recommendation": {
                "recommendations": [
                    {
                        "title": "Two Sum",
                        "platform": "leetcode",
                        "difficulty": "easy",
                        "category": "array",
                        "url": "https://leetcode.com/problems/two-sum/",
                        "reason": "Fundamental array manipulation problem",
                        "learning_objectives": ["Hash map usage", "Time complexity optimization"],
                        "estimated_time": "15-20 minutes"
                    }
                ],
                "focus_areas": ["Array manipulation", "Hash maps"],
                "study_tips": ["Practice with different data structures", "Focus on time complexity"]
            },
            "flashcards": [
                {
                    "question": "What is the time complexity of binary search?",
                    "answer": "O(log n) - binary search halves the search space in each iteration",
                    "category": "algorithms",
                    "difficulty": "medium"
                }
            ]
        }
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        # Simple keyword matching for responses
        prompt_lower = prompt.lower()
        
        if "study plan" in prompt_lower:
            return {
                "content": json.dumps(self.responses["study_plan"], indent=2),
                "provider": self.name,
                "tokens_used": 0
            }
        elif "problem" in prompt_lower and "recommend" in prompt_lower:
            return {
                "content": json.dumps(self.responses["problem_recommendation"], indent=2),
                "provider": self.name,
                "tokens_used": 0
            }
        elif "flashcard" in prompt_lower:
            return {
                "content": json.dumps(self.responses["flashcards"], indent=2),
                "provider": self.name,
                "tokens_used": 0
            }
        else:
            return {
                "content": "I'm here to help you with your coding journey! Please ask me about study plans, problem recommendations, or any programming concepts.",
                "provider": self.name,
                "tokens_used": 0
            }

class MultiProviderAI:
    """Multi-provider AI system with automatic fallback"""
    
    def __init__(self):
        self.providers = [
            OpenAIProvider(),
            DeepSeekProvider(),
            GeminiProvider(),
            OpenRouterProvider(),
            HuggingFaceProvider(),
            LocalFallbackProvider()  # Always available as final fallback
        ]
        
        # Track provider performance
        self.provider_stats = {
            provider.name: {
                "success_count": 0,
                "failure_count": 0,
                "avg_response_time": 0,
                "last_used": None
            }
            for provider in self.providers
        }
    
    def _get_best_provider(self) -> AIProviderBase:
        """Get the best available provider based on stats"""
        available_providers = [p for p in self.providers if p.is_available()]
        
        if not available_providers:
            return self.providers[-1]  # Local fallback
        
        # Sort by success rate and response time
        def provider_score(provider):
            stats = self.provider_stats[provider.name]
            total_requests = stats["success_count"] + stats["failure_count"]
            success_rate = stats["success_count"] / max(total_requests, 1)
            return success_rate - (stats["avg_response_time"] / 1000)  # Prefer faster providers
        
        return max(available_providers, key=provider_score)
    
    def _update_provider_stats(self, provider_name: str, success: bool, response_time: float):
        """Update provider performance statistics"""
        stats = self.provider_stats[provider_name]
        stats["last_used"] = datetime.now()
        
        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1
        
        # Update average response time
        total_requests = stats["success_count"] + stats["failure_count"]
        stats["avg_response_time"] = (
            (stats["avg_response_time"] * (total_requests - 1) + response_time) / total_requests
        )
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response with automatic fallback"""
        start_time = time.time()
        
        # Try providers in order of preference
        for provider in self.providers:
            if not provider.is_available():
                continue
            
            try:
                response = provider.generate_response(prompt, **kwargs)
                response_time = (time.time() - start_time) * 1000  # ms
                
                if "error" not in response:
                    self._update_provider_stats(provider.name, True, response_time)
                    logger.info(f"Successfully generated response using {provider.name}")
                    return response
                else:
                    self._update_provider_stats(provider.name, False, response_time)
                    logger.warning(f"{provider.name} failed: {response['error']}")
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                self._update_provider_stats(provider.name, False, response_time)
                logger.error(f"{provider.name} exception: {e}")
                continue
        
        # This should never happen due to local fallback, but just in case
        return {
            "content": "I'm sorry, I'm having trouble connecting to AI services right now. Please try again later.",
            "provider": "System",
            "error": "All providers failed"
        }
    
    def generate_study_plan(self, user_goals: str, skill_level: str) -> Dict[str, Any]:
        """Generate personalized study plan"""
        provider = self._get_best_provider()
        
        if hasattr(provider, 'generate_study_plan'):
            return provider.generate_study_plan(user_goals, skill_level)
        else:
            # Fallback to general response
            prompt = f"Create a 4-week study plan for {skill_level} programmer with goals: {user_goals}"
            response = self.generate_response(prompt)
            if "error" not in response:
                try:
                    return json.loads(response["content"])
                except:
                    return {"error": "Failed to parse study plan"}
            return response
    
    def generate_problem_recommendation(self, user_stats: Dict, weak_areas: List[str]) -> Dict[str, Any]:
        """Generate problem recommendations"""
        provider = self._get_best_provider()
        
        if hasattr(provider, 'generate_problem_recommendation'):
            return provider.generate_problem_recommendation(user_stats, weak_areas)
        else:
            # Fallback to general response
            prompt = f"Recommend coding problems based on stats: {user_stats} and weak areas: {weak_areas}"
            response = self.generate_response(prompt)
            if "error" not in response:
                try:
                    return json.loads(response["content"])
                except:
                    return {"error": "Failed to parse problem recommendations"}
            return response
    
    def generate_flashcards(self, topic: str, difficulty: str) -> List[Dict[str, str]]:
        """Generate flashcards for a topic"""
        provider = self._get_best_provider()
        
        if hasattr(provider, 'generate_flashcards'):
            return provider.generate_flashcards(topic, difficulty)
        else:
            # Fallback to general response
            prompt = f"Generate flashcards for {topic} at {difficulty} level"
            response = self.generate_response(prompt)
            if "error" not in response:
                try:
                    return json.loads(response["content"])
                except:
                    return []
            return []
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about provider performance"""
        return self.provider_stats

# Global instance
ai_provider = MultiProviderAI()
