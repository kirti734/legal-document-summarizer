import os
import json
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any

class ClauseAnalysis(BaseModel):
    text: str
    classification: str  # 'harmful', 'warning', 'good', 'neutral'
    reasoning: str
    confidence: float
    start_pos: int
    end_pos: int

class DocumentAnalysis(BaseModel):
    clauses: List[ClauseAnalysis]
    overall_summary: str
    risk_level: str  # 'high', 'medium', 'low'

class GeminiAnalyzer:
    """Handles Gemini AI integration for document analysis and clause classification."""
    
    def __init__(self):
        """Initialize Gemini analyzer with API key."""
        self.logger = logging.getLogger(__name__)
        
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not found")
            
            # Initialize client with timeout settings
            self.client = genai.Client(
                api_key=api_key,
                http_options={'timeout': 30}  # 30 second timeout
            )
            self.logger.info("Gemini AI client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            raise Exception(f"Gemini AI initialization failed: {e}")
    
    def analyze_document(self, text: str, entities: Dict[str, List]) -> Dict[str, Any]:
        """
        Analyze legal document and classify clauses.
        
        Args:
            text (str): Document text
            entities (dict): Extracted entities from NER
            
        Returns:
            dict: Analysis results with clause classifications
        """
        try:
            self.logger.info("Starting clause analysis...")
            
            # Get clause analysis with timeout protection
            clause_analysis = self._classify_clauses(text)
            self.logger.info(f"Classified {len(clause_analysis)} clauses")
            
            # Get overall summary
            self.logger.info("Generating summary...")
            summary = self._generate_summary(text, entities, clause_analysis)
            
            # Assess risk
            risk_assessment = self._assess_overall_risk(clause_analysis)
            
            return {
                'clauses': clause_analysis,
                'summary': summary,
                'risk_assessment': risk_assessment
            }
            
        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
            # Return fallback analysis
            fallback_clauses = self._create_fallback_analysis(text)
            fallback_counts = {'harmful': 0, 'warning': 0, 'good': 0, 'neutral': len(fallback_clauses)}
            
            return {
                'clauses': fallback_clauses,
                'summary': self._generate_fallback_summary(entities, fallback_counts),
                'risk_assessment': {'level': 'unknown', 'description': 'AI analysis unavailable - basic analysis provided'}
            }
    
    def _classify_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Classify clauses in the document using Gemini AI."""
        try:
            # Split text into manageable chunks for analysis
            text_chunk = text[:3000] if len(text) > 3000 else text
            
            prompt = f"""Analyze this legal document and identify key clauses. Classify each clause as harmful, warning, good, or neutral.

Document text:
{text_chunk}

Please analyze the document and return a JSON response with this exact structure:
{{
  "clauses": [
    {{
      "text": "exact clause text",
      "classification": "harmful|warning|good|neutral",
      "reasoning": "brief explanation",
      "confidence": 0.8
    }}
  ]
}}

Focus on the most important clauses. Limit to 5-8 clauses maximum."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=2000
                ),
            )

            if not response.text:
                self.logger.warning("Empty response from Gemini")
                return self._create_fallback_analysis(text)
            
            # Clean the response text
            response_text = response.text.strip()
            
            # Try to extract JSON from the response
            try:
                # Look for JSON content between curly braces
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_text = response_text[start_idx:end_idx]
                    analysis_data = json.loads(json_text)
                else:
                    # If no JSON found, try parsing the whole response
                    analysis_data = json.loads(response_text)
                    
            except json.JSONDecodeError as je:
                self.logger.warning(f"JSON parsing failed: {je}")
                self.logger.warning(f"Response text: {response_text[:500]}...")
                return self._create_fallback_analysis(text)
            
            # Process and validate the response
            clauses = []
            if isinstance(analysis_data, dict) and 'clauses' in analysis_data:
                for i, clause_data in enumerate(analysis_data['clauses']):
                    if isinstance(clause_data, dict):
                        clause = {
                            'text': clause_data.get('text', f'Clause {i+1}'),
                            'classification': clause_data.get('classification', 'neutral'),
                            'reasoning': clause_data.get('reasoning', 'No reasoning provided'),
                            'confidence': float(clause_data.get('confidence', 0.5)),
                            'start_pos': i * 100,  # Approximate positions
                            'end_pos': (i + 1) * 100
                        }
                        clauses.append(clause)
            
            if not clauses:
                self.logger.warning("No clauses extracted from Gemini response")
                return self._create_fallback_analysis(text)
            
            return clauses
            
        except Exception as e:
            self.logger.error(f"Clause classification failed: {e}")
            return self._create_fallback_analysis(text)
    
    def _generate_summary(self, text: str, entities: Dict, clause_analysis: List[Dict]) -> str:
        """Generate comprehensive summary using Gemini AI."""
        try:
            # Count clause types
            clause_counts = {'harmful': 0, 'warning': 0, 'good': 0, 'neutral': 0}
            for clause in clause_analysis:
                clause_type = clause.get('classification', 'neutral')
                clause_counts[clause_type] = clause_counts.get(clause_type, 0) + 1
            
            entities_summary = self._format_entities_for_summary(entities)
            text_sample = text[:1500] if len(text) > 1500 else text
            
            prompt = f"""Please provide a clear, easy-to-understand summary of this legal document.

Document Sample:
{text_sample}

Key Information Found:
{entities_summary}

Analysis Results:
- Harmful clauses found: {clause_counts['harmful']}
- Warning clauses found: {clause_counts['warning']}
- Good clauses found: {clause_counts['good']}
- Neutral clauses found: {clause_counts['neutral']}

Please write a summary that includes:
1. What type of document this is
2. Who are the main parties involved
3. What are the key terms and obligations
4. Any potential risks or concerns
5. Overall assessment

Use simple language that anyone can understand. Keep it concise but informative."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=800
                )
            )

            if response.text and response.text.strip():
                return response.text.strip()
            else:
                self.logger.warning("Empty summary response from Gemini")
                return self._generate_fallback_summary(entities, clause_counts)
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return self._generate_fallback_summary(entities, clause_counts)
    
    def _assess_overall_risk(self, clause_analysis: List[Dict]) -> Dict[str, Any]:
        """Assess overall risk level based on clause analysis."""
        if not clause_analysis:
            return {'level': 'unknown', 'description': 'No clause analysis available'}
        
        harmful_count = sum(1 for c in clause_analysis if c.get('classification') == 'harmful')
        warning_count = sum(1 for c in clause_analysis if c.get('classification') == 'warning')
        total_clauses = len(clause_analysis)
        
        if harmful_count > 0:
            if harmful_count >= total_clauses * 0.3:  # 30% or more harmful
                return {
                    'level': 'high',
                    'description': f'Document contains {harmful_count} harmful clause(s). Careful review recommended.'
                }
            else:
                return {
                    'level': 'medium',
                    'description': f'Document contains {harmful_count} harmful clause(s) and {warning_count} warning clause(s).'
                }
        elif warning_count > total_clauses * 0.4:  # More than 40% warnings
            return {
                'level': 'medium',
                'description': f'Document contains {warning_count} clause(s) that need attention.'
            }
        else:
            return {
                'level': 'low',
                'description': 'Document appears to have standard terms with minimal risks.'
            }
    
    def _format_entities_for_summary(self, entities: Dict) -> str:
        """Format entities for inclusion in summary prompt."""
        formatted = []
        for entity_type, entity_list in entities.items():
            if entity_list:
                items = [e.get('text', str(e)) for e in entity_list[:3]]  # Top 3
                formatted.append(f"{entity_type}: {', '.join(items)}")
        
        return '\n'.join(formatted) if formatted else "No key entities identified"
    
    def _create_fallback_analysis(self, text: str) -> List[Dict[str, Any]]:
        """Create basic fallback analysis when Gemini fails."""
        # Split text into sentences and create basic analysis
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        clauses = []
        
        pos = 0
        for sentence in sentences[:10]:  # Analyze first 10 sentences
            clause = {
                'text': sentence,
                'classification': 'neutral',
                'reasoning': 'Automatic classification - manual review recommended',
                'confidence': 0.3,
                'start_pos': pos,
                'end_pos': pos + len(sentence)
            }
            clauses.append(clause)
            pos += len(sentence) + 1
        
        return clauses
    
    def _generate_fallback_summary(self, entities: Dict, clause_counts: Dict) -> str:
        """Generate a basic fallback summary when Gemini fails."""
        summary_parts = []
        
        # Basic document info
        summary_parts.append("Document Analysis Summary:")
        summary_parts.append("")
        
        # Clause analysis
        total_clauses = sum(clause_counts.values())
        if total_clauses > 0:
            summary_parts.append(f"Found {total_clauses} clauses for analysis:")
            if clause_counts['harmful'] > 0:
                summary_parts.append(f"• {clause_counts['harmful']} potentially harmful clauses")
            if clause_counts['warning'] > 0:
                summary_parts.append(f"• {clause_counts['warning']} clauses requiring attention")
            if clause_counts['good'] > 0:
                summary_parts.append(f"• {clause_counts['good']} beneficial clauses")
            if clause_counts['neutral'] > 0:
                summary_parts.append(f"• {clause_counts['neutral']} standard clauses")
        
        # Entity information
        if entities:
            summary_parts.append("")
            summary_parts.append("Key information identified:")
            for entity_type, entity_list in entities.items():
                if entity_list:
                    entity_name = entity_type.replace('_', ' ').title()
                    items = [e.get('text', str(e)) for e in entity_list[:2]]
                    summary_parts.append(f"• {entity_name}: {', '.join(items)}")
        
        return "\n".join(summary_parts)