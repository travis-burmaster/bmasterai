import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from bmasterai.agents.base_agent import BaseAgent
from bmasterai.tools.text_processing import TextProcessor
from bmasterai.utils.exceptions import AgentError

logger = logging.getLogger(__name__)

class EditingAgent(BaseAgent):
    """
    Agent responsible for refining and formatting the final research report.
    
    This agent takes synthesized research content and applies editorial refinements
    including grammar correction, style consistency, formatting, and structure optimization.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the editing agent.
        
        Args:
            config: Configuration dictionary containing editing preferences and settings
        """
        super().__init__(
            name="EditingAgent",
            description="Refines and formats research reports with professional editing standards",
            config=config
        )
        
        self.text_processor = TextProcessor()
        self.editing_rules = config.get('editing_rules', self._get_default_editing_rules())
        self.output_format = config.get('output_format', 'markdown')
        self.style_guide = config.get('style_guide', 'academic')
        self.max_section_length = config.get('max_section_length', 2000)
        
        # Editorial standards
        self.grammar_check_enabled = config.get('grammar_check', True)
        self.consistency_check_enabled = config.get('consistency_check', True)
        self.citation_format = config.get('citation_format', 'apa')
        
    def _get_default_editing_rules(self) -> Dict[str, Any]:
        """Get default editing rules and preferences."""
        return {
            'remove_redundancy': True,
            'improve_transitions': True,
            'standardize_terminology': True,
            'enhance_clarity': True,
            'maintain_academic_tone': True,
            'check_logical_flow': True,
            'optimize_paragraph_length': True,
            'ensure_consistent_formatting': True
        }
    
    async def process_content(self, synthesized_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and refine synthesized research content.
        
        Args:
            synthesized_content: Dictionary containing synthesized research data
            
        Returns:
            Dictionary containing the refined and formatted report
        """
        try:
            self.update_status("processing", "Starting content editing and refinement")
            
            # Extract content sections
            sections = self._extract_sections(synthesized_content)
            
            # Apply editorial refinements
            refined_sections = await self._refine_sections(sections)
            
            # Ensure consistency across sections
            consistent_sections = await self._ensure_consistency(refined_sections)
            
            # Format according to output specifications
            formatted_report = await self._format_report(consistent_sections)
            
            # Generate metadata
            metadata = self._generate_metadata(formatted_report)
            
            result = {
                'report': formatted_report,
                'metadata': metadata,
                'editing_summary': self._generate_editing_summary(),
                'timestamp': datetime.now().isoformat(),
                'agent': self.name
            }
            
            self.update_status("completed", "Content editing and formatting completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error in content editing: {str(e)}"
            logger.error(error_msg)
            self.update_status("error", error_msg)
            raise AgentError(error_msg) from e
    
    def _extract_sections(self, content: Dict[str, Any]) -> Dict[str, str]:
        """Extract and organize content sections for editing."""
        sections = {}
        
        # Standard report sections
        section_keys = [
            'executive_summary', 'introduction', 'methodology', 
            'findings', 'analysis', 'conclusions', 'recommendations',
            'references', 'appendices'
        ]
        
        for key in section_keys:
            if key in content:
                sections[key] = content[key]
        
        # Handle custom sections
        if 'custom_sections' in content:
            sections.update(content['custom_sections'])
        
        # Ensure we have at least basic content
        if not sections and 'content' in content:
            sections['main_content'] = content['content']
        
        return sections
    
    async def _refine_sections(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Apply editorial refinements to each section."""
        refined_sections = {}
        
        for section_name, content in sections.items():
            self.update_status("processing", f"Refining section: {section_name}")
            
            # Apply section-specific editing
            refined_content = await self._refine_section_content(content, section_name)
            refined_sections[section_name] = refined_content
        
        return refined_sections
    
    async def _refine_section_content(self, content: str, section_type: str) -> str:
        """Refine individual section content."""
        if not content or not content.strip():
            return content
        
        refined_content = content
        
        # Apply grammar and style corrections
        if self.grammar_check_enabled:
            refined_content = self._apply_grammar_corrections(refined_content)
        
        # Improve sentence structure and clarity
        refined_content = self._improve_clarity(refined_content)
        
        # Remove redundancy
        if self.editing_rules.get('remove_redundancy'):
            refined_content = self._remove_redundancy(refined_content)
        
        # Improve transitions between paragraphs
        if self.editing_rules.get('improve_transitions'):
            refined_content = self._improve_transitions(refined_content)
        
        # Optimize paragraph length
        if self.editing_rules.get('optimize_paragraph_length'):
            refined_content = self._optimize_paragraph_length(refined_content)
        
        # Apply section-specific formatting
        refined_content = self._apply_section_formatting(refined_content, section_type)
        
        return refined_content
    
    def _apply_grammar_corrections(self, content: str) -> str:
        """Apply basic grammar and punctuation corrections."""
        # Fix common punctuation issues
        content = re.sub(r'\s+([,.!?;:])', r'\1', content)  # Remove space before punctuation
        content = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', content)  # Ensure space after sentence endings
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        
        # Fix common grammar patterns
        content = re.sub(r'\bi\.e\.\s*', 'i.e., ', content)
        content = re.sub(r'\be\.g\.\s*', 'e.g., ', content)
        content = re.sub(r'\betc\.\s*', 'etc. ', content)
        
        return content.strip()
    
    def _improve_clarity(self, content: str) -> str:
        """Improve sentence clarity and readability."""
        # Split into sentences for processing
        sentences = re.split(r'(?<=[.!?])\s+', content)
        improved_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # Remove unnecessary words
            sentence = re.sub(r'\b(very|quite|rather|somewhat|fairly)\s+', '', sentence)
            sentence = re.sub(r'\b(in order to)\b', 'to', sentence)
            sentence = re.sub(r'\b(due to the fact that)\b', 'because', sentence)
            sentence = re.sub(r'\b(at this point in time)\b', 'now', sentence)
            
            improved_sentences.append(sentence)
        
        return ' '.join(improved_sentences)
    
    def _remove_redundancy(self, content: str) -> str:
        """Remove redundant phrases and repetitive content."""
        paragraphs = content.split('\n\n')
        unique_paragraphs = []
        seen_content = set()
        
        for paragraph in paragraphs:
            # Create a normalized version for comparison
            normalized = re.sub(r'\W+', ' ', paragraph.lower()).strip()
            
            # Skip if we've seen very similar content
            is_duplicate = False
            for seen in seen_content:
                if self._calculate_similarity(normalized, seen) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate and normalized:
                unique_paragraphs.append(paragraph)
                seen_content.add(normalized)
        
        return '\n\n'.join(unique_paragraphs)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _improve_transitions(self, content: str) -> str:
        """Improve transitions between paragraphs."""
        paragraphs = content.split('\n\n')
        if len(paragraphs) <= 1:
            return content
        
        improved_paragraphs = [paragraphs[0]]  # First paragraph unchanged
        
        transition_words = [
            'Furthermore', 'Additionally', 'Moreover', 'However', 'Nevertheless',
            'Consequently', 'Therefore', 'In contrast', 'Similarly', 'Meanwhile'
        ]
        
        for i in range(1, len(paragraphs)):
            paragraph = paragraphs[i].strip()
            if not paragraph:
                continue
            
            # Check if paragraph already has a transition
            first_word = paragraph.split()[0] if paragraph.split() else ''
            
            if first_word not in transition_words and not first_word.endswith(','):
                # Add appropriate transition based on context
                if i == len(paragraphs) - 1:  # Last paragraph
                    paragraph = f"Finally, {paragraph.lower()}"
                elif 'however' in paragraph.lower() or 'but' in paragraph.lower():
                    paragraph = f"However, {paragraph}"
                else:
                    paragraph = f"Additionally, {paragraph}"
            
            improved_paragraphs.append(paragraph)
        
        return '\n\n'.join(improved_paragraphs)
    
    def _optimize_paragraph_length(self, content: str) -> str:
        """Optimize paragraph length for readability."""
        paragraphs = content.split('\n\n')
        optimized_paragraphs = []
        
        for paragraph in paragraphs:
            if len(paragraph) > 500:  # Long paragraph
                # Split into smaller paragraphs at sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                current_para = []
                current_length = 0
                
                for sentence in sentences:
                    if current_length + len(sentence) > 300 and current_para:
                        optimized_paragraphs.append(' '.join(current_para))
                        current_para = [sentence]
                        current_length = len(sentence)
                    else:
                        current_para.append(sentence)
                        current_length += len(sentence)
                
                if current_para:
                    optimized_paragraphs.append(' '.join(current_para))
            else:
                optimized_paragraphs.append(paragraph)
        
        return '\n\n'.join(optimized_paragraphs)
    
    def _apply_section_formatting(self, content: str, section_type: str) -> str:
        """Apply section-specific formatting rules."""
        if section_type == 'executive_summary':
            # Ensure executive summary is concise
            if len(content) > 1000:
                sentences = re.split(r'(?<=[.!?])\s+', content)
                content = ' '.join(sentences[:5])  # Keep first 5 sentences
        
        elif section_type == 'conclusions':
            # Ensure conclusions are clearly structured
            if not content.startswith(('In conclusion', 'To conclude', 'In summary')):
                content = f"In conclusion, {content.lower()}"
        
        elif section_type == 'recommendations':
            # Format recommendations as a list if not already
            if '1.' not in content and '•' not in content:
                sentences = re.split(r'(?<=[.!?])\s+', content)
                if len(sentences) > 1:
                    formatted_recs = []
                    for i, sentence in enumerate(sentences, 1):
                        if sentence.strip():
                            formatted_recs.append(f"{i}. {sentence.strip()}")
                    content = '\n'.join(formatted_recs)
        
        return content
    
    async def _ensure_consistency(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Ensure consistency across all sections."""
        if not self.consistency_check_enabled:
            return sections
        
        # Extract terminology used across sections
        terminology = self._extract_terminology(sections)
        
        # Standardize terminology usage
        consistent_sections = {}
        for section_name, content in sections.items():
            consistent_content = self._standardize_terminology(content, terminology)
            consistent_sections[section_name] = consistent_content
        
        return consistent_sections
    
    def _extract_terminology(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Extract and standardize key terminology."""
        # This is a simplified version - in practice, you might use NLP libraries
        terminology = {}
        
        # Common technical terms that should be consistent
        all_text = ' '.join(sections.values()).lower()
        
        # Extract potential key terms (simplified approach)
        words = re.findall(r'\b[a-z]{4,}\b', all_text)
        word_counts = {}
        
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Keep frequently used terms
        for word, count in word_counts.items():
            if count >= 3:  # Appears at least 3 times
                terminology[word] = word  # In practice, you'd apply standardization rules
        
        return terminology
    
    def _standardize_terminology(self, content: str, terminology: Dict[str, str]) -> str:
        """Apply terminology standardization to content."""
        standardized_content = content
        
        for original, standard in terminology.items():
            if original != standard:
                # Replace with word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(original) + r'\b'
                standardized_content = re.sub(pattern, standard, standardized_content, flags=re.IGNORECASE)
        
        return standardized_content
    
    async def _format_report(self, sections: Dict[str, str]) -> str:
        """Format the final report according to output specifications."""
        if self.output_format == 'markdown':
            return self._format_markdown_report(sections)
        elif self.output_format == 'html':
            return self._format_html_report(sections)
        else:
            return self._format_plain_text_report(sections)
    
    def _format_markdown_report(self, sections: Dict[str, str]) -> str:
        """Format report as Markdown."""
        formatted_sections = []
        
        # Define section order and headers
        section_headers = {
            'executive_summary': '# Executive Summary',
            'introduction': '# Introduction',
            'methodology': '# Methodology',
            'findings': '# Key Findings',
            'analysis': '# Analysis',
            'conclusions': '# Conclusions',
            'recommendations': '# Recommendations',
            'references': '# References',
            'appendices': '# Appendices'
        }
        
        # Add title and metadata
        formatted_sections.append(f"# Research Report")
        formatted_sections.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Add sections in order
        for section_name in section_headers.keys():
            if section_name in sections and sections[section_name].strip():
                formatted_sections.append(section_headers[section_name])
                formatted_sections.append(sections[section_name])
                formatted_sections.append("")  # Add spacing
        
        # Add any custom sections
        for section_name, content in sections.items():
            if section_name not in section_headers and content.strip():
                header = f"# {section_name.replace('_', ' ').title()}"
                formatted_sections.append(header)
                formatted_sections.append(content)
                formatted_sections.append("")
        
        return '\n'.join(formatted_sections)
    
    def _format_html_report(self, sections: Dict[str, str]) -> str:
        """Format report as HTML."""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Research Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; border-bottom: 2px solid #333; }",
            "h2 { color: #666; }",
            "p { line-height: 1.6; }",
            "</style>",
            "</head>",
            "<body>"
        ]
        
        html_parts.append("<h1>Research Report</h1>")
        html_parts.append(f"<p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>")
        
        section_headers = {
            'executive_summary': 'Executive Summary',
            'introduction': 'Introduction',
            'methodology': 'Methodology',
            'findings': 'Key Findings',
            'analysis': 'Analysis',
            'conclusions': 'Conclusions',
            'recommendations': 'Recommendations',
            'references': 'References'
        }
        
        for section_name, header in section_headers.items():
            if section_name in sections and sections[section_name].strip():
                html_parts.append(f"<h2>{header}</h2>")
                # Convert paragraphs to HTML
                paragraphs = sections[section_name].split('\n\n')
                for paragraph in paragraphs:
                    if paragraph.strip():
                        html_parts.append(f"<p>{paragraph.strip()}</p>")
        
        html_parts.extend(["</body>", "</html>"])
        return '\n'.join(html_parts)
    
    def _format_plain_text_report(self, sections: Dict[str, str]) -> str:
        """Format report as plain text."""
        text_parts = []
        
        text_parts.append("RESEARCH REPORT")
        text_parts.append("=" * 50)
        text_parts.append(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        text_parts.append("")
        
        section_headers = {
            'executive_summary': 'EXECUTIVE SUMMARY',
            'introduction': 'INTRODUCTION',
            'methodology': 'METHODOLOGY',
            'findings': 'KEY FINDINGS',
            'analysis': 'ANALYSIS',
            'conclusions': 'CONCLUSIONS',
            'recommendations': 'RECOMMENDATIONS',
            'references': 'REFERENCES'
        }
        
        for section_name, header in section_headers.items():
            if section_name in sections and sections[section_name].strip():
                text_parts.append(header)
                text_parts.append("-" * len(header))
                text_parts.append(sections[section_name])
                text_parts.append("")
        
        return '\n'.join(text_parts)
    
    def _generate_metadata(self, report: str) -> Dict[str, Any]:
        """Generate metadata for the formatted report."""
        word_count = len(report.split())
        char_count = len(report)
        
        # Estimate reading time (average 200 words per minute)
        reading_time = max(1, word_count // 200)
        
        return {
            'word_count': word_count,
            'character_count': char_count,
            'estimated_reading_time_minutes': reading_time,
            'format': self.output_format,
            'style_guide': self.style_guide,
            'editing_rules_applied': list(self.editing_rules.keys()),
            'generated_timestamp': datetime.now().isoformat()
        }
    
    def _generate_editing_summary(self) -> Dict[str, Any]:
        """Generate summary of editing actions performed."""
        return {
            'grammar_check_applied': self.grammar_check_enabled,
            'consistency_check_applied': self.consistency_check_enabled,
            'redundancy_removal': self.editing_rules.get('remove_redundancy', False),
            'transition_improvement': self.editing_rules.get('improve_transitions', False),
            'paragraph_optimization': self.editing_rules.get('optimize_paragraph_length', False),
            'style_guide_used': self.style_guide,
            'output_format': self.output_format
        }
    
    async def refine_specific_section(self, section_content: str, section_type: str) -> str:
        """
        Refine a specific section independently.
        
        Args:
            section_content: Content of the section to refine
            section_type: Type of section (e.g., 'introduction', 'conclusions')
            
        Returns:
            Refined section content
        """
        try:
            self.update_status("processing", f"Refining {section_type} section")
            refined_content = await self._refine_section_content(section_content, section_type)
            return refined_content
        except Exception as e:
            logger.error(f"Error refining section {section_type}: {str(e)}")
            return section_content  # Return original if refinement fails
    
    def validate_report_structure(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate the structure and completeness of the report.
        
        Args:
            sections: Dictionary of report sections
            
        Returns:
            Validation results with recommendations
        """
        validation_results = {
            'is_valid': True,
            'missing_sections': [],
            'recommendations': [],
            'section_lengths': {}
        }
        
        # Check for essential sections
        essential_sections = ['introduction', 'findings', 'conclusions']
        for section in essential_sections:
            if section not in sections or not sections[section].strip():
                validation_results['missing_sections'].append(section)
                validation_results['is_valid'] = False
        
        # Check section lengths
        for section_name, content in sections.items():
            length = len(content.split())
            validation_results['section_lengths'][section_name] = length
            
            if length < 50:  # Very short section
                validation_results['recommendations'].append(
                    f"Section '{section_name}' is quite short ({length} words). Consider expanding."
                )
            elif length > self.max_section_length:  # Very long section
                validation_results['recommendations'].append(
                    f"Section '{section_name}'