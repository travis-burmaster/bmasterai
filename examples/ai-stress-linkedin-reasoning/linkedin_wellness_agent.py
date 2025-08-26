"""
LinkedIn Chain of Thought Wellness Advisor

This module implements a wellness advisor that analyzes LinkedIn profiles to provide
personalized stress reduction and happiness suggestions using transparent chain of 
thought reasoning with BMasterAI.
"""

import time
import json
import os
import sys
import requests
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import google.generativeai as genai

# Import the local mock data API for LinkedIn data access
from data_api import ApiClient

# Import BMasterAI components for full transparency
try:
    from bmasterai import (
        configure_logging, get_logger, get_monitor,
        LogLevel
    )
    BMASTERAI_AVAILABLE = True
    
    # Try importing reasoning components (may not be available in all versions)
    try:
        from bmasterai import ReasoningSession, ChainOfThought, with_reasoning_logging, log_reasoning
        REASONING_AVAILABLE = True
    except ImportError:
        REASONING_AVAILABLE = False
        # Mock reasoning components not needed since ChainOfThought is disabled
        ReasoningSession = None
        ChainOfThought = None
        def with_reasoning_logging(func):
            return func
        def log_reasoning(agent_id, task, thoughts, conclusion):
            pass
        
except ImportError:
    BMASTERAI_AVAILABLE = False
    REASONING_AVAILABLE = False
    print("BMasterAI library not found. Please install it with: pip install bmasterai")
    
    # Create mock classes for when bmasterai is not available
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    def get_logger(name):
        return MockLogger()
    
    def get_monitor():
        return None
    
    def configure_logging(**kwargs):
        pass
    
    class LogLevel:
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"


class LinkedInWellnessAgent:
    """
        Chain of thought wellness advisor powered by Gemini + BMasterAI + LinkedIn APIs
        Provides transparent reasoning for personalized stress reduction and happiness suggestions
    """
    
    def __init__(self, agent_id: str, gemini_api_key: str):
        self.agent_id = agent_id
        self.gemini_api_key = gemini_api_key
        self.model_name = "gemini-2.0-flash-exp"
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        # Initialize LinkedIn API client
        self.linkedin_client = ApiClient()
        
        # Get BMasterAI logger and monitor if available
        if BMASTERAI_AVAILABLE:
            self.logger = get_logger()
            self.monitor = get_monitor()
            self.monitor.start_monitoring()
        else:
            self.logger = None
            self.monitor = None
        
        # Callback for real-time UI updates
        self.update_callback: Optional[Callable] = None
    
    def set_update_callback(self, callback: Callable):
        """Set callback function for real-time UI updates"""
        self.update_callback = callback
    
    def _send_reasoning_update(self, step_type: str, reasoning: str, conclusion: str = "", data: Any = None, confidence: float = 0.8):
        """Send reasoning update to UI callback and BMasterAI logging"""
        
        update_data = {
        'type': step_type,
        'reasoning': reasoning,
        'conclusion': conclusion,
        'data': data,
        'confidence': confidence,
        'timestamp': datetime.now().isoformat()
        }
        
        # Log to BMasterAI if available
        if BMASTERAI_AVAILABLE and self.logger:
            log_reasoning(
            agent_id=self.agent_id,
            task_description=step_type,
            thinking_steps=[reasoning],
            final_conclusion=str(data),
            model="gemini-pro",
            metadata={'confidence': confidence}
            )
        
            # Send to UI callback
        if self.update_callback:
            self.update_callback(update_data)
    
    def get_linkedin_profile_data(self, username: str) -> Dict[str, Any]:
    """Get LinkedIn profile data with transparent reasoning"""
        
        self._send_reasoning_update(
        "profile_extraction_start",
        f"I need to extract comprehensive profile data for {username} to understand their professional context, career trajectory, and current situation.",
        "Starting LinkedIn profile data extraction process."
        )
        
        try:
        self._send_reasoning_update(
            "api_call_linkedin",
            f"Calling LinkedIn API to get profile data for {username}. This will provide experience, skills, education, and current role information that I need for wellness analysis.",
            "Making API call to LinkedIn profile endpoint."
        )
        
        response = self.linkedin_client.call_api('LinkedIn/get_user_profile_by_username', 
        query={'username': username})
        
        if response and (response.get('success') or response.get('id')):
            # Handle both wrapped and direct response formats
            profile_data = response.get('data', response) if response.get('success') else response
                
            self._send_reasoning_update(
            "data_extraction_success",
            f"Successfully extracted profile data for {username}. Found {len(profile_data.get('position', []))} work experiences, {len(profile_data.get('skills', []))} skills, and {len(profile_data.get('educations', []))} education entries.",
            "Profile data extraction completed successfully.",
            data={'profile_summary': self._create_profile_summary(profile_data)}
            )
                
        return profile_data
        else:
        self._send_reasoning_update(
            "data_extraction_error",
            f"LinkedIn API returned an error or empty response for {username}. This could mean the profile is private, doesn't exist, or there's an API issue.",
            "Will proceed with demo mode using sample data.",
        data={'error': response}
            )
        return self._get_demo_profile_data(username)
                
        except Exception as e:
        self._send_reasoning_update(
            "data_extraction_exception",
            f"Exception occurred while extracting profile data for {username}: {str(e)}. This could be due to network issues, API limits, or invalid username.",
            "Will proceed with demo mode to demonstrate the reasoning process.",
        data={'error': str(e)}
        )
        return self._get_demo_profile_data(username)
    
    def _create_profile_summary(self, profile_data: Dict) -> Dict:
    """Create a summary of key profile information"""
        return {
        'name': f"{profile_data.get('firstName', '')} {profile_data.get('lastName', '')}".strip(),
        'headline': profile_data.get('headline', 'N/A'),
        'location': profile_data.get('geo', {}).get('full', 'N/A'),
        'current_position': profile_data.get('position', [{}])[0].get('title', 'N/A') if profile_data.get('position') else 'N/A',
        'current_company': profile_data.get('position', [{}])[0].get('companyName', 'N/A') if profile_data.get('position') else 'N/A',
        'experience_count': len(profile_data.get('position', [])),
        'skills_count': len(profile_data.get('skills', [])),
        'education_count': len(profile_data.get('educations', []))
        }
    
    def _get_demo_profile_data(self, username: str) -> Dict[str, Any]:
    """Generate demo profile data for demonstration purposes"""
        return {
        'firstName': 'Demo',
        'lastName': 'User',
        'username': username,
        'headline': 'Senior Software Engineer | AI/ML Enthusiast | Tech Leadership',
        'geo': {'full': 'San Francisco, CA'},
        'position': [
            {
            'title': 'Senior Software Engineer',
            'companyName': 'TechCorp Inc.',
            'start': {'year': 2022},
            'end': {'year': 0},  # Current position
            'description': 'Leading AI/ML initiatives and managing a team of 5 engineers'
            },
            {
            'title': 'Software Engineer',
            'companyName': 'StartupXYZ',
            'start': {'year': 2020},
            'end': {'year': 2022},
            'description': 'Full-stack development with focus on scalable backend systems'
            }
        ],
        'skills': [
            {'name': 'Python', 'endorsementsCount': 45},
            {'name': 'Machine Learning', 'endorsementsCount': 32},
            {'name': 'Leadership', 'endorsementsCount': 28},
            {'name': 'React', 'endorsementsCount': 25},
            {'name': 'AWS', 'endorsementsCount': 22}
        ],
        'educations': [
            {
            'schoolName': 'Stanford University',
            'degree': 'Master of Science',
            'fieldOfStudy': 'Computer Science',
            'start': {'year': 2018},
            'end': {'year': 2020}
            }
        ],
        'summary': 'Passionate software engineer with expertise in AI/ML and team leadership. Focused on building scalable solutions and mentoring junior developers.',
        'isDemo': True
        }
    
    def analyze_stress_factors_with_reasoning(self, profile_data: Dict) -> List[Dict]:
    """Analyze potential stress factors with transparent chain of thought reasoning"""
        
        if not BMASTERAI_AVAILABLE:
            return self._analyze_stress_factors_basic(profile_data)
        
            # cot = ChainOfThought(self.agent_id, "stress_factor_identification", "gemini-pro")
            stress_factors = []
        
            # Career Transition Analysis
            # cot.step("Analyzing career transitions and job stability")
            # cot.reason("Recent job changes can indicate career instability, growth seeking, or adaptation to market changes. Each scenario has different stress implications.")
        
            positions = profile_data.get('position', [])
        if len(positions) > 1:
            recent_changes = sum(1 for pos in positions[:3] if pos.get('end', {}).get('year', 0) > 2020)
        if recent_changes >= 2:
            stress_factor = {
            'category': 'Career Instability',
            'severity': 'Medium',
            'description': f'Multiple job changes in recent years ({recent_changes} changes since 2020)',
            'reasoning': 'Frequent job changes can create uncertainty about career direction and financial stability, leading to increased stress levels.',
            'impact': 'May cause anxiety about job security and career progression'
            }
            stress_factors.append(stress_factor)
                
            self._send_reasoning_update(
            "career_transition_analysis",
            f"Identified {recent_changes} job changes since 2020. This pattern suggests either rapid career growth or potential instability.",
            f"Classified as medium-severity stress factor due to potential uncertainty.",
            data=stress_factor
            )
        
            # Industry and Role Pressure Assessment
            # cot.step("Evaluating industry-specific and role-specific stress factors")
            # cot.reason("Different industries and roles have varying stress levels, work cultures, and pressure points that affect well-being.")
        
            current_title = positions[0].get('title', '') if positions else ''
            current_company = positions[0].get('companyName', '') if positions else ''
        
            # Check for high-stress role indicators
            high_stress_keywords = ['senior', 'lead', 'manager', 'director', 'vp', 'cto', 'ceo']
        if any(keyword in current_title.lower() for keyword in high_stress_keywords):
            stress_factor = {
            'category': 'Leadership Responsibility',
            'severity': 'High',
            'description': f'Senior role with leadership responsibilities: {current_title}',
            'reasoning': 'Leadership positions typically involve higher stress due to increased responsibility, decision-making pressure, and accountability for team performance.',
            'impact': 'May experience pressure from managing people, meeting targets, and making critical decisions'
            }
            stress_factors.append(stress_factor)
        
            self._send_reasoning_update(
            "leadership_stress_analysis",
            f"Current role '{current_title}' indicates leadership responsibilities. Senior positions typically involve higher stress levels due to increased accountability.",
            "Identified high-severity stress factor related to leadership pressure.",
            data=stress_factor
            )
        
            # Tech Industry Specific Stress
            tech_indicators = ['engineer', 'developer', 'software', 'tech', 'ai', 'ml', 'data']
        if any(indicator in current_title.lower() for indicator in tech_indicators):
            stress_factor = {
            'category': 'Tech Industry Pressure',
            'severity': 'Medium',
            'description': 'Working in fast-paced technology sector',
            'reasoning': 'Tech industry is known for rapid changes, continuous learning requirements, long hours, and high performance expectations.',
            'impact': 'May experience pressure to stay current with technology, meet tight deadlines, and handle complex problem-solving'
            }
            stress_factors.append(stress_factor)
        
            self._send_reasoning_update(
            "tech_industry_analysis",
            "Identified technology sector employment. Tech industry typically involves rapid change, continuous learning pressure, and high-performance expectations.",
            "Added medium-severity stress factor for tech industry pressures.",
            data=stress_factor
            )
        
            # Work-Life Balance Assessment
            # cot.step("Examining work-life balance indicators")
            # cot.reason("Location, company size, and role demands significantly affect personal time and work-life balance.")
        
            location = profile_data.get('geo', {}).get('full', '')
            high_cost_areas = ['san francisco', 'new york', 'seattle', 'boston', 'los angeles']
        if any(area in location.lower() for area in high_cost_areas):
            stress_factor = {
            'category': 'Cost of Living Pressure',
            'severity': 'Medium',
            'description': f'Living in high-cost area: {location}',
            'reasoning': 'High cost of living areas create financial pressure and may require longer work hours or higher salaries to maintain lifestyle.',
            'impact': 'Financial stress and potential for longer commutes or smaller living spaces'
            }
            stress_factors.append(stress_factor)
        
            self._send_reasoning_update(
            "location_stress_analysis",
            f"Location '{location}' is identified as a high-cost living area. This typically creates additional financial pressure and lifestyle constraints.",
            "Added medium-severity stress factor for cost of living pressures.",
            data=stress_factor
            )
        
            # Skill Gap Analysis
            # cot.step("Assessing potential skill gaps and learning pressure")
            # cot.reason("In rapidly evolving fields, skill gaps can create anxiety about career relevance and job security.")
        
            skills = profile_data.get('skills', [])
        if len(skills) < 10:
            stress_factor = {
            'category': 'Skill Development Pressure',
            'severity': 'Low',
            'description': f'Limited skill diversity ({len(skills)} skills listed)',
            'reasoning': 'Having fewer documented skills may indicate need for skill development or better self-promotion, both of which can create professional anxiety.',
            'impact': 'May feel pressure to develop more skills or better showcase existing capabilities'
            }
            stress_factors.append(stress_factor)
        
            self._send_reasoning_update(
            "skill_gap_analysis",
            f"Profile shows {len(skills)} documented skills. This may indicate opportunity for skill development or better self-promotion.",
            "Added low-severity stress factor for skill development needs.",
            data=stress_factor
            )
        
            # cot.conclude(f"Identified {len(stress_factors)} potential stress factors across career, industry, location, and skill dimensions.")
        
        return stress_factors
    
    def _analyze_stress_factors_basic(self, profile_data: Dict) -> List[Dict]:
    """Basic stress factor analysis without BMasterAI"""
        stress_factors = []
        
        # Simple analysis without chain of thought
        positions = profile_data.get('position', [])
        current_title = positions[0].get('title', '') if positions else ''
        
        if 'senior' in current_title.lower() or 'lead' in current_title.lower():
            stress_factors.append({
            'category': 'Leadership Responsibility',
            'severity': 'High',
            'description': f'Senior role: {current_title}',
            'reasoning': 'Leadership positions involve higher stress and responsibility.',
            'impact': 'Increased pressure and decision-making responsibility'
            })
        
        return stress_factors
    
    def identify_happiness_opportunities_with_reasoning(self, profile_data: Dict, stress_factors: List[Dict]) -> List[Dict]:
    """Identify happiness enhancement opportunities with transparent reasoning"""
        
        if not BMASTERAI_AVAILABLE:
            return self._identify_happiness_opportunities_basic(profile_data, stress_factors)
        
            # cot = ChainOfThought(self.agent_id, "happiness_opportunity_identification", "gemini-pro")
            opportunities = []
        
            # Skill Development and Confidence Building
            # cot.step("Identifying skill development opportunities for confidence building")
            # cot.reason("Continuous learning and skill building enhance career satisfaction, reduce anxiety about job security, and provide sense of accomplishment.")
        
            skills = profile_data.get('skills', [])
            current_title = profile_data.get('position', [{}])[0].get('title', '') if profile_data.get('position') else ''
        
            # Identify trending skills in their field
        if 'engineer' in current_title.lower() or 'developer' in current_title.lower():
            opportunity = {
            'category': 'Professional Development',
            'priority': 'High',
            'title': 'Expand Technical Leadership Skills',
            'description': 'Develop advanced technical leadership and mentoring capabilities',
            'reasoning': 'Technical professionals often find fulfillment in mentoring others and leading technical initiatives, which also enhances career prospects.',
            'specific_actions': [
            'Consider technical mentoring or coaching opportunities',
            'Explore speaking at tech meetups or conferences',
            'Lead a technical initiative or open-source project',
            'Develop skills in emerging technologies relevant to your field'
            ],
            'happiness_impact': 'Provides sense of purpose, recognition, and career advancement'
            }
            opportunities.append(opportunity)
        
            self._send_reasoning_update(
            "skill_development_opportunity",
            f"Based on technical role '{current_title}', identified opportunity for technical leadership development. This aligns with natural career progression and provides fulfillment through mentoring.",
            "Added high-priority opportunity for technical leadership skills.",
            data=opportunity
            )
        
            # Work-Life Balance Enhancement
            # cot.step("Assessing work-life balance improvement opportunities")
            # cot.reason("Better boundaries and time management lead to reduced stress and increased personal fulfillment without sacrificing career growth.")
        
            # Check if they have stress factors that could be mitigated
            has_high_stress = any(sf['severity'] == 'High' for sf in stress_factors)
        if has_high_stress:
            opportunity = {
            'category': 'Work-Life Balance',
            'priority': 'High',
            'title': 'Implement Stress Management and Boundary Setting',
            'description': 'Develop sustainable work practices and stress management techniques',
            'reasoning': 'Given identified high-stress factors, implementing structured stress management and boundary setting is crucial for long-term happiness and career sustainability.',
            'specific_actions': [
            'Establish clear work-life boundaries (e.g., no emails after 7 PM)',
            'Practice time-blocking for focused work and personal time',
            'Implement regular stress-relief activities (exercise, meditation, hobbies)',
            'Consider delegating more responsibilities if in leadership role'
            ],
            'happiness_impact': 'Reduces burnout risk, improves personal relationships, and increases overall life satisfaction'
            }
            opportunities.append(opportunity)
        
            self._send_reasoning_update(
            "work_life_balance_opportunity",
            "Identified high-stress factors in profile analysis. Implementing structured work-life balance improvements could significantly reduce stress and increase happiness.",
            "Added high-priority opportunity for stress management and boundary setting.",
            data=opportunity
            )
        
            # Career Alignment and Purpose
            # cot.step("Evaluating career-passion alignment and purpose fulfillment")
            # cot.reason("When work aligns with personal interests and values, job satisfaction and happiness increase significantly, leading to better performance and life satisfaction.")
        
            education = profile_data.get('educations', [])
        if education:
            latest_education = education[0]
            field_of_study = latest_education.get('fieldOfStudy', '')
        
            opportunity = {
            'category': 'Career Fulfillment',
            'priority': 'Medium',
            'title': 'Align Work with Educational Background and Interests',
            'description': f'Leverage {field_of_study} background for more fulfilling work',
            'reasoning': f'Educational background in {field_of_study} suggests deep interest in this area. Aligning current work more closely with this foundation can increase job satisfaction.',
            'specific_actions': [
            f'Seek projects that utilize {field_of_study} knowledge more directly',
            'Consider specializing in areas that combine current role with educational background',
            'Explore opportunities to teach or share knowledge in your field of study',
            'Join professional associations related to your educational background'
            ],
            'happiness_impact': 'Increases sense of purpose and utilizes natural interests and abilities'
            }
            opportunities.append(opportunity)
        
            self._send_reasoning_update(
            "career_alignment_opportunity",
            f"Educational background in {field_of_study} provides foundation for career alignment. Leveraging this background more directly could increase job satisfaction and sense of purpose.",
            "Added medium-priority opportunity for career-education alignment.",
            data=opportunity
            )
        
            # Social Connection and Networking
            # cot.step("Identifying social connection and professional networking opportunities")
            # cot.reason("Strong professional and personal relationships are key predictors of happiness and career success, providing support, opportunities, and sense of belonging.")
        
            location = profile_data.get('geo', {}).get('full', '')
        if location:
            opportunity = {
            'category': 'Social Connection',
            'priority': 'Medium',
            'title': 'Build Professional and Personal Community',
            'description': f'Expand professional network and social connections in {location}',
            'reasoning': 'Strong social connections are fundamental to happiness and career success. Building community provides support, opportunities, and sense of belonging.',
            'specific_actions': [
            f'Join professional meetups and organizations in {location}',
            'Participate in industry conferences and networking events',
            'Consider joining hobby groups or volunteer organizations',
            'Schedule regular coffee meetings with colleagues and industry peers'
            ],
            'happiness_impact': 'Provides social support, reduces isolation, and creates opportunities for collaboration and friendship'
            }
            opportunities.append(opportunity)
        
            self._send_reasoning_update(
            "social_connection_opportunity",
            f"Location in {location} provides opportunities for professional and social networking. Building stronger community connections can significantly impact happiness and career growth.",
            "Added medium-priority opportunity for community building.",
            data=opportunity
            )
        
            # Recognition and Achievement
            # cot.step("Identifying opportunities for recognition and achievement satisfaction")
            # cot.reason("Recognition and achievement are important motivators. Creating opportunities for visible accomplishments can boost confidence and career satisfaction.")
        
            skills = profile_data.get('skills', [])
            top_skills = sorted(skills, key=lambda x: x.get('endorsementsCount', 0), reverse=True)[:3]
        
        if top_skills:
            top_skill = top_skills[0]['name']
            opportunity = {
            'category': 'Recognition & Achievement',
            'priority': 'Medium',
            'title': f'Showcase Expertise in {top_skill}',
            'description': f'Build recognition around your strongest skill: {top_skill}',
            'reasoning': f'{top_skill} appears to be a key strength with {top_skills[0].get("endorsementsCount", 0)} endorsements. Building visible expertise in this area can provide recognition and career advancement.',
            'specific_actions': [
            f'Write articles or blog posts about {top_skill}',
            f'Speak at conferences or meetups about {top_skill}',
            f'Mentor others in {top_skill}',
            f'Contribute to open-source projects showcasing {top_skill}'
            ],
            'happiness_impact': 'Provides recognition, builds reputation, and creates sense of expertise and authority'
            }
            opportunities.append(opportunity)
        
            self._send_reasoning_update(
            "recognition_opportunity",
            f"Top skill '{top_skill}' with {top_skills[0].get('endorsementsCount', 0)} endorsements represents a strength that could be leveraged for greater recognition and career satisfaction.",
            "Added medium-priority opportunity for expertise showcase.",
            data=opportunity
            )
        
            # cot.conclude(f"Identified {len(opportunities)} happiness enhancement opportunities across professional development, work-life balance, career alignment, social connection, and recognition dimensions.")
        
        return opportunities
    
    def _identify_happiness_opportunities_basic(self, profile_data: Dict, stress_factors: List[Dict]) -> List[Dict]:
    """Basic happiness opportunity identification without BMasterAI"""
        opportunities = []
        
        # Simple analysis
        skills = profile_data.get('skills', [])
        if skills:
            top_skill = max(skills, key=lambda x: x.get('endorsementsCount', 0))['name']
            opportunities.append({
            'category': 'Professional Development',
            'priority': 'High',
            'title': f'Develop expertise in {top_skill}',
            'description': f'Build on your strength in {top_skill}',
            'reasoning': 'Leveraging existing strengths builds confidence.',
            'specific_actions': [f'Take advanced courses in {top_skill}'],
            'happiness_impact': 'Increased confidence and career prospects'
            })
        
        return opportunities
    
    def generate_personalized_recommendations_with_reasoning(self, profile_data: Dict, stress_factors: List[Dict], opportunities: List[Dict]) -> List[Dict]:
    """Generate personalized recommendations with transparent reasoning"""
        
        if not BMASTERAI_AVAILABLE:
            return self._generate_recommendations_basic(profile_data, stress_factors, opportunities)
        
            # cot = ChainOfThought(self.agent_id, "personalized_recommendation_generation", "gemini-pro")
            recommendations = []
        
            # Prioritization and Integration
            # cot.step("Prioritizing recommendations based on impact and feasibility")
            # cot.reason("I need to prioritize recommendations based on potential impact, feasibility, and alignment with identified stress factors and happiness opportunities.")
        
            # High-priority recommendations addressing immediate stress
            high_stress_factors = [sf for sf in stress_factors if sf['severity'] == 'High']
            high_priority_opportunities = [op for op in opportunities if op['priority'] == 'High']
        
        if high_stress_factors and high_priority_opportunities:
            # Create integrated recommendation addressing both stress and opportunity
            stress_factor = high_stress_factors[0]
            opportunity = high_priority_opportunities[0]
        
            recommendation = {
            'title': 'Immediate Stress Management with Skill Development',
            'priority': 'Critical',
            'timeframe': '1-3 months',
            'description': f'Address {stress_factor["category"].lower()} while building {opportunity["category"].lower()} capabilities',
            'reasoning': f'Combining stress management for {stress_factor["category"]} with {opportunity["category"]} development creates a sustainable approach that addresses immediate concerns while building long-term satisfaction.',
            'specific_steps': [
            {
            'step': 1,
            'action': 'Assess current stress levels and triggers',
            'timeline': 'Week 1',
            'reasoning': 'Understanding specific stress triggers enables targeted interventions'
            },
            {
            'step': 2,
            'action': 'Implement daily stress management routine',
            'timeline': 'Week 2-4',
            'reasoning': 'Consistent daily practices build resilience and coping capacity'
            },
            {
            'step': 3,
            'action': f'Begin {opportunity["title"].lower()} activities',
            'timeline': 'Week 3-8',
            'reasoning': 'Starting skill development early provides positive focus and future benefits'
            },
            {
            'step': 4,
            'action': 'Evaluate progress and adjust approach',
            'timeline': 'Week 8-12',
            'reasoning': 'Regular evaluation ensures the approach remains effective and sustainable'
            }
            ],
            'expected_outcomes': [
            'Reduced daily stress levels',
            'Improved coping mechanisms',
            'Enhanced professional capabilities',
            'Greater sense of control and direction'
            ],
            'success_metrics': [
            'Daily stress rating (1-10 scale)',
            'Sleep quality improvement',
            'Progress on skill development goals',
            'Feedback from colleagues or supervisors'
            ]
            }
            recommendations.append(recommendation)
        
            self._send_reasoning_update(
            "critical_recommendation_generation",
            f"Created integrated recommendation addressing high-severity stress factor ({stress_factor['category']}) with high-priority opportunity ({opportunity['category']}). This approach tackles immediate concerns while building long-term satisfaction.",
            "Generated critical-priority recommendation combining stress management with skill development.",
            data=recommendation
            )
        
            # Medium-term career development recommendation
            # cot.step("Creating medium-term career development recommendations")
            # cot.reason("Medium-term recommendations should focus on sustainable career growth and life satisfaction improvements that build on immediate stress management.")
        
            current_title = profile_data.get('position', [{}])[0].get('title', '') if profile_data.get('position') else ''
            skills = profile_data.get('skills', [])
        
            recommendation = {
            'title': 'Strategic Career Development and Life Integration',
            'priority': 'High',
            'timeframe': '3-12 months',
            'description': 'Build sustainable career growth while maintaining work-life balance',
            'reasoning': f'Based on current role as {current_title} and skill set, focusing on strategic career development with life integration will provide long-term satisfaction and reduced stress.',
            'specific_steps': [
            {
            'step': 1,
            'action': 'Define 12-month career and life goals',
            'timeline': 'Month 1',
            'reasoning': 'Clear goals provide direction and motivation while preventing drift'
            },
            {
            'step': 2,
            'action': 'Identify skill gaps and development opportunities',
            'timeline': 'Month 1-2',
            'reasoning': 'Understanding skill gaps enables targeted learning and career advancement'
            },
            {
            'step': 3,
            'action': 'Create learning and networking plan',
            'timeline': 'Month 2-3',
            'reasoning': 'Structured learning and networking accelerate career growth and satisfaction'
            },
            {
            'step': 4,
            'action': 'Implement monthly progress reviews',
            'timeline': 'Month 3-12',
            'reasoning': 'Regular reviews ensure progress and allow for course corrections'
            }
            ],
            'expected_outcomes': [
            'Clear career direction and goals',
            'Enhanced professional network',
            'Improved skills and capabilities',
            'Better work-life integration'
            ],
            'success_metrics': [
            'Achievement of monthly learning goals',
            'Expansion of professional network',
            'Positive feedback on new skills',
            'Improved work-life balance rating'
            ]
            }
            recommendations.append(recommendation)
        
            self._send_reasoning_update(
            "career_development_recommendation",
            f"Created strategic career development recommendation based on current role '{current_title}' and identified opportunities. This provides sustainable growth path while maintaining life balance.",
            "Generated high-priority recommendation for strategic career development.",
            data=recommendation
            )
        
            # Long-term fulfillment and purpose recommendation
            # cot.step("Developing long-term fulfillment and purpose recommendations")
            # cot.reason("Long-term recommendations should focus on deeper fulfillment, purpose, and sustainable happiness that goes beyond immediate career concerns.")
        
            education = profile_data.get('educations', [])
            location = profile_data.get('geo', {}).get('full', '')
        
            recommendation = {
            'title': 'Purpose-Driven Impact and Community Building',
            'priority': 'Medium',
            'timeframe': '6-24 months',
            'description': 'Build meaningful impact and community connections for long-term fulfillment',
            'reasoning': 'Long-term happiness comes from sense of purpose, meaningful relationships, and positive impact. Building these elements creates sustainable fulfillment beyond career success.',
            'specific_steps': [
            {
            'step': 1,
            'action': 'Identify personal values and impact areas',
            'timeline': 'Month 1-2',
            'reasoning': 'Understanding personal values guides meaningful choices and activities'
            },
            {
            'step': 2,
            'action': 'Find mentoring or teaching opportunities',
            'timeline': 'Month 3-6',
            'reasoning': 'Sharing knowledge and helping others provides deep satisfaction and purpose'
            },
            {
            'step': 3,
            'action': 'Join or create community initiatives',
            'timeline': 'Month 6-12',
            'reasoning': 'Community involvement builds relationships and creates positive impact'
            },
            {
            'step': 4,
            'action': 'Develop long-term impact projects',
            'timeline': 'Month 12-24',
            'reasoning': 'Long-term projects provide sustained purpose and meaningful achievement'
            }
            ],
            'expected_outcomes': [
            'Stronger sense of purpose and meaning',
            'Expanded community connections',
            'Positive impact on others',
            'Enhanced life satisfaction and fulfillment'
            ],
            'success_metrics': [
            'Number of people mentored or helped',
            'Community involvement level',
            'Personal fulfillment rating',
            'Long-term project progress'
            ]
            }
            recommendations.append(recommendation)
        
            self._send_reasoning_update(
            "purpose_fulfillment_recommendation",
            f"Created long-term fulfillment recommendation focusing on purpose, community, and impact. This addresses deeper happiness needs beyond immediate career concerns.",
            "Generated medium-priority recommendation for purpose-driven impact.",
            data=recommendation
            )
        
            # cot.conclude(f"Generated {len(recommendations)} personalized recommendations spanning immediate stress management, strategic career development, and long-term purpose fulfillment.")
        
        return recommendations
    
    def _generate_recommendations_basic(self, profile_data: Dict, stress_factors: List[Dict], opportunities: List[Dict]) -> List[Dict]:
    """Basic recommendation generation without BMasterAI"""
        recommendations = []
        
        # Simple recommendation based on stress factors
        if stress_factors:
            recommendations.append({
            'title': 'Stress Management Plan',
            'priority': 'High',
            'timeframe': '1-3 months',
            'description': 'Address identified stress factors',
            'reasoning': 'Managing stress is crucial for well-being.',
            'specific_steps': [
            {'step': 1, 'action': 'Identify stress triggers', 'timeline': 'Week 1'},
            {'step': 2, 'action': 'Implement coping strategies', 'timeline': 'Week 2-12'}
            ],
            'expected_outcomes': ['Reduced stress levels'],
            'success_metrics': ['Daily stress rating']
            })
        
        return recommendations
    
    def analyze_linkedin_profile_for_wellness(self, username: str) -> Dict[str, Any]:
    """
        Complete LinkedIn profile analysis for wellness recommendations with full chain of thought transparency
    """
        
        if not BMASTERAI_AVAILABLE:
            return self._analyze_profile_basic(username)
        
            with ReasoningSession(
            self.agent_id,
            f"Analyze LinkedIn profile {username} for personalized stress reduction and happiness suggestions",
            self.model_name,
            metadata={"username": username, "analysis_type": "wellness_assessment"}
            ) as session:
        
            # Step 1: Profile Data Extraction
            session.think(
            f"I need to extract comprehensive profile data for {username} to understand their professional context, career trajectory, and potential stress factors. This will form the foundation for personalized wellness recommendations.",
            confidence=0.9
            )
        
            profile_data = self.get_linkedin_profile_data(username)
        
        if not profile_data:
            session.think("Profile data extraction failed. I'll provide general wellness guidance and demonstrate the reasoning process.", confidence=0.5)
        return {'error': 'Profile data not available', 'demo_mode': True}
        
        # Step 2: Stress Factor Identification
        session.think(
            "Now I'll analyze the profile data to identify potential sources of stress based on role, industry, career changes, and work-life balance indicators. This systematic analysis will help me understand what might be causing stress in their professional life.",
        confidence=0.8
        )
        
        stress_factors = self.analyze_stress_factors_with_reasoning(profile_data)
        
        # Step 3: Happiness Opportunity Assessment
        session.think(
            "I'll look for opportunities to enhance happiness through career satisfaction, skill development, work-life balance, and personal fulfillment. These opportunities should complement the stress reduction strategies.",
        confidence=0.8
        )
        
        happiness_opportunities = self.identify_happiness_opportunities_with_reasoning(profile_data, stress_factors)
        
        # Step 4: Personalized Recommendation Generation
        session.think(
            "Based on my analysis of stress factors and happiness opportunities, I'll generate specific, actionable recommendations tailored to this person's unique professional situation. These recommendations will be prioritized and include concrete steps.",
        confidence=0.9
        )
        
        recommendations = self.generate_personalized_recommendations_with_reasoning(
            profile_data, stress_factors, happiness_opportunities
        )
        
        # Step 5: Final Integration and Summary
        session.think(
            f"I've completed a comprehensive analysis identifying {len(stress_factors)} stress factors, {len(happiness_opportunities)} happiness opportunities, and generated {len(recommendations)} personalized recommendations. Now I'll create a cohesive summary with clear next steps.",
        confidence=0.9
        )
        
        # Create comprehensive analysis result
        analysis_result = {
            'profile_summary': self._create_profile_summary(profile_data),
            'stress_factors': stress_factors,
            'happiness_opportunities': happiness_opportunities,
            'recommendations': recommendations,
            'analysis_metadata': {
            'username': username,
            'analysis_date': datetime.now().isoformat(),
            'total_stress_factors': len(stress_factors),
            'total_opportunities': len(happiness_opportunities),
            'total_recommendations': len(recommendations),
            'high_priority_recommendations': len([r for r in recommendations if r['priority'] in ['Critical', 'High']]),
            'is_demo': profile_data.get('isDemo', False)
            }
        }
        
        session.decide(
            "Analysis completion assessment",
            ["comprehensive_analysis_complete", "partial_analysis_complete", "analysis_insufficient"],
            "comprehensive_analysis_complete",
            f"Successfully completed comprehensive wellness analysis with {len(stress_factors)} stress factors, {len(happiness_opportunities)} opportunities, and {len(recommendations)} actionable recommendations."
        )
        
        self._send_reasoning_update(
            "analysis_complete",
            f"Completed comprehensive LinkedIn wellness analysis for {username}. Generated personalized recommendations addressing both stress reduction and happiness enhancement.",
            f"Analysis complete with {len(recommendations)} actionable recommendations.",
        data=analysis_result['analysis_metadata']
        )
        
        return analysis_result
    
    def _analyze_profile_basic(self, username: str) -> Dict[str, Any]:
    """Basic profile analysis without BMasterAI"""
        profile_data = self.get_linkedin_profile_data(username)
        stress_factors = self._analyze_stress_factors_basic(profile_data)
        opportunities = self._identify_happiness_opportunities_basic(profile_data, stress_factors)
        recommendations = self._generate_recommendations_basic(profile_data, stress_factors, opportunities)
        
        return {
        'profile_summary': self._create_profile_summary(profile_data),
        'stress_factors': stress_factors,
        'happiness_opportunities': opportunities,
        'recommendations': recommendations,
        'analysis_metadata': {
            'username': username,
            'analysis_date': datetime.now().isoformat(),
            'total_stress_factors': len(stress_factors),
            'total_opportunities': len(opportunities),
            'total_recommendations': len(recommendations),
            'is_demo': profile_data.get('isDemo', False)
        }
        }
    
    def get_agent_stats(self) -> Dict[str, Any]:
    """Get agent statistics for analytics display"""
        if BMASTERAI_AVAILABLE and self.monitor:
            return {
            'total_events': getattr(self.monitor, 'total_events', 0),
            'event_types': getattr(self.monitor, 'event_types', {}),
            'bmasterai_available': True
            }
        else:
        return {
            'total_events': 0,
            'event_types': {},
            'bmasterai_available': False
        }
    
    def export_reasoning_logs(self, format_type: str = "json") -> str:
    """Export reasoning logs in specified format"""
        if not BMASTERAI_AVAILABLE:
            return "BMasterAI not available - no logs to export"
        
            # This would integrate with BMasterAI's export functionality
            # For now, return a placeholder
        if format_type == "json":
            return json.dumps({
            'agent_id': self.agent_id,
            'export_date': datetime.now().isoformat(),
            'note': 'BMasterAI log export functionality would be integrated here'
            }, indent=2)
        else:
        return f"# BMasterAI Reasoning Logs\n\nAgent ID: {self.agent_id}\nExport Date: {datetime.now().isoformat()}\n\nBMasterAI log export functionality would be integrated here."

