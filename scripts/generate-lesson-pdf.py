#!/usr/bin/env python3
"""
PDF Generation Script for Lesson Documentation

This script converts Markdown lesson files to PDF format using weasyprint.
It processes individual lesson files or entire lesson directories with proper
formatting, styling, and navigation.

Requirements:
    pip install weasyprint markdown beautifulsoup4 pygments

Usage:
    python scripts/generate-lesson-pdf.py
    python scripts/generate-lesson-pdf.py --lesson lesson-01-github-mcp-streamlit
    python scripts/generate-lesson-pdf.py --output custom-output-dir
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LessonPDFGenerator:
    """Generate PDF documents from Markdown lesson files."""
    
    def __init__(self, lessons_dir: str = "lessons", output_dir: str = "lessons/pdf"):
        self.lessons_dir = Path(lessons_dir)
        self.output_dir = Path(output_dir)
        self.font_config = FontConfiguration()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Markdown extensions for better formatting
        self.md_extensions = [
            'codehilite',
            'fenced_code',
            'tables',
            'toc',
            'attr_list',
            'def_list',
            'footnotes',
            'md_in_html'
        ]
        
        # CSS styling for PDF
        self.css_content = """
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "BMasterAI Lessons";
                font-family: Arial, sans-serif;
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-family: Arial, sans-serif;
                font-size: 10pt;
                color: #666;
            }
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 11pt;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
            margin-bottom: 20px;
            font-size: 24pt;
            page-break-before: auto;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 18pt;
        }
        
        h3 {
            color: #2c3e50;
            margin-top: 20px;
            margin-bottom: 12px;
            font-size: 14pt;
        }
        
        h4, h5, h6 {
            color: #34495e;
            margin-top: 15px;
            margin-bottom: 10px;
            font-size: 12pt;
        }
        
        p {
            margin-bottom: 12px;
            text-align: justify;
        }
        
        code {
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
            color: #e74c3c;
        }
        
        pre {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
            overflow-x: auto;
            page-break-inside: avoid;
        }
        
        pre code {
            background-color: transparent;
            padding: 0;
            color: #333;
            font-size: 9pt;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding: 10px 20px;
            background-color: #f8f9fa;
            font-style: italic;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            page-break-inside: avoid;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        
        ul, ol {
            margin: 10px 0;
            padding-left: 25px;
        }
        
        li {
            margin-bottom: 5px;
        }
        
        .toc {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc li {
            margin-bottom: 8px;
        }
        
        .toc a {
            text-decoration: none;
            color: #3498db;
        }
        
        .highlight {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .note {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .warning {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .page-break {
            page-break-before: always;
        }
        
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 15px auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        
        .codehilite {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
            overflow-x: auto;
        }
        """

    def process_markdown_content(self, content: str, base_path: Path) -> str:
        """Process markdown content and convert to HTML with enhancements."""
        try:
            # Convert markdown to HTML
            md = markdown.Markdown(extensions=self.md_extensions)
            html_content = md.convert(content)
            
            # Parse with BeautifulSoup for post-processing
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Add custom classes for special content
            self._enhance_content_blocks(soup)
            
            # Fix relative image paths
            self._fix_image_paths(soup, base_path)
            
            # Add page breaks before major sections
            self._add_page_breaks(soup)
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Error processing markdown content: {e}")
            raise

    def _enhance_content_blocks(self, soup: BeautifulSoup) -> None:
        """Add custom styling classes to content blocks."""
        # Enhance blockquotes with special classes
        for blockquote in soup.find_all('blockquote'):
            text = blockquote.get_text().lower()
            if 'note:' in text or 'info:' in text:
                blockquote['class'] = blockquote.get('class', []) + ['note']
            elif 'warning:' in text or 'caution:' in text:
                blockquote['class'] = blockquote.get('class', []) + ['warning']
            elif 'highlight:' in text or 'important:' in text:
                blockquote['class'] = blockquote.get('class', []) + ['highlight']

    def _fix_image_paths(self, soup: BeautifulSoup, base_path: Path) -> None:
        """Convert relative image paths to absolute paths."""
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith(('http://', 'https://', 'data:')):
                # Convert relative path to absolute
                img_path = base_path / src
                if img_path.exists():
                    img['src'] = f"file://{img_path.absolute()}"
                else:
                    logger.warning(f"Image not found: {img_path}")

    def _add_page_breaks(self, soup: BeautifulSoup) -> None:
        """Add page breaks before major sections."""
        h1_tags = soup.find_all('h1')
        for i, h1 in enumerate(h1_tags):
            if i > 0:  # Don't add page break before first h1
                h1['class'] = h1.get('class', []) + ['page-break']

    def create_html_document(self, title: str, content: str) -> str:
        """Create complete HTML document with proper structure."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                {self.css_content}
            </style>
        </head>
        <body>
            <div class="document">
                {content}
            </div>
        </body>
        </html>
        """

    def generate_lesson_pdf(self, lesson_path: Path, output_name: Optional[str] = None) -> Path:
        """Generate PDF for a single lesson."""
        try:
            logger.info(f"Processing lesson: {lesson_path}")
            
            # Read markdown content
            readme_path = lesson_path / "README.md"
            if not readme_path.exists():
                raise FileNotFoundError(f"README.md not found in {lesson_path}")
            
            with open(readme_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Process markdown to HTML
            html_content = self.process_markdown_content(markdown_content, lesson_path)
            
            # Create complete HTML document
            title = f"BMasterAI Lesson: {lesson_path.name}"
            full_html = self.create_html_document(title, html_content)
            
            # Generate output filename
            if not output_name:
                output_name = f"{lesson_path.name}.pdf"
            
            output_path = self.output_dir / output_name
            
            # Generate PDF
            logger.info(f"Generating PDF: {output_path}")
            html_doc = HTML(string=full_html, base_url=str(lesson_path))
            css_doc = CSS(string=self.css_content, font_config=self.font_config)
            
            html_doc.write_pdf(
                output_path,
                stylesheets=[css_doc],
                font_config=self.font_config
            )
            
            logger.info(f"PDF generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PDF for {lesson_path}: {e}")
            raise

    def generate_combined_pdf(self, lesson_paths: List[Path], output_name: str = "all-lessons.pdf") -> Path:
        """Generate a combined PDF from multiple lessons."""
        try:
            logger.info("Generating combined PDF from multiple lessons")
            
            combined_content = []
            
            for lesson_path in lesson_paths:
                readme_path = lesson_path / "README.md"
                if not readme_path.exists():
                    logger.warning(f"Skipping {lesson_path}: README.md not found")
                    continue
                
                logger.info(f"Adding lesson to combined PDF: {lesson_path}")
                
                with open(readme_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                
                # Add lesson title and page break
                lesson_title = f"# {lesson_path.name.replace('-', ' ').title()}\n\n"
                full_content = lesson_title + markdown_content
                
                html_content = self.process_markdown_content(full_content, lesson_path)
                combined_content.append(html_content)
            
            if not combined_content:
                raise ValueError("No valid lessons found to combine")
            
            # Join all content
            full_html_content = '<div class="page-break"></div>'.join(combined_content)
            
            # Create complete HTML document
            title = "BMasterAI Complete Lessons Guide"
            full_html = self.create_html_document(title, full_html_content)
            
            # Generate PDF
            output_path = self.output_dir / output_name
            logger.info(f"Generating combined PDF: {output_path}")
            
            html_doc = HTML(string=full_html, base_url=str(self.lessons_dir))
            css_doc = CSS(string=self.css_content, font_config=self.font_config)
            
            html_doc.write_pdf(
                output_path,
                stylesheets=[css_doc],
                font_config=self.font_config
            )
            
            logger.info(f"Combined PDF generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating combined PDF: {e}")
            raise

    def find_lesson_directories(self) -> List[Path]:
        """Find all lesson directories in the lessons folder."""
        lesson_dirs = []
        
        if not self.lessons_dir.exists():
            logger.warning(f"Lessons directory not found: {self.lessons_dir}")
            return lesson_dirs
        
        for item in self.lessons_dir.iterdir():
            if item.is_dir() and item.name.startswith('lesson-'):
                readme_path = item / "README.md"
                if readme_path.exists():
                    lesson_dirs.append(item)
                else:
                    logger.warning(f"Skipping {item}: no README.md found")
        
        return sorted(lesson_dirs)

    def generate_all_lessons(self) -> List[Path]:
        """Generate PDFs for all lessons."""
        lesson_dirs = self.find_lesson_directories()
        
        if not lesson_dirs:
            logger.warning("No lesson directories found")
            return []
        
        generated_pdfs = []
        
        # Generate individual lesson PDFs
        for lesson_dir in lesson_dirs:
            try:
                pdf_path = self.generate_lesson_pdf(lesson_dir)
                generated_pdfs.append(pdf_path)
            except Exception as e:
                logger.error(f"Failed to generate PDF for {lesson_dir}: {e}")
        
        # Generate combined PDF
        if lesson_dirs:
            try:
                combined_pdf = self.generate_combined_pdf(lesson_dirs)
                generated_pdfs.append(combined_pdf)
            except Exception as e:
                logger.error(f"Failed to generate combined PDF: {e}")
        
        return generated_pdfs


def main():
    """Main function to handle command line arguments and execute PDF generation."""
    parser = argparse.ArgumentParser(
        description="Generate PDF versions of Markdown lessons",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate-lesson-pdf.py
  python scripts/generate-lesson-pdf.py --lesson lesson-01-github-mcp-streamlit
  python scripts/generate-lesson-pdf.py --output custom-output --combined-only
        """
    )
    
    parser.add_argument(
        '--lesson',
        type=str,
        help='Specific lesson directory name to process'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='lessons/pdf',
        help='Output directory for PDF files (default: lessons/pdf)'
    )
    
    parser.add_argument(
        '--lessons-dir',
        type=str,
        default='lessons',
        help='Lessons source directory (default: lessons)'
    )
    
    parser.add_argument(
        '--combined-only',
        action='store_true',
        help='Generate only combined PDF, skip individual lesson PDFs'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize PDF generator
        generator = LessonPDFGenerator(
            lessons_dir=args.lessons_dir,
            output_dir=args.output
        )
        
        generated_files = []
        
        if args.lesson:
            # Generate PDF for specific lesson
            lesson_path = Path(args.lessons_dir) / args.lesson
            if not lesson_path.exists():
                logger.error(f"Lesson directory not found: {lesson_path}")
                sys.exit(1)
            
            pdf_path = generator.generate_lesson_pdf(lesson_path)
            generated_files.append(pdf_path)
            
        elif args.combined_only:
            # Generate only combined PDF
            lesson_dirs = generator.find_lesson_directories()
            if lesson_dirs:
                combined_pdf = generator.generate_combined_pdf(lesson_dirs)
                generated_files.append(combined_pdf)
            else:
                logger.error("No lesson directories found")
                sys.exit(1)
                
        else:
            # Generate all lesson PDFs
            generated_files = generator.generate_all_lessons()
        
        # Summary
        if generated_files:
            logger.info(f"\nSuccessfully generated {len(generated_files)} PDF file(s):")
            for pdf_file in generated_files:
                logger.info(f"  - {pdf_file}")
        else:
            logger.warning("No PDF files were generated")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("PDF generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()