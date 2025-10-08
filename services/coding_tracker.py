"""
Platform Integration & Web Scraping for CodeTrack Pro
Handles LeetCode, GeeksforGeeks, GitHub, and HackerRank data extraction
"""

import os
import re
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)

class PlatformScraperBase:
    """Base class for platform scrapers"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rate_limit_delay = 1  # seconds between requests
    
    def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a rate-limited request"""
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _setup_driver(self) -> Optional[webdriver.Chrome]:
        """Setup undetected Chrome driver"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            driver = uc.Chrome(options=options)
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return None

class LeetCodeScraper(PlatformScraperBase):
    """LeetCode platform scraper with GraphQL API and enhanced scraping"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://leetcode.com"
        self.graphql_url = "https://leetcode.com/graphql"
        
        # GraphQL queries
        self.user_stats_query = """
        query userStats($username: String!) {
            matchedUser(username: $username) {
                username
                profile {
                    ranking
                    userAvatar
                    realName
                    aboutMe
                    school
                    websites
                    countryName
                    company
                    jobTitle
                    skillTags
                    postViewCount
                    postViewCountDiff
                    reputation
                    reputationDiff
                    solutionCount
                    solutionCountDiff
                    categoryDiscussCount
                    categoryDiscussCountDiff
                }
                submitStats {
                    acSubmissionNum {
                        difficulty
                        count
                        submissions
                    }
                }
                badges {
                    id
                    displayName
                    icon
                    creationDate
                }
                upcomingBadges {
                    name
                    icon
                }
                activeBadges {
                    id
                    displayName
                    icon
                    creationDate
                }
            }
        }
        """
        
        self.user_calendar_query = """
        query userProfileCalendar($username: String!, $year: String!) {
            matchedUser(username: $username) {
                userCalendar(year: $year) {
                    activeYears
                    streak
                    totalActiveDays
                    dccBadges {
                        timestamp
                        badge {
                            name
                            icon
                        }
                    }
                    submissionCalendar
                }
            }
        }
        """
    
    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Get user statistics using GraphQL API"""
        if not username:
            return {"error": "Username required"}
        
        try:
            # Get basic stats
            stats_data = self._get_graphql_data(self.user_stats_query, {"username": username})
            if "error" in stats_data:
                return stats_data
            
            user_data = stats_data.get("data", {}).get("matchedUser")
            if not user_data:
                return {"error": "User not found"}
            
            # Get calendar data for streak
            current_year = datetime.now().year
            calendar_data = self._get_graphql_data(
                self.user_calendar_query, 
                {"username": username, "year": str(current_year)}
            )
            
            streak = 0
            if calendar_data.get("data", {}).get("matchedUser", {}).get("userCalendar"):
                streak = calendar_data["data"]["matchedUser"]["userCalendar"].get("streak", 0)
            
            # Process submission stats
            submit_stats = user_data.get("submitStats", {}).get("acSubmissionNum", [])
            difficulty_stats = {}
            
            for stat in submit_stats:
                difficulty = stat.get("difficulty", "").lower()
                count = stat.get("count", 0)
                difficulty_stats[difficulty] = count
            
            total_problems = sum(difficulty_stats.values())
            
            # Get contest rating (requires additional scraping)
            contest_rating = self._get_contest_rating(username)
            
            return {
                "platform": "leetcode",
                "username": username,
                "total_problems": total_problems,
                "easy_solved": difficulty_stats.get("easy", 0),
                "medium_solved": difficulty_stats.get("medium", 0),
                "hard_solved": difficulty_stats.get("hard", 0),
                "contest_rating": contest_rating,
                "streak": streak,
                "ranking": user_data.get("profile", {}).get("ranking", 0),
                "reputation": user_data.get("profile", {}).get("reputation", 0),
                "badges": len(user_data.get("badges", [])),
                "last_updated": datetime.now().isoformat(),
                "raw_data": user_data
            }
            
        except Exception as e:
            logger.error(f"LeetCode scraping error for {username}: {e}")
            return {"error": str(e)}
    
    def _get_graphql_data(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GraphQL query"""
        try:
            payload = {
                "query": query,
                "variables": variables
            }
            
            response = self.session.post(
                self.graphql_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"GraphQL query failed: {e}")
            return {"error": str(e)}
    
    def _get_contest_rating(self, username: str) -> int:
        """Get contest rating by scraping profile page"""
        try:
            profile_url = f"{self.base_url}/{username}"
            response = self._make_request(profile_url)
            if not response:
                return 0
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for contest rating in the page
            rating_elements = soup.find_all(text=re.compile(r'Contest Rating'))
            for element in rating_elements:
                parent = element.parent
                if parent:
                    rating_text = parent.get_text()
                    rating_match = re.search(r'(\d+)', rating_text)
                    if rating_match:
                        return int(rating_match.group(1))
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to get contest rating for {username}: {e}")
            return 0
    
    def get_recent_activity(self, username: str) -> List[Dict[str, Any]]:
        """Get recent problem solving activity"""
        try:
            activity_url = f"{self.base_url}/{username}"
            response = self._make_request(activity_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            activities = []
            
            # Look for recent submissions or activities
            # This would need to be customized based on LeetCode's current HTML structure
            activity_elements = soup.find_all('div', class_=re.compile(r'submission|activity'))
            
            for element in activity_elements[:10]:  # Get last 10 activities
                try:
                    problem_link = element.find('a')
                    if problem_link:
                        activities.append({
                            "problem_title": problem_link.get_text().strip(),
                            "problem_url": problem_link.get('href', ''),
                            "timestamp": datetime.now().isoformat(),  # Would need to parse actual timestamp
                            "status": "accepted"  # Would need to determine from element
                        })
                except Exception:
                    continue
            
            return activities
            
        except Exception as e:
            logger.error(f"Failed to get recent activity for {username}: {e}")
            return []

class GeeksforGeeksScraper(PlatformScraperBase):
    """GeeksforGeeks profile scraper"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://auth.geeksforgeeks.org/user"
    
    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Get user statistics from GeeksforGeeks profile"""
        if not username:
            return {"error": "Username required"}
        
        try:
            profile_url = f"{self.base_url}/{username}"
            response = self._make_request(profile_url)
            if not response:
                return {"error": "Failed to fetch profile"}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic stats
            stats = {
                "platform": "geeksforgeeks",
                "username": username,
                "total_problems": 0,
                "easy_solved": 0,
                "medium_solved": 0,
                "hard_solved": 0,
                "contest_rating": 0,
                "streak": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            # Look for problem count statistics
            problem_count_elements = soup.find_all(text=re.compile(r'Problems Solved'))
            for element in problem_count_elements:
                parent = element.parent
                if parent:
                    count_text = parent.get_text()
                    count_match = re.search(r'(\d+)', count_text)
                    if count_match:
                        stats["total_problems"] = int(count_match.group(1))
                        break
            
            # Look for difficulty breakdown
            difficulty_elements = soup.find_all(text=re.compile(r'(Easy|Medium|Hard).*?\d+'))
            for element in difficulty_elements:
                text = element.strip()
                if 'Easy' in text:
                    easy_match = re.search(r'Easy.*?(\d+)', text)
                    if easy_match:
                        stats["easy_solved"] = int(easy_match.group(1))
                elif 'Medium' in text:
                    medium_match = re.search(r'Medium.*?(\d+)', text)
                    if medium_match:
                        stats["medium_solved"] = int(medium_match.group(1))
                elif 'Hard' in text:
                    hard_match = re.search(r'Hard.*?(\d+)', text)
                    if hard_match:
                        stats["hard_solved"] = int(hard_match.group(1))
            
            # Look for contest rating or ranking
            rating_elements = soup.find_all(text=re.compile(r'(Rating|Rank).*?\d+'))
            for element in rating_elements:
                text = element.strip()
                rating_match = re.search(r'(\d+)', text)
                if rating_match:
                    stats["contest_rating"] = int(rating_match.group(1))
                    break
            
            return stats
            
        except Exception as e:
            logger.error(f"GeeksforGeeks scraping error for {username}: {e}")
            return {"error": str(e)}

class GitHubScraper(PlatformScraperBase):
    """GitHub repository analysis scraper"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.github.com"
        self.token = os.environ.get('GITHUB_TOKEN')  # Optional for higher rate limits
        
        if self.token:
            self.session.headers.update({'Authorization': f'token {self.token}'})
    
    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Get user statistics from GitHub"""
        if not username:
            return {"error": "Username required"}
        
        try:
            # Get user profile
            user_url = f"{self.base_url}/users/{username}"
            response = self._make_request(user_url)
            if not response:
                return {"error": "Failed to fetch user profile"}
            
            user_data = response.json()
            
            # Get repository statistics
            repos_url = f"{self.base_url}/users/{username}/repos"
            repos_response = self._make_request(repos_url)
            repos_data = repos_response.json() if repos_response else []
            
            # Analyze repositories
            total_repos = len(repos_data)
            total_stars = sum(repo.get('stargazers_count', 0) for repo in repos_data)
            total_forks = sum(repo.get('forks_count', 0) for repo in repos_data)
            
            # Get language statistics
            language_stats = self._get_language_statistics(repos_data)
            
            # Get contribution statistics
            contribution_stats = self._get_contribution_stats(username)
            
            return {
                "platform": "github",
                "username": username,
                "total_repositories": total_repos,
                "total_stars": total_stars,
                "total_forks": total_forks,
                "followers": user_data.get('followers', 0),
                "following": user_data.get('following', 0),
                "public_repos": user_data.get('public_repos', 0),
                "language_stats": language_stats,
                "contribution_stats": contribution_stats,
                "account_created": user_data.get('created_at', ''),
                "last_updated": datetime.now().isoformat(),
                "raw_data": user_data
            }
            
        except Exception as e:
            logger.error(f"GitHub scraping error for {username}: {e}")
            return {"error": str(e)}
    
    def _get_language_statistics(self, repos_data: List[Dict]) -> Dict[str, int]:
        """Get language statistics from repositories"""
        language_counts = {}
        
        for repo in repos_data[:10]:  # Limit to first 10 repos for performance
            if repo.get('language'):
                lang = repo['language']
                language_counts[lang] = language_counts.get(lang, 0) + 1
        
        return language_counts
    
    def _get_contribution_stats(self, username: str) -> Dict[str, Any]:
        """Get contribution statistics"""
        try:
            # This would require scraping the contributions graph
            # For now, return basic stats
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "total_contributions": 0,
                "contributions_this_year": 0
            }
        except Exception as e:
            logger.error(f"Failed to get contribution stats: {e}")
            return {}

class HackerRankScraper(PlatformScraperBase):
    """HackerRank profile scraper"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.hackerrank.com"
    
    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Get user statistics from HackerRank"""
        if not username:
            return {"error": "Username required"}
        
        try:
            profile_url = f"{self.base_url}/{username}"
            response = self._make_request(profile_url)
            if not response:
                return {"error": "Failed to fetch profile"}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats = {
                "platform": "hackerrank",
                "username": username,
                "total_problems": 0,
                "easy_solved": 0,
                "medium_solved": 0,
                "hard_solved": 0,
                "contest_rating": 0,
                "streak": 0,
                "certificates": 0,
                "badges": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            # Look for problem statistics
            problem_elements = soup.find_all(text=re.compile(r'(\d+)\s+(problems|solved)'))
            for element in problem_elements:
                text = element.strip()
                match = re.search(r'(\d+)', text)
                if match:
                    stats["total_problems"] = int(match.group(1))
                    break
            
            # Look for domain-wise progress
            domain_elements = soup.find_all('div', class_=re.compile(r'domain|skill'))
            for element in domain_elements:
                # Extract domain-specific statistics
                pass  # Implementation would depend on current HackerRank structure
            
            return stats
            
        except Exception as e:
            logger.error(f"HackerRank scraping error for {username}: {e}")
            return {"error": str(e)}

class CodingTracker:
    """Main coding tracker that orchestrates all platform scrapers"""
    
    def __init__(self):
        self.scrapers = {
            'leetcode': LeetCodeScraper(),
            'geeksforgeeks': GeeksforGeeksScraper(),
            'github': GitHubScraper(),
            'hackerrank': HackerRankScraper()
        }
        
        # Rate limiting per platform
        self.last_scrape_times = {}
        self.scrape_cooldown = 300  # 5 minutes between scrapes per platform
    
    def scrape_user_stats(self, platform: str, username: str) -> Dict[str, Any]:
        """Scrape user statistics from specified platform"""
        if platform not in self.scrapers:
            return {"error": f"Unsupported platform: {platform}"}
        
        # Check rate limiting
        last_scrape_key = f"{platform}_{username}"
        last_scrape_time = self.last_scrape_times.get(last_scrape_key, datetime.min)
        
        if datetime.now() - last_scrape_time < timedelta(seconds=self.scrape_cooldown):
            return {"error": "Rate limited. Please try again later."}
        
        try:
            scraper = self.scrapers[platform]
            result = scraper.get_user_stats(username)
            
            # Update last scrape time
            self.last_scrape_times[last_scrape_key] = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Scraping failed for {platform}/{username}: {e}")
            return {"error": str(e)}
    
    def scrape_all_platforms(self, usernames: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Scrape all platforms for a user"""
        results = {}
        
        for platform, username in usernames.items():
            if username:  # Only scrape if username is provided
                logger.info(f"Scraping {platform} for user {username}")
                results[platform] = self.scrape_user_stats(platform, username)
            else:
                results[platform] = {"error": "No username provided"}
        
        return results
    
    def get_scraping_status(self) -> Dict[str, Any]:
        """Get current scraping status and rate limits"""
        return {
            "active_scrapers": list(self.scrapers.keys()),
            "rate_limits": self.last_scrape_times,
            "cooldown_seconds": self.scrape_cooldown
        }

# Global instance
coding_tracker = CodingTracker()
