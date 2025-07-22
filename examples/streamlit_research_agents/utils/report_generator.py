import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import markdown
from jinja2 import Template, Environment, FileSystemLoader
import pdfkit
from weasyprint import HTML, CSS
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Utility class for generating formatted technical reports in multiple formats."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the report generator.
        
        Args:
            template_dir: Directory containing report templates
        """
        self.template_dir = template_dir or os.path.join(os.path.dirname(__file__), 'templates')
        self.ensure_template_dir()
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )
        
    def ensure_template_dir(self):
        """Ensure template directory exists and create default templates if needed."""
        Path(self.template_dir).mkdir(parents=True, exist_ok=True)
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default report templates."""
        templates = {
            'markdown_report.md': self._get_markdown_template(),
            'html_report.html': self._get_html_template(),
            'pdf_styles.css': self._get_pdf_styles()
        }
        
        for filename, content in templates.items():
            template_path = os.path.join(self.template_dir, filename)
            if not os.path.exists(template_path):
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def generate_report(
        self,
        data: Dict[str, Any],
        format_type: str = 'markdown',
        output_path: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> str:
        """
        Generate a formatted report from research data.
        
        Args:
            data: Research data dictionary
            format_type: Output format ('markdown', 'html', 'pdf')
            output_path: Path to save the report
            template_name: Custom template name to use
            
        Returns:
            Generated report content or file path
        """
        try:
            if format_type == 'markdown':
                return self._generate_markdown_report(data, output_path, template_name)
            elif format_type == 'html':
                return self._generate_html_report(data, output_path, template_name)
            elif format_type == 'pdf':
                return self._generate_pdf_report(data, output_path, template_name)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
                
        except Exception as e:
            logger.error(f"Error generating {format_type} report: {str(e)}")
            raise
    
    def _generate_markdown_report(
        self,
        data: Dict[str, Any],
        output_path: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> str:
        """Generate a Markdown report."""
        template_name = template_name or 'markdown_report.md'
        
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception:
            # Fallback to default template content
            template = Template(self._get_markdown_template())
        
        # Prepare data for template
        template_data = self._prepare_template_data(data)
        
        # Render the template
        content = template.render(**template_data)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return output_path
        
        return content
    
    def _generate_html_report(
        self,
        data: Dict[str, Any],
        output_path: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> str:
        """Generate an HTML report."""
        template_name = template_name or 'html_report.html'
        
        try:
            template = self.jinja_env.get_template(template_name)
        except Exception:
            # Fallback to default template content
            template = Template(self._get_html_template())
        
        # Prepare data for template
        template_data = self._prepare_template_data(data)
        
        # Render the template
        content = template.render(**template_data)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return output_path
        
        return content
    
    def _generate_pdf_report(
        self,
        data: Dict[str, Any],
        output_path: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> str:
        """Generate a PDF report."""
        # First generate HTML content
        html_content = self._generate_html_report(data, template_name=template_name)
        
        if not output_path:
            output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        try:
            # Use WeasyPrint for better CSS support
            css_path = os.path.join(self.template_dir, 'pdf_styles.css')
            css = CSS(filename=css_path) if os.path.exists(css_path) else None
            
            HTML(string=html_content).write_pdf(output_path, stylesheets=[css] if css else None)
            
        except Exception as e:
            logger.warning(f"WeasyPrint failed: {e}. Trying pdfkit...")
            
            try:
                # Fallback to pdfkit
                options = {
                    'page-size': 'A4',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': "UTF-8",
                    'no-outline': None
                }
                pdfkit.from_string(html_content, output_path, options=options)
                
            except Exception as e2:
                logger.error(f"Both PDF generation methods failed: {e2}")
                raise
        
        return output_path
    
    def _prepare_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and structure data for template rendering."""
        template_data = {
            'title': data.get('title', 'Research Report'),
            'subtitle': data.get('subtitle', ''),
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'executive_summary': data.get('executive_summary', ''),
            'research_question': data.get('research_question', ''),
            'methodology': data.get('methodology', ''),
            'findings': data.get('findings', []),
            'conclusions': data.get('conclusions', ''),
            'recommendations': data.get('recommendations', []),
            'sources': data.get('sources', []),
            'appendices': data.get('appendices', []),
            'metadata': data.get('metadata', {}),
            'agents_used': data.get('agents_used', []),
            'processing_time': data.get('processing_time', 'N/A')
        }
        
        # Format findings if they're in a different structure
        if isinstance(template_data['findings'], dict):
            template_data['findings'] = [
                {'title': k, 'content': v} for k, v in template_data['findings'].items()
            ]
        
        return template_data
    
    def _get_markdown_template(self) -> str:
        """Get the default Markdown template."""
        return """# {{ title }}
{% if subtitle %}
## {{ subtitle }}
{% endif %}

**Generated:** {{ generated_date }}
{% if processing_time %}
**Processing Time:** {{ processing_time }}
{% endif %}

---

## Executive Summary

{{ executive_summary }}

## Research Question

{{ research_question }}

## Methodology

{{ methodology }}

## Key Findings

{% for finding in findings %}
### {{ finding.title if finding.title else "Finding " + loop.index|string }}

{{ finding.content }}

{% endfor %}

## Conclusions

{{ conclusions }}

## Recommendations

{% for recommendation in recommendations %}
- {{ recommendation }}
{% endfor %}

## Sources

{% for source in sources %}
- {{ source }}
{% endfor %}

{% if appendices %}
## Appendices

{% for appendix in appendices %}
### {{ appendix.title }}

{{ appendix.content }}

{% endfor %}
{% endif %}

---

{% if agents_used %}
*This report was generated using the following AI agents: {{ agents_used|join(', ') }}*
{% endif %}
"""
    
    def _get_html_template(self) -> str:
        """Get the default HTML template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        h3 {
            color: #7f8c8d;
        }
        .metadata {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .finding {
            background-color: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #3498db;
            border-radius: 0 5px 5px 0;
        }
        .recommendations {
            background-color: #e8f5e8;
            padding: 20px;
            border-radius: 5px;
        }
        .sources {
            background-color: #fff3cd;
            padding: 20px;
            border-radius: 5px;
        }
        ul {
            padding-left: 20px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #bdc3c7;
            font-style: italic;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        {% if subtitle %}
        <h2>{{ subtitle }}</h2>
        {% endif %}
        
        <div class="metadata">
            <strong>Generated:</strong> {{ generated_date }}<br>
            {% if processing_time %}
            <strong>Processing Time:</strong> {{ processing_time }}<br>
            {% endif %}
            {% if agents_used %}
            <strong>AI Agents Used:</strong> {{ agents_used|join(', ') }}
            {% endif %}
        </div>

        <h2>Executive Summary</h2>
        <p>{{ executive_summary }}</p>

        <h2>Research Question</h2>
        <p>{{ research_question }}</p>

        <h2>Methodology</h2>
        <p>{{ methodology }}</p>

        <h2>Key Findings</h2>
        {% for finding in findings %}
        <div class="finding">
            <h3>{{ finding.title if finding.title else "Finding " + loop.index|string }}</h3>
            <p>{{ finding.content }}</p>
        </div>
        {% endfor %}

        <h2>Conclusions</h2>
        <p>{{ conclusions }}</p>

        {% if recommendations %}
        <h2>Recommendations</h2>
        <div class="recommendations">
            <ul>
            {% for recommendation in recommendations %}
                <li>{{ recommendation }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}

        {% if sources %}
        <h2>Sources</h2>
        <div class="sources">
            <ul>
            {% for source in sources %}
                <li>{{ source }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}

        {% if appendices %}
        <h2>Appendices</h2>
        {% for appendix in appendices %}
        <h3>{{ appendix.title }}</h3>
        <p>{{ appendix.content }}</p>
        {% endfor %}
        {% endif %}

        {% if agents_used %}
        <div class="footer">
            This report was generated using AI agents: {{ agents_used|join(', ') }}
        </div>
        {% endif %}
    </div>
</body>
</html>"""
    
    def _get_pdf_styles(self) -> str:
        """Get the default PDF CSS styles."""
        return """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: 'Times New Roman', serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #000;
}

h1 {
    font-size: 18pt;
    font-weight: bold;
    margin-bottom: 20pt;
    page-break-after: avoid;
}

h2 {
    font-size: 14pt;
    font-weight: bold;
    margin-top: 20pt;
    margin-bottom: 10pt;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    font-weight: bold;
    margin-top: 15pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
}

p {
    margin-bottom: 10pt;
    text-align: justify;
}

ul, ol {
    margin-bottom: 10pt;
    padding-left: 20pt;
}

.metadata {
    background-color: #f0f0f0;
    padding: 10pt;
    margin-bottom: 20pt;
    border: 1pt solid #ccc;
}

.finding {
    margin: 15pt 0;
    padding: 10pt;
    border-left: 3pt solid #333;
    background-color: #f9f9f9;
}

.page-break {
    page-break-before: always;
}
"""

def create_sample_report_data() -> Dict[str, Any]:
    """Create sample data for testing report generation."""
    return {
        'title': 'AI Research Report',
        'subtitle': 'Multi-Agent Collaboration Analysis',
        'research_question': 'How can multi-agent systems improve research efficiency?',
        'executive_summary': 'This report analyzes the effectiveness of multi-agent systems in conducting complex research tasks.',
        'methodology': 'We employed three specialized AI agents to conduct comprehensive research using the Perplexity API.',
        'findings': [
            {
                'title': 'Improved Efficiency',
                'content': 'Multi-agent systems showed 40% improvement in research task completion time.'
            },
            {
                'title': 'Enhanced Quality',
                'content': 'Collaborative agents produced more comprehensive and accurate results.'
            }
        ],
        'conclusions': 'Multi-agent systems represent a significant advancement in automated research capabilities.',
        'recommendations': [
            'Implement multi-agent systems for complex research tasks',
            'Develop specialized agents for different research domains',
            'Establish clear coordination protocols between agents'
        ],
        'sources': [
            'Academic papers on multi-agent systems',
            'Industry reports on AI collaboration',
            'Experimental data from agent interactions'
        ],
        'agents_used': ['Research Coordinator', 'Search Agent', 'Synthesis Agent', 'Editing Agent'],
        'processing_time': '5 minutes 32 seconds'
    }