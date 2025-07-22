import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from bmasterai.agents.base_agent import BaseAgent
from bmasterai.tools.llm_tool import LLMTool


@dataclass
class SynthesisResult:
    """Data class for synthesis results"""
    key_insights: List[str]
    patterns: List[str]
    themes: List[str]
    summary: str
    confidence_score: float
    sources_analyzed: int
    analysis_timestamp: datetime
    recommendations: List[str]
    gaps_identified: List[str]


class SynthesisAgent(BaseAgent):
    """
    Agent responsible for synthesizing and analyzing gathered research information.
    
    This agent takes raw research data from multiple sources and:
    - Identifies key patterns and themes
    - Extracts meaningful insights
    - Creates structured summaries
    - Provides confidence assessments
    - Identifies knowledge gaps
    """
    
    def __init__(self, name: str = "SynthesisAgent", **kwargs):
        super().__init__(name=name, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.llm_tool = LLMTool()
        
        # Analysis configuration
        self.min_confidence_threshold = 0.6
        self.max_insights_per_analysis = 10
        self.pattern_detection_sensitivity = 0.7
        
        # Synthesis prompts
        self.synthesis_prompts = {
            "insight_extraction": """
            Analyze the following research data and extract key insights:
            
            Research Data:
            {research_data}
            
            Please identify:
            1. The most important findings
            2. Surprising or counterintuitive discoveries
            3. Actionable insights
            4. Statistical or quantitative highlights
            5. Expert opinions and consensus views
            
            Format your response as a JSON object with an 'insights' array.
            """,
            
            "pattern_analysis": """
            Examine the following research information for patterns and themes:
            
            Data:
            {research_data}
            
            Identify:
            1. Recurring themes across sources
            2. Contradictions or conflicting information
            3. Temporal patterns or trends
            4. Causal relationships
            5. Common methodologies or approaches
            
            Return a JSON object with 'patterns' and 'themes' arrays.
            """,
            
            "comprehensive_summary": """
            Create a comprehensive summary of the research findings:
            
            Research Topic: {topic}
            
            Data Sources:
            {research_data}
            
            Key Insights:
            {insights}
            
            Patterns:
            {patterns}
            
            Create a well-structured summary that:
            1. Provides an executive overview
            2. Highlights key findings
            3. Discusses implications
            4. Notes limitations or gaps
            5. Suggests areas for further research
            
            Keep the summary concise but comprehensive (500-800 words).
            """,
            
            "gap_analysis": """
            Analyze the research data to identify knowledge gaps and limitations:
            
            Research Data:
            {research_data}
            
            Topic: {topic}
            
            Identify:
            1. Areas with insufficient information
            2. Contradictory findings that need resolution
            3. Missing perspectives or stakeholder views
            4. Methodological limitations
            5. Temporal or geographical gaps
            
            Return a JSON object with a 'gaps' array describing each identified gap.
            """
        }
    
    async def synthesize_research(
        self, 
        research_data: List[Dict[str, Any]], 
        topic: str,
        focus_areas: Optional[List[str]] = None
    ) -> SynthesisResult:
        """
        Main synthesis method that processes research data and generates insights.
        
        Args:
            research_data: List of research findings from various sources
            topic: The research topic being analyzed
            focus_areas: Optional list of specific areas to focus analysis on
            
        Returns:
            SynthesisResult object containing all analysis results
        """
        try:
            self.logger.info(f"Starting synthesis for topic: {topic}")
            
            # Validate input data
            if not research_data:
                raise ValueError("No research data provided for synthesis")
            
            # Prepare data for analysis
            formatted_data = self._format_research_data(research_data)
            
            # Run parallel analysis tasks
            tasks = [
                self._extract_insights(formatted_data, focus_areas),
                self._analyze_patterns(formatted_data),
                self._identify_gaps(formatted_data, topic)
            ]
            
            insights, (patterns, themes), gaps = await asyncio.gather(*tasks)
            
            # Generate comprehensive summary
            summary = await self._generate_summary(
                topic, formatted_data, insights, patterns
            )
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                insights, patterns, gaps, topic
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                research_data, insights, patterns
            )
            
            # Create synthesis result
            result = SynthesisResult(
                key_insights=insights,
                patterns=patterns,
                themes=themes,
                summary=summary,
                confidence_score=confidence_score,
                sources_analyzed=len(research_data),
                analysis_timestamp=datetime.now(),
                recommendations=recommendations,
                gaps_identified=gaps
            )
            
            self.logger.info(f"Synthesis completed with confidence: {confidence_score:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during synthesis: {str(e)}")
            raise
    
    def _format_research_data(self, research_data: List[Dict[str, Any]]) -> str:
        """Format research data for LLM processing"""
        formatted_sections = []
        
        for i, data in enumerate(research_data, 1):
            section = f"Source {i}:\n"
            
            if 'title' in data:
                section += f"Title: {data['title']}\n"
            if 'source' in data:
                section += f"Source: {data['source']}\n"
            if 'content' in data:
                section += f"Content: {data['content']}\n"
            if 'key_points' in data:
                section += f"Key Points: {', '.join(data['key_points'])}\n"
            if 'metadata' in data:
                section += f"Metadata: {json.dumps(data['metadata'])}\n"
            
            section += "\n" + "-" * 50 + "\n\n"
            formatted_sections.append(section)
        
        return "".join(formatted_sections)
    
    async def _extract_insights(
        self, 
        research_data: str, 
        focus_areas: Optional[List[str]] = None
    ) -> List[str]:
        """Extract key insights from research data"""
        try:
            prompt = self.synthesis_prompts["insight_extraction"].format(
                research_data=research_data
            )
            
            if focus_areas:
                prompt += f"\n\nFocus particularly on these areas: {', '.join(focus_areas)}"
            
            response = await self.llm_tool.generate_response(prompt)
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response)
                insights = parsed_response.get('insights', [])
            except json.JSONDecodeError:
                # Fallback: extract insights from text response
                insights = self._extract_insights_from_text(response)
            
            # Limit number of insights
            return insights[:self.max_insights_per_analysis]
            
        except Exception as e:
            self.logger.error(f"Error extracting insights: {str(e)}")
            return []
    
    async def _analyze_patterns(self, research_data: str) -> Tuple[List[str], List[str]]:
        """Analyze patterns and themes in research data"""
        try:
            prompt = self.synthesis_prompts["pattern_analysis"].format(
                research_data=research_data
            )
            
            response = await self.llm_tool.generate_response(prompt)
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response)
                patterns = parsed_response.get('patterns', [])
                themes = parsed_response.get('themes', [])
            except json.JSONDecodeError:
                # Fallback: extract from text
                patterns, themes = self._extract_patterns_from_text(response)
            
            return patterns, themes
            
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {str(e)}")
            return [], []
    
    async def _generate_summary(
        self, 
        topic: str, 
        research_data: str, 
        insights: List[str], 
        patterns: List[str]
    ) -> str:
        """Generate comprehensive summary"""
        try:
            prompt = self.synthesis_prompts["comprehensive_summary"].format(
                topic=topic,
                research_data=research_data[:2000],  # Truncate for token limits
                insights="\n".join(f"- {insight}" for insight in insights),
                patterns="\n".join(f"- {pattern}" for pattern in patterns)
            )
            
            summary = await self.llm_tool.generate_response(prompt)
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return f"Summary generation failed for topic: {topic}"
    
    async def _identify_gaps(self, research_data: str, topic: str) -> List[str]:
        """Identify knowledge gaps in the research"""
        try:
            prompt = self.synthesis_prompts["gap_analysis"].format(
                research_data=research_data,
                topic=topic
            )
            
            response = await self.llm_tool.generate_response(prompt)
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response)
                gaps = parsed_response.get('gaps', [])
            except json.JSONDecodeError:
                # Fallback: extract from text
                gaps = self._extract_gaps_from_text(response)
            
            return gaps
            
        except Exception as e:
            self.logger.error(f"Error identifying gaps: {str(e)}")
            return []
    
    async def _generate_recommendations(
        self, 
        insights: List[str], 
        patterns: List[str], 
        gaps: List[str], 
        topic: str
    ) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        try:
            prompt = f"""
            Based on the following analysis of research on "{topic}", generate actionable recommendations:
            
            Key Insights:
            {chr(10).join(f"- {insight}" for insight in insights)}
            
            Patterns Identified:
            {chr(10).join(f"- {pattern}" for pattern in patterns)}
            
            Knowledge Gaps:
            {chr(10).join(f"- {gap}" for gap in gaps)}
            
            Provide 3-7 specific, actionable recommendations that address the findings and gaps.
            Format as a JSON object with a 'recommendations' array.
            """
            
            response = await self.llm_tool.generate_response(prompt)
            
            try:
                parsed_response = json.loads(response)
                recommendations = parsed_response.get('recommendations', [])
            except json.JSONDecodeError:
                recommendations = self._extract_recommendations_from_text(response)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _calculate_confidence_score(
        self, 
        research_data: List[Dict[str, Any]], 
        insights: List[str], 
        patterns: List[str]
    ) -> float:
        """Calculate confidence score for the synthesis"""
        try:
            # Factors affecting confidence
            source_count_factor = min(len(research_data) / 5.0, 1.0)  # More sources = higher confidence
            insight_quality_factor = min(len(insights) / 5.0, 1.0)  # More insights = higher confidence
            pattern_consistency_factor = min(len(patterns) / 3.0, 1.0)  # Patterns indicate consistency
            
            # Check for source diversity
            source_types = set()
            for data in research_data:
                if 'source_type' in data:
                    source_types.add(data['source_type'])
            
            diversity_factor = min(len(source_types) / 3.0, 1.0)
            
            # Calculate weighted confidence score
            confidence = (
                source_count_factor * 0.3 +
                insight_quality_factor * 0.3 +
                pattern_consistency_factor * 0.2 +
                diversity_factor * 0.2
            )
            
            return max(min(confidence, 1.0), 0.1)  # Clamp between 0.1 and 1.0
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.5  # Default moderate confidence
    
    def _extract_insights_from_text(self, text: str) -> List[str]:
        """Fallback method to extract insights from text response"""
        insights = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 
                        line.startswith('*') or re.match(r'^\d+\.', line)):
                # Clean up the line
                cleaned = re.sub(r'^[-•*\d.]\s*', '', line).strip()
                if len(cleaned) > 10:  # Filter out very short items
                    insights.append(cleaned)
        
        return insights[:self.max_insights_per_analysis]
    
    def _extract_patterns_from_text(self, text: str) -> Tuple[List[str], List[str]]:
        """Fallback method to extract patterns and themes from text"""
        patterns = []
        themes = []
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip().lower()
            
            if 'pattern' in line:
                current_section = 'patterns'
                continue
            elif 'theme' in line:
                current_section = 'themes'
                continue
            
            if line and (line.startswith('-') or line.startswith('•') or 
                        line.startswith('*') or re.match(r'^\d+\.', line)):
                cleaned = re.sub(r'^[-•*\d.]\s*', '', line).strip()
                if len(cleaned) > 10:
                    if current_section == 'patterns':
                        patterns.append(cleaned)
                    elif current_section == 'themes':
                        themes.append(cleaned)
                    else:
                        # Default to patterns if section unclear
                        patterns.append(cleaned)
        
        return patterns, themes
    
    def _extract_gaps_from_text(self, text: str) -> List[str]:
        """Fallback method to extract gaps from text response"""
        gaps = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 
                        line.startswith('*') or re.match(r'^\d+\.', line)):
                cleaned = re.sub(r'^[-•*\d.]\s*', '', line).strip()
                if len(cleaned) > 10:
                    gaps.append(cleaned)
        
        return gaps
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Fallback method to extract recommendations from text response"""
        recommendations = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or 
                        line.startswith('*') or re.match(r'^\d+\.', line)):
                cleaned = re.sub(r'^[-•*\d.]\s*', '', line).strip()
                if len(cleaned) > 15:  # Recommendations should be substantial
                    recommendations.append(cleaned)
        
        return recommendations
    
    async def validate_synthesis_quality(self, result: SynthesisResult) -> Dict[str, Any]:
        """Validate the quality of synthesis results"""
        validation_report = {
            "overall_quality": "good",
            "issues": [],
            "suggestions": [],
            "confidence_assessment": "acceptable"
        }
        
        try:
            # Check confidence score
            if result.confidence_score < self.min_confidence_threshold:
                validation_report["issues"].append(
                    f"Low confidence score: {result.confidence_score:.2f}"
                )
                validation_report["overall_quality"] = "needs_improvement"
            
            # Check for sufficient insights
            if len(result.key_insights) < 3:
                validation_report["issues"].append("Insufficient key insights identified")
                validation_report["suggestions"].append("Consider gathering more diverse sources")
            
            # Check for patterns
            if len(result.patterns) < 2:
                validation_report["suggestions"].append("Look for more pattern connections")
            
            # Check summary length
            if len(result.summary) < 200:
                validation_report["issues"].append("Summary appears too brief")
            
            # Assess confidence level
            if result.confidence_score >= 0.8:
                validation_report["confidence_assessment"] = "high"
            elif result.confidence_score >= 0.6:
                validation_report["confidence_assessment"] = "acceptable"
            else:
                validation_report["confidence_assessment"] = "low"
            
            return validation_report
            
        except Exception as e:
            self.logger.error(f"Error validating synthesis quality: {str(e)}")
            return {
                "overall_quality": "unknown",
                "issues": ["Validation failed"],
                "suggestions": [],
                "confidence_assessment": "unknown"
            }