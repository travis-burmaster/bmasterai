"""
Simple LinkedIn Wellness Agent - Working Version
"""

import json
import subprocess
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import google.generativeai as genai

# For Tavily search
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

# Import BMasterAI components
try:
    from bmasterai import configure_logging, get_logger, get_monitor, LogLevel
    BMASTERAI_AVAILABLE = True
except ImportError:
    BMASTERAI_AVAILABLE = False
    
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    def get_logger(): return MockLogger()
    def get_monitor(): return None
    def configure_logging(**kwargs): pass


class LinkedInWellnessAgent:
    """Simple wellness advisor for LinkedIn profiles"""
    
    def __init__(self, agent_id: str, gemini_api_key: str, tavily_api_key: str = None):
        self.agent_id = agent_id
        self.gemini_api_key = gemini_api_key
        self.tavily_api_key = tavily_api_key
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # Initialize Tavily client
        self.tavily_client = None
        if TAVILY_AVAILABLE and tavily_api_key:
            try:
                self.tavily_client = TavilyClient(api_key=tavily_api_key)
            except Exception as e:
                print(f"Failed to initialize Tavily client: {e}")
        
        # BMasterAI integration
        self.logger = get_logger() if BMASTERAI_AVAILABLE else None
        self.monitor = get_monitor() if BMASTERAI_AVAILABLE else None
        
        self.update_callback = None

    def set_update_callback(self, callback: Callable):
        self.update_callback = callback

    def get_linkedin_profile_data(self, username: str) -> Dict[str, Any]:
        """Get LinkedIn profile data using Tavily search + web scraping"""
        if not self.tavily_client:
            raise ValueError("Tavily API key not configured. Cannot search for LinkedIn profiles.")
        
        try:
            # Search for LinkedIn profile using Tavily
            search_query = f"{username} site:linkedin.com/in/"
            search_results = self.tavily_client.search(
                query=search_query,
                search_depth="basic",
                max_results=3
            )
            
            linkedin_url = None
            for result in search_results.get('results', []):
                url = result.get('url', '')
                if 'linkedin.com/in/' in url:
                    linkedin_url = url
                    break
            
            if not linkedin_url:
                raise ValueError(f"No LinkedIn profile found for username: {username}")
            
            # Scrape the LinkedIn profile using curl
            curl_command = [
                'curl', '-s', '-L', 
                '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                linkedin_url
            ]
            
            result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise ValueError(f"Failed to fetch LinkedIn profile: {result.stderr}")
            
            html_content = result.stdout
            
            # Parse the HTML content to extract profile data
            profile_data = self._parse_linkedin_html(html_content, username)
            profile_data['linkedin_url'] = linkedin_url
            
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Error fetching LinkedIn profile for {username}: {e}")
            raise ValueError(f"Failed to fetch LinkedIn profile for {username}: {str(e)}")
    
    def _parse_linkedin_html(self, html_content: str, username: str) -> Dict[str, Any]:
        """Parse LinkedIn HTML content to extract profile information"""
        # Extract name from title tag
        name_match = re.search(r'<title[^>]*>([^|]+)', html_content)
        full_name = name_match.group(1).strip() if name_match else username
        
        # Split name into first and last
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else username
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        # Extract headline/description
        headline_patterns = [
            r'"headline":"([^"]+)"',
            r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"',
            r'<meta[^>]*name="description"[^>]*content="([^"]*)"'
        ]
        
        headline = ''
        for pattern in headline_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                headline = match.group(1).strip()
                break
        
        # Extract location
        location_patterns = [
            r'"geoLocationName":"([^"]+)"',
            r'"location":"([^"]+)"',
            r'<span[^>]*class="[^"]*location[^"]*"[^>]*>([^<]+)</span>'
        ]
        
        location = ''
        for pattern in location_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                break
        
        # Extract work experience data
        experiences = []
        current_title = ''
        current_company = ''
        
        # Look for structured job data in JSON-LD or other formats
        json_patterns = [
            r'"workHistory":\s*\[(.*?)\]',
            r'"position":\s*\[(.*?)\]',
            r'"jobTitle":"([^"]+)"',
            r'"worksFor":\s*{[^}]*"name":"([^"]+)"',
        ]
        
        # Try to extract job information from various sources
        job_title_patterns = [
            r'"jobTitle":"([^"]+)"',
            r'"title":"([^"]+)"[^}]*"companyName":"([^"]+)"',
            r'<span[^>]*>([^<]+)</span>[^<]*<span[^>]*>at\s+([^<]+)</span>',
        ]
        
        for pattern in job_title_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    title = match.group(1).strip()
                    company = match.group(2).strip()
                    if title and company and title not in [exp.get('title', '') for exp in experiences]:
                        experiences.append({
                            'title': title,
                            'company': company,
                            'description': f'{title} at {company}'
                        })
        
        # Extract current position/title from headline
        if headline:
            # Try to extract job title and company from headline
            title_company_patterns = [
                r'^([^|@]+?)\s+at\s+([^|@]+)',
                r'^([^|]+)\s*\|\s*([^|]+)',
                r'^([^@]+)\s*@\s*([^@]+)',
            ]
            
            for pattern in title_company_patterns:
                match = re.search(pattern, headline)
                if match:
                    current_title = match.group(1).strip()
                    current_company = match.group(2).strip()
                    break
            
            if not current_title:
                current_title = headline.split('|')[0].strip()
        
        # If we found experiences, use the first one as current
        if experiences and not current_title:
            current_title = experiences[0]['title']
            current_company = experiences[0].get('company', '')
        
        # Add current position to experiences if not already there
        if current_title and not any(exp.get('title') == current_title for exp in experiences):
            experiences.insert(0, {
                'title': current_title,
                'company': current_company,
                'description': f'{current_title}' + (f' at {current_company}' if current_company else ''),
                'isCurrent': True
            })
        
        # Extract skills from various sources
        skills = []
        skill_patterns = [
            r'"skills":\s*\[([^\]]+)\]',
            r'"name":"([^"]+)"[^}]*"type":"SKILL"',
            r'<span[^>]*skill[^>]*>([^<]+)</span>',
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE)
            for match in matches:
                skill_text = match.group(1).strip()
                if skill_text and skill_text not in skills:
                    skills.append({
                        'name': skill_text,
                        'endorsementsCount': 1  # Default count
                    })
        
        # Create comprehensive profile structure
        profile_data = {
            'firstName': first_name,
            'lastName': last_name,
            'headline': headline,
            'location': location,
            'current_title': current_title,
            'current_company': current_company,
            'position': experiences,
            'experience': experiences,  # Alternative key for compatibility
            'experience_count': len(experiences),
            'skills': skills,
            'skills_count': len(skills),
            'isDemo': False
        }
        
        return profile_data

    def analyze_stress_factors_with_reasoning(self, profile_data: Dict) -> List[Dict]:
        """Analyze stress factors"""
        stress_factors = []
        
        # Get current title from various possible structures
        current_title = ''
        positions = profile_data.get('position', [])
        if positions:
            current_title = positions[0].get('title', '')
        else:
            current_title = profile_data.get('current_title', '')
        
        # Also check headline
        headline = profile_data.get('headline', '')
        title_text = f"{current_title} {headline}".lower()
        
        if title_text:
            # Check for leadership stress
            high_stress_keywords = ['senior', 'lead', 'manager', 'director', 'vp', 'cto', 'ceo']
            if any(keyword in title_text for keyword in high_stress_keywords):
                stress_factors.append({
                    'category': 'Leadership Responsibility',
                    'severity': 'High',
                    'description': f'Senior role: {current_title or headline}',
                    'reasoning': 'Leadership positions involve higher stress and responsibility.',
                    'impact': 'May experience pressure from managing people and making critical decisions'
                })
            
            # Check for tech industry stress
            tech_keywords = ['engineer', 'developer', 'software', 'tech', 'ai', 'ml', 'data']
            if any(keyword in title_text for keyword in tech_keywords):
                stress_factors.append({
                    'category': 'Tech Industry Pressure',
                    'severity': 'Medium', 
                    'description': 'Working in fast-paced technology sector',
                    'reasoning': 'Tech industry requires continuous learning and adaptation.',
                    'impact': 'May experience pressure to stay current with technology'
                })
        
        # Check location for cost of living stress
        location = profile_data.get('location', '')
        high_cost_areas = ['san francisco', 'new york', 'seattle', 'boston', 'los angeles']
        if location and any(area in location.lower() for area in high_cost_areas):
            stress_factors.append({
                'category': 'Cost of Living Pressure',
                'severity': 'Medium',
                'description': f'Living in high-cost area: {location}',
                'reasoning': 'High cost of living areas create financial pressure.',
                'impact': 'Financial stress and potential for longer commutes'
            })
        
        return stress_factors

    def identify_happiness_opportunities_with_reasoning(self, profile_data: Dict, stress_factors: List[Dict]) -> List[Dict]:
        """Identify happiness opportunities"""
        opportunities = []
        
        # Professional development based on role
        current_title = profile_data.get('current_title', '')
        headline = profile_data.get('headline', '')
        role_text = f"{current_title} {headline}".lower()
        
        if role_text:
            # Leadership development opportunity
            leadership_keywords = ['ceo', 'director', 'vp', 'manager', 'lead', 'senior']
            if any(keyword in role_text for keyword in leadership_keywords):
                opportunities.append({
                    'category': 'Leadership Development',
                    'priority': 'High',
                    'title': 'Enhance leadership and strategic thinking skills',
                    'description': 'Develop advanced leadership capabilities and strategic vision',
                    'reasoning': 'Senior leaders benefit from continuous leadership development.',
                    'specific_actions': [
                        'Attend executive leadership workshops',
                        'Join leadership peer groups',
                        'Find an executive coach',
                        'Practice mindful leadership techniques'
                    ]
                })
            
            # Innovation and learning opportunity for tech roles
            tech_keywords = ['engineer', 'developer', 'software', 'tech', 'ai', 'ml', 'data']
            if any(keyword in role_text for keyword in tech_keywords):
                opportunities.append({
                    'category': 'Professional Development', 
                    'priority': 'High',
                    'title': 'Stay current with emerging technologies',
                    'description': 'Continuous learning in rapidly evolving tech landscape',
                    'reasoning': 'Technology professionals thrive when learning new skills.',
                    'specific_actions': [
                        'Take courses in AI/ML and emerging technologies',
                        'Attend technology conferences',
                        'Contribute to open source projects',
                        'Join professional tech communities'
                    ]
                })
        
        # Work-life balance opportunities
        if any(sf['severity'] in ['High', 'Medium'] for sf in stress_factors):
            opportunities.append({
                'category': 'Work-Life Balance',
                'priority': 'High', 
                'title': 'Implement comprehensive wellness practices',
                'description': 'Build sustainable habits for long-term success and well-being',
                'reasoning': 'Proactive wellness prevents burnout and enhances performance.',
                'specific_actions': [
                    'Establish clear work-life boundaries',
                    'Practice daily meditation or mindfulness',
                    'Schedule regular exercise and outdoor activities',
                    'Plan regular vacation and unplugging time'
                ]
            })
        
        # Network and mentorship opportunities
        location = profile_data.get('location', '')
        if location:
            opportunities.append({
                'category': 'Network & Community',
                'priority': 'Medium',
                'title': 'Build meaningful professional relationships',
                'description': f'Expand professional network in {location} area',
                'reasoning': 'Strong professional networks enhance career satisfaction.',
                'specific_actions': [
                    'Join local professional associations',
                    'Attend networking events and meetups',
                    'Become a mentor to junior professionals',
                    'Participate in industry panels or speaking opportunities'
                ]
            })
        
        return opportunities

    def generate_personalized_recommendations_with_reasoning(self, profile_data: Dict, stress_factors: List[Dict], opportunities: List[Dict]) -> List[Dict]:
        """Generate recommendations"""
        recommendations = []
        
        # High-priority stress management if stress factors exist
        if stress_factors:
            high_severity_count = sum(1 for sf in stress_factors if sf['severity'] == 'High')
            priority = 'Critical' if high_severity_count > 1 else 'High'
            
            recommendations.append({
                'title': 'Comprehensive Stress Management Strategy',
                'priority': priority,
                'timeframe': '2-4 weeks',
                'description': f'Address {len(stress_factors)} identified stress factors to prevent burnout',
                'reasoning': 'Proactive stress management is essential for sustained high performance.',
                'specific_steps': [
                    {'step': 1, 'action': 'Conduct stress audit and identify triggers', 'timeline': 'Week 1', 'reasoning': 'Self-awareness is the first step to stress management'},
                    {'step': 2, 'action': 'Implement daily mindfulness practice (10 minutes)', 'timeline': 'Week 2', 'reasoning': 'Mindfulness reduces cortisol and improves focus'},
                    {'step': 3, 'action': 'Establish work boundaries and communication protocols', 'timeline': 'Week 3', 'reasoning': 'Clear boundaries prevent work from overwhelming personal time'},
                    {'step': 4, 'action': 'Create weekly reflection and adjustment routine', 'timeline': 'Week 4', 'reasoning': 'Regular check-ins ensure sustainable progress'}
                ],
                'expected_outcomes': [
                    'Reduced daily stress levels by 30-40%',
                    'Improved focus and decision-making quality',
                    'Better work-life integration',
                    'Increased energy and motivation'
                ],
                'success_metrics': [
                    'Daily stress rating (1-10 scale)',
                    'Sleep quality improvement',
                    'Number of stress-triggered reactions per week',
                    'Weekly well-being assessment score'
                ]
            })
        
        # Professional development based on opportunities
        if opportunities:
            high_priority_opps = [opp for opp in opportunities if opp.get('priority') == 'High']
            if high_priority_opps:
                recommendations.append({
                    'title': 'Strategic Professional Development Plan',
                    'priority': 'High',
                    'timeframe': '3-6 months',
                    'description': f'Leverage {len(high_priority_opps)} high-priority growth opportunities',
                    'reasoning': 'Investing in strengths and growth areas accelerates career satisfaction.',
                    'specific_steps': [
                        {'step': 1, 'action': 'Set 3 specific development goals aligned with opportunities', 'timeline': 'Month 1', 'reasoning': 'Clear goals provide direction and motivation'},
                        {'step': 2, 'action': 'Identify and enroll in relevant courses or programs', 'timeline': 'Month 2', 'reasoning': 'Structured learning accelerates skill development'},
                        {'step': 3, 'action': 'Apply new skills in real projects or initiatives', 'timeline': 'Month 3-4', 'reasoning': 'Practice solidifies learning and builds confidence'},
                        {'step': 4, 'action': 'Share knowledge through mentoring or presentations', 'timeline': 'Month 5-6', 'reasoning': 'Teaching others reinforces learning and builds reputation'}
                    ],
                    'expected_outcomes': [
                        'Enhanced expertise in key areas',
                        'Increased visibility and recognition',
                        'Greater job satisfaction and engagement',
                        'Expanded professional network'
                    ],
                    'success_metrics': [
                        'Completion of development goals',
                        'Positive feedback from colleagues/supervisors',
                        'New opportunities or projects received',
                        'Self-assessment of confidence improvement'
                    ]
                })
        
        # Work-life integration recommendation
        current_title = profile_data.get('current_title', '')
        if any(keyword in current_title.lower() for keyword in ['ceo', 'director', 'vp', 'senior']):
            recommendations.append({
                'title': 'Executive Wellness & Sustainability Program',
                'priority': 'High',
                'timeframe': '6-12 months',
                'description': 'Build sustainable practices for long-term leadership effectiveness',
                'reasoning': 'Senior executives need sustainable practices to maintain peak performance.',
                'specific_steps': [
                    {'step': 1, 'action': 'Design personal energy management system', 'timeline': 'Month 1-2', 'reasoning': 'Energy management is more important than time management for executives'},
                    {'step': 2, 'action': 'Establish quarterly leadership retreats/reflection time', 'timeline': 'Month 3', 'reasoning': 'Regular strategic thinking time improves decision quality'},
                    {'step': 3, 'action': 'Build trusted advisory network', 'timeline': 'Month 4-6', 'reasoning': 'Peer support reduces isolation and improves decision-making'},
                    {'step': 4, 'action': 'Implement delegation and team empowerment practices', 'timeline': 'Month 7-12', 'reasoning': 'Effective delegation reduces stress and develops team capability'}
                ],
                'expected_outcomes': [
                    'Sustained high performance without burnout',
                    'Improved strategic thinking and decision quality',
                    'Stronger, more capable team',
                    'Better work-life integration'
                ],
                'success_metrics': [
                    'Energy levels throughout the day',
                    '360-degree feedback improvements',
                    'Team performance and engagement scores',
                    'Personal satisfaction and fulfillment ratings'
                ]
            })
        
        return recommendations

    def analyze_linkedin_profile_for_wellness(self, username: str) -> Dict[str, Any]:
        """Complete wellness analysis"""
        
        # Get profile data
        profile_data = self.get_linkedin_profile_data(username)
        
        # Analyze stress factors
        stress_factors = self.analyze_stress_factors_with_reasoning(profile_data)
        
        # Identify opportunities
        opportunities = self.identify_happiness_opportunities_with_reasoning(profile_data, stress_factors)
        
        # Generate recommendations
        recommendations = self.generate_personalized_recommendations_with_reasoning(
            profile_data, stress_factors, opportunities
        )
        
        return {
            'profile_summary': {
                'name': f"{profile_data.get('firstName', '')} {profile_data.get('lastName', '')}".strip(),
                'headline': profile_data.get('headline', 'N/A'),
                'location': profile_data.get('location', 'N/A'),
                'current_position': profile_data.get('current_title', 'N/A'),
                'current_company': profile_data.get('current_company', 'N/A'),
                'experience_count': profile_data.get('experience_count', 0),
                'skills_count': profile_data.get('skills_count', 0),
                'linkedin_url': profile_data.get('linkedin_url', ''),
                'total_factors': len(stress_factors) + len(opportunities)
            },
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
        """Get agent statistics"""
        return {
            'total_events': 0,
            'event_types': {},
            'bmasterai_available': BMASTERAI_AVAILABLE
        }

    def export_reasoning_logs(self, format_type: str = "json") -> str:
        """Export reasoning logs"""
        return json.dumps({
            'agent_id': self.agent_id,
            'export_date': datetime.now().isoformat(),
            'note': 'Simple version - full reasoning logs available in complex version'
        }, indent=2)