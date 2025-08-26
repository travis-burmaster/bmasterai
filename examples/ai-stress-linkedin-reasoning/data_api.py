"""
Mock Data API for LinkedIn Wellness Agent

This module provides a mock implementation of the LinkedIn data API
for demonstration purposes when the actual Manus API is not available.
"""

import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class ApiClient:
    """Mock API client for LinkedIn data access"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.mock-linkedin.com/v1"
        
    def get_profile_data(self, profile_url: str) -> Dict[str, Any]:
        """
        Mock LinkedIn profile data retrieval
        
        Args:
            profile_url: LinkedIn profile URL
            
        Returns:
            Dictionary containing mock profile data
        """
        # Extract username from URL for consistency
        username = profile_url.split('/')[-1] if '/' in profile_url else profile_url
        
        # Generate mock profile data
        mock_data = {
            "profile_url": profile_url,
            "username": username,
            "name": f"Mock User {username.title()}",
            "headline": self._get_random_headline(),
            "location": random.choice(["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX"]),
            "industry": random.choice(["Technology", "Healthcare", "Finance", "Marketing", "Education"]),
            "connections": random.randint(500, 2000),
            "posts": self._generate_mock_posts(),
            "activity_level": random.choice(["high", "medium", "low"]),
            "engagement_score": round(random.uniform(0.1, 1.0), 2),
            "stress_indicators": self._generate_stress_indicators(),
            "last_updated": datetime.now().isoformat()
        }
        
        return mock_data
    
    def get_recent_activity(self, profile_url: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Mock recent LinkedIn activity data
        
        Args:
            profile_url: LinkedIn profile URL
            days: Number of days to look back
            
        Returns:
            List of mock activity items
        """
        activities = []
        num_activities = random.randint(5, 20)
        
        for i in range(num_activities):
            activity_date = datetime.now() - timedelta(days=random.randint(0, days))
            activity = {
                "type": random.choice(["post", "comment", "like", "share", "connection"]),
                "content": self._get_random_activity_content(),
                "timestamp": activity_date.isoformat(),
                "engagement": random.randint(0, 50),
                "sentiment": random.choice(["positive", "neutral", "negative"]),
                "stress_level": random.choice(["low", "medium", "high"])
            }
            activities.append(activity)
        
        return sorted(activities, key=lambda x: x["timestamp"], reverse=True)
    
    def _get_random_headline(self) -> str:
        """Generate a random professional headline"""
        roles = ["Software Engineer", "Data Scientist", "Product Manager", "Marketing Director", 
                "Sales Executive", "UX Designer", "Business Analyst", "DevOps Engineer"]
        companies = ["TechCorp", "InnovateCo", "DataSys", "CloudFirst", "AIStartup", "BigTech"]
        
        return f"{random.choice(roles)} at {random.choice(companies)}"
    
    def _generate_mock_posts(self) -> List[Dict[str, Any]]:
        """Generate mock LinkedIn posts"""
        post_templates = [
            "Excited to share my thoughts on the future of {topic}...",
            "Had a great experience working on {project} with my team...",
            "Just completed a challenging project involving {skill}...",
            "Grateful for the opportunity to work with {team_type} teams...",
            "Learning so much about {technology} in my current role..."
        ]
        
        topics = ["AI", "machine learning", "cloud computing", "data science", "remote work"]
        projects = ["mobile app development", "data migration", "system optimization", "user research"]
        skills = ["Python", "React", "AWS", "data analysis", "project management"]
        team_types = ["cross-functional", "international", "diverse", "agile"]
        technologies = ["Kubernetes", "GraphQL", "microservices", "blockchain", "edge computing"]
        
        posts = []
        num_posts = random.randint(3, 8)
        
        for i in range(num_posts):
            template = random.choice(post_templates)
            content = template.format(
                topic=random.choice(topics),
                project=random.choice(projects),
                skill=random.choice(skills),
                team_type=random.choice(team_types),
                technology=random.choice(technologies)
            )
            
            post_date = datetime.now() - timedelta(days=random.randint(1, 60))
            
            post = {
                "content": content,
                "timestamp": post_date.isoformat(),
                "likes": random.randint(5, 100),
                "comments": random.randint(0, 25),
                "shares": random.randint(0, 10),
                "sentiment": random.choice(["positive", "neutral", "negative"])
            }
            posts.append(post)
        
        return sorted(posts, key=lambda x: x["timestamp"], reverse=True)
    
    def _generate_stress_indicators(self) -> Dict[str, Any]:
        """Generate mock stress indicators from profile analysis"""
        return {
            "posting_frequency": random.choice(["low", "normal", "high"]),
            "negative_sentiment_ratio": round(random.uniform(0.0, 0.3), 2),
            "work_life_balance_mentions": random.randint(0, 5),
            "overtime_indicators": random.randint(0, 3),
            "burnout_keywords": random.randint(0, 2),
            "stress_level_estimate": random.choice(["low", "medium", "high"]),
            "confidence_score": round(random.uniform(0.6, 0.9), 2)
        }
    
    def _get_random_activity_content(self) -> str:
        """Generate random activity content"""
        activities = [
            "Shared an article about industry trends",
            "Commented on a colleague's post about remote work",
            "Posted about a recent project milestone",
            "Liked a post about professional development",
            "Shared insights from a recent conference",
            "Connected with a new professional contact",
            "Commented on a discussion about work-life balance",
            "Posted about team achievements"
        ]
        return random.choice(activities)