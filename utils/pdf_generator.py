import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import logging
from typing import List, Dict, Any

class ColorCodedPDFGenerator:
    """Generates color-coded PDF reports for legal document analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define colors for different clause types
        self.colors = {
            'harmful': HexColor('#ffebee'),    # Light red background
            'warning': HexColor('#fff3e0'),    # Light orange background
            'good': HexColor('#e8f5e8'),       # Light green background
            'neutral': HexColor('#f5f5f5'),    # Light gray background
        }
        
        # Text colors for better visibility
        self.text_colors = {
            'harmful': HexColor('#d32f2f'),    # Red text
            'warning': HexColor('#f57c00'),    # Orange text
            'good': HexColor('#388e3c'),       # Green text
            'neutral': HexColor('#424242'),    # Dark gray text
        }
    
    def generate_highlighted_document(self, original_text: str, analysis_data: Dict[str, Any], 
                                    entities: Dict, filename: str) -> str:
        """
        Generate a PDF that looks like the original document but with color-coded highlights.
        
        Args:
            original_text (str): Original document text
            analysis_data (dict): Analysis results from Gemini
            entities (dict): Extracted entities
            filename (str): Original filename
            
        Returns:
            str: Path to generated highlighted PDF file
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = 'reports'
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate unique filename
            import uuid
            pdf_filename = f"highlighted_{uuid.uuid4().hex[:8]}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            # Create PDF document with similar layout to original
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Build document content - just the highlighted text
            story = []
            styles = getSampleStyleSheet()
            
            # Add a simple title with the filename
            title_style = ParagraphStyle(
                'SimpleTitle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=HexColor('#333333'),
                alignment=TA_CENTER,
                spaceAfter=20,
                fontName='Helvetica-Bold'
            )
            
            clean_filename = filename.replace('_', ' ').replace('.pdf', '').replace('.txt', '')
            story.append(Paragraph(clean_filename, title_style))
            story.append(Spacer(1, 20))
            
            # Add the highlighted original text (main content)
            self._add_simple_highlighted_text(story, styles, original_text, analysis_data.get('clauses', []))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"Generated highlighted document: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}")
            raise Exception(f"Failed to generate highlighted PDF: {str(e)}")

    def generate_analysis_report(self, original_text: str, analysis_data: Dict[str, Any], 
                               entities: Dict, filename: str) -> str:
        """
        Generate a color-coded PDF report of the document analysis.
        
        Args:
            original_text (str): Original document text
            analysis_data (dict): Analysis results from Gemini
            entities (dict): Extracted entities
            filename (str): Original filename
            
        Returns:
            str: Path to generated PDF file
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = 'reports'
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate unique filename
            import uuid
            pdf_filename = f"analysis_{uuid.uuid4().hex[:8]}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            # Build document content
            story = []
            styles = getSampleStyleSheet()
            
            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=HexColor('#1976d2'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            story.append(Paragraph("Legal Document Analysis Report", title_style))
            story.append(Spacer(1, 20))
            
            # Add document info
            self._add_document_info(story, styles, filename, analysis_data)
            
            # Add risk assessment
            self._add_risk_assessment(story, styles, analysis_data.get('risk_assessment', {}))
            
            # Add summary
            self._add_summary(story, styles, analysis_data.get('summary', ''))
            
            # Add entities
            self._add_entities_section(story, styles, entities)
            
            # Add color-coded clause analysis
            self._add_clause_analysis(story, styles, analysis_data.get('clauses', []))
            
            # Add original text with highlighting
            self._add_highlighted_text(story, styles, original_text, analysis_data.get('clauses', []))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"Generated analysis report: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}")
            raise Exception(f"Failed to generate PDF report: {str(e)}")
    
    def _add_document_info(self, story: List, styles, filename: str, analysis_data: Dict):
        """Add document information section."""
        story.append(Paragraph("Document Information", styles['Heading2']))
        
        info_data = [
            ['Original File:', filename],
            ['Analysis Date:', self._get_current_date()],
            ['Total Clauses Analyzed:', str(len(analysis_data.get('clauses', [])))]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc'))
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
    
    def _add_risk_assessment(self, story: List, styles, risk_data: Dict):
        """Add risk assessment section."""
        story.append(Paragraph("Risk Assessment", styles['Heading2']))
        
        risk_level = risk_data.get('level', 'unknown').upper()
        risk_description = risk_data.get('description', 'No assessment available')
        
        # Color code risk level
        risk_color = HexColor('#d32f2f')  # Red for high
        if risk_level == 'MEDIUM':
            risk_color = HexColor('#f57c00')  # Orange
        elif risk_level == 'LOW':
            risk_color = HexColor('#388e3c')  # Green
        
        risk_style = ParagraphStyle(
            'RiskLevel',
            parent=styles['Normal'],
            fontSize=14,
            textColor=risk_color,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph(f"Risk Level: {risk_level}", risk_style))
        story.append(Paragraph(risk_description, styles['Normal']))
        story.append(Spacer(1, 20))
    
    def _add_summary(self, story: List, styles, summary: str):
        """Add summary section."""
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        
        # Format summary paragraphs
        paragraphs = summary.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), styles['Normal']))
                story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))
    
    def _add_entities_section(self, story: List, styles, entities: Dict):
        """Add entities section."""
        if not entities:
            return
            
        story.append(Paragraph("Key Entities Identified", styles['Heading2']))
        
        for entity_type, entity_list in entities.items():
            if entity_list:
                entity_name = entity_type.replace('_', ' ').title()
                story.append(Paragraph(f"{entity_name}:", styles['Heading3']))
                
                # Create bullet list of entities
                for entity in entity_list[:5]:  # Show top 5
                    entity_text = entity.get('text', str(entity))
                    confidence = entity.get('confidence', 1.0)
                    story.append(Paragraph(f"• {entity_text} ({int(confidence*100)}%)", styles['Normal']))
                
                story.append(Spacer(1, 10))
        
        story.append(Spacer(1, 20))
    
    def _add_clause_analysis(self, story: List, styles, clauses: List[Dict]):
        """Add clause analysis section with color coding."""
        story.append(Paragraph("Clause Analysis", styles['Heading2']))
        
        # Create legend
        story.append(Paragraph("Color Legend:", styles['Heading3']))
        legend_data = [
            ['🔴 Harmful', 'Potentially disadvantageous or unfair clauses'],
            ['🟡 Warning', 'Clauses requiring careful attention and review'],
            ['🟢 Good', 'Beneficial or standard good practice clauses'],
            ['⚪ Neutral', 'Standard clauses with no particular risk']
        ]
        
        legend_table = Table(legend_data, colWidths=[1.5*inch, 4*inch])
        legend_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(legend_table)
        story.append(Spacer(1, 20))
        
        # Add individual clause analysis
        for i, clause in enumerate(clauses, 1):
            classification = clause.get('classification', 'neutral')
            text = clause.get('text', '')
            reasoning = clause.get('reasoning', '')
            confidence = clause.get('confidence', 0.0)
            
            # Create colored box for clause
            clause_style = ParagraphStyle(
                f'Clause{i}',
                parent=styles['Normal'],
                backColor=self.colors.get(classification, self.colors['neutral']),
                textColor=self.text_colors.get(classification, self.text_colors['neutral']),
                borderColor=self.text_colors.get(classification, self.text_colors['neutral']),
                borderWidth=1,
                leftIndent=10,
                rightIndent=10,
                spaceBefore=6,
                spaceAfter=6,
                borderPadding=8
            )
            
            # Emoji mapping
            emoji_map = {
                'harmful': '🔴',
                'warning': '🟡', 
                'good': '🟢',
                'neutral': '⚪'
            }
            
            emoji = emoji_map.get(classification, '⚪')
            
            story.append(Paragraph(f"{emoji} Clause {i} ({classification.title()} - {int(confidence*100)}%)", styles['Heading4']))
            story.append(Paragraph(f"<b>Text:</b> {text[:500]}{'...' if len(text) > 500 else ''}", clause_style))
            
            if reasoning:
                story.append(Paragraph(f"<b>Analysis:</b> {reasoning}", styles['Normal']))
            
            story.append(Spacer(1, 10))
    
    def _add_highlighted_text(self, story: List, styles, original_text: str, clauses: List[Dict]):
        """Add original text with highlighted sections."""
        story.append(PageBreak())
        story.append(Paragraph("Original Document with Highlights", styles['Heading2']))
        
        if not clauses:
            # If no clause analysis, just show original text
            story.append(Paragraph(original_text, styles['Normal']))
            return
        
        # Sort clauses by start position
        sorted_clauses = sorted(clauses, key=lambda x: x.get('start_pos', 0))
        
        # Create highlighted text
        highlighted_parts = []
        last_pos = 0
        
        for clause in sorted_clauses:
            start_pos = clause.get('start_pos', 0)
            end_pos = clause.get('end_pos', 0)
            classification = clause.get('classification', 'neutral')
            
            # Add text before this clause
            if start_pos > last_pos:
                before_text = original_text[last_pos:start_pos]
                if before_text.strip():
                    highlighted_parts.append(before_text)
            
            # Add highlighted clause
            clause_text = original_text[start_pos:end_pos] if end_pos > start_pos else clause.get('text', '')
            if clause_text.strip():
                color = self.text_colors.get(classification, self.text_colors['neutral']).hexval()
                highlighted_parts.append(f'<font color="{color}"><b>{clause_text}</b></font>')
            
            last_pos = max(end_pos, last_pos)
        
        # Add remaining text
        if last_pos < len(original_text):
            remaining_text = original_text[last_pos:]
            if remaining_text.strip():
                highlighted_parts.append(remaining_text)
        
        # Create final highlighted text
        highlighted_text = ''.join(highlighted_parts)
        
        # Split into manageable chunks
        text_style = ParagraphStyle(
            'HighlightedText',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # Split text into smaller paragraphs to avoid reportlab issues
        chunks = self._split_text_into_chunks(highlighted_text, 2000)
        for chunk in chunks:
            if chunk.strip():
                story.append(Paragraph(chunk, text_style))
                story.append(Spacer(1, 6))
    
    def _split_text_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Split text into smaller chunks for PDF processing."""
        chunks = []
        words = text.split(' ')
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _add_simple_highlighted_text(self, story: List, styles, original_text: str, clauses: List[Dict]):
        """Add original text with simple color highlights - no analysis sections."""
        
        # Document-like text style
        text_style = ParagraphStyle(
            'DocumentText',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceBefore=4,
            spaceAfter=4
        )
        
        if not clauses or len(clauses) == 0:
            # If no clause analysis, add basic pattern-based highlighting
            self._add_basic_pattern_highlights(story, text_style, original_text)
            return
        
        # Sort clauses by start position for proper highlighting
        valid_clauses = [c for c in clauses if c.get('start_pos', 0) >= 0 and c.get('end_pos', 0) > c.get('start_pos', 0)]
        if not valid_clauses:
            # No valid position data, fall back to pattern matching
            self._add_basic_pattern_highlights(story, text_style, original_text)
            return
            
        sorted_clauses = sorted(valid_clauses, key=lambda x: x.get('start_pos', 0))
        
        # Create highlighted text paragraph by paragraph to avoid ReportLab issues
        highlighted_paragraphs = self._create_highlighted_paragraphs(original_text, sorted_clauses)
        
        for para_text in highlighted_paragraphs:
            if para_text.strip():
                try:
                    # Clean and format the text
                    clean_text = self._clean_text_for_pdf(para_text)
                    story.append(Paragraph(clean_text, text_style))
                except Exception as e:
                    # If highlighting fails, add plain text
                    plain_text = self._strip_html_tags(para_text)
                    story.append(Paragraph(plain_text, text_style))
                story.append(Spacer(1, 6))
    
    def _add_basic_pattern_highlights(self, story: List, text_style, original_text: str):
        """Add highlighting based on common legal patterns when AI analysis fails."""
        # Split into paragraphs
        paragraphs = original_text.split('\n\n')
        
        for para in paragraphs:
            if not para.strip():
                continue
                
            # Apply basic pattern highlighting
            highlighted_para = self._apply_pattern_highlights(para)
            
            try:
                story.append(Paragraph(highlighted_para, text_style))
            except:
                story.append(Paragraph(para, text_style))
            story.append(Spacer(1, 6))
    
    def _apply_pattern_highlights(self, text: str) -> str:
        """Apply highlights based on legal document patterns."""
        import re
        
        # Escape HTML first
        text = self._escape_html(text)
        
        # Pattern-based highlighting for common legal terms
        harmful_patterns = [
            r'\b(penalty|penalt(y|ies))\b',
            r'\b(forfeit|forfeiture)\b', 
            r'\b(breach|violation)\b',
            r'\b(terminate|termination)\b',
            r'\b(liable|liability)\b'
        ]
        
        warning_patterns = [
            r'\b(shall|must|required)\b',
            r'\b(obligation|duty)\b',
            r'\b(notice|notification)\b',
            r'\b(deadline|due date)\b'
        ]
        
        good_patterns = [
            r'\b(benefit|advantage)\b',
            r'\b(right|entitle)\b',
            r'\b(protection|protect)\b'
        ]
        
        # Apply highlighting (case insensitive)
        for pattern in harmful_patterns:
            text = re.sub(pattern, f'<font color="#d32f2f" backcolor="#ffcdd2"><b>\\g<0></b></font>', 
                         text, flags=re.IGNORECASE)
        
        for pattern in warning_patterns:
            text = re.sub(pattern, f'<font color="#f57c00" backcolor="#fff3b0"><b>\\g<0></b></font>', 
                         text, flags=re.IGNORECASE)
        
        for pattern in good_patterns:
            text = re.sub(pattern, f'<font color="#388e3c" backcolor="#c8e6c9"><b>\\g<0></b></font>', 
                         text, flags=re.IGNORECASE)
        
        return text
    
    def _create_highlighted_paragraphs(self, original_text: str, clauses: List[Dict]) -> List[str]:
        """Create paragraphs with proper highlighting."""
        paragraphs = []
        
        # Split text into natural paragraphs first
        text_paragraphs = original_text.split('\n\n')
        current_pos = 0
        
        for para in text_paragraphs:
            if not para.strip():
                current_pos += len(para) + 2  # +2 for \n\n
                continue
                
            para_start = current_pos
            para_end = current_pos + len(para)
            
            # Find clauses that overlap with this paragraph
            para_clauses = []
            for clause in clauses:
                clause_start = clause.get('start_pos', 0)
                clause_end = clause.get('end_pos', 0)
                
                # Check if clause overlaps with paragraph
                if clause_start < para_end and clause_end > para_start:
                    # Adjust positions relative to paragraph start
                    rel_start = max(0, clause_start - para_start)
                    rel_end = min(len(para), clause_end - para_start)
                    
                    if rel_end > rel_start:
                        para_clauses.append({
                            'start_pos': rel_start,
                            'end_pos': rel_end,
                            'classification': clause.get('classification', 'neutral')
                        })
            
            # Apply highlighting to this paragraph
            if para_clauses:
                highlighted_para = self._highlight_paragraph(para, para_clauses)
            else:
                highlighted_para = self._escape_html(para)
                
            paragraphs.append(highlighted_para)
            current_pos = para_end + 2  # +2 for \n\n
        
        return paragraphs
    
    def _highlight_paragraph(self, para_text: str, clauses: List[Dict]) -> str:
        """Highlight a single paragraph with clause data."""
        # Sort clauses by position
        sorted_clauses = sorted(clauses, key=lambda x: x.get('start_pos', 0))
        
        result_parts = []
        last_pos = 0
        
        for clause in sorted_clauses:
            start_pos = clause.get('start_pos', 0)
            end_pos = clause.get('end_pos', 0)
            classification = clause.get('classification', 'neutral')
            
            # Add text before clause
            if start_pos > last_pos:
                before_text = para_text[last_pos:start_pos]
                result_parts.append(self._escape_html(before_text))
            
            # Add highlighted clause
            clause_text = para_text[start_pos:end_pos]
            if clause_text.strip():
                bg_color = self._get_highlight_color(classification)
                text_color = self.text_colors.get(classification, self.text_colors['neutral']).hexval()
                highlighted = f'<font color="{text_color}" backcolor="{bg_color}"><b>{self._escape_html(clause_text)}</b></font>'
                result_parts.append(highlighted)
            
            last_pos = max(end_pos, last_pos)
        
        # Add remaining text
        if last_pos < len(para_text):
            remaining = para_text[last_pos:]
            result_parts.append(self._escape_html(remaining))
        
        return ''.join(result_parts)
    
    def _clean_text_for_pdf(self, text: str) -> str:
        """Clean text for PDF generation."""
        # Remove problematic characters that cause ReportLab issues
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;').replace('>', '&gt;')  
        
        # Fix the HTML tags back
        text = text.replace('&lt;font ', '<font ')
        text = text.replace('&lt;/font&gt;', '</font>')
        text = text.replace('&lt;b&gt;', '<b>')
        text = text.replace('&lt;/b&gt;', '</b>')
        
        return text
    
    def _strip_html_tags(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        return re.sub(r'<[^>]+>', '', text)
    
    def _get_highlight_color(self, classification: str) -> str:
        """Get hex color for highlighting based on classification."""
        color_map = {
            'harmful': '#ffcdd2',     # Light red
            'warning': '#fff3b0',     # Light yellow  
            'good': '#c8e6c9',        # Light green
            'neutral': '#f5f5f5'      # Light gray
        }
        return color_map.get(classification, color_map['neutral'])
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters in text."""
        import html
        return html.escape(text, quote=False)
    
    def _get_current_date(self) -> str:
        """Get current date formatted for display."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")