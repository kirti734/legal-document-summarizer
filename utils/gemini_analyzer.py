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
            
            self.client = genai.Client(api_key=api_key)
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
            # Get clause analysis
            clause_analysis = self._classify_clauses(text)
            
            # Get overall summary
            summary = self._generate_summary(text, entities, clause_analysis)
            
            return {
                'clauses': clause_analysis,
                'summary': summary,
                'risk_assessment': self._assess_overall_risk(clause_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
            return {
                'clauses': [],
                'summary': f"Analysis failed: {str(e)}",
                'risk_assessment': {'level': 'unknown', 'description': 'Could not analyze document'}
            }
    
    def _classify_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Classify clauses in the document using Gemini AI."""
        try:
            system_prompt = """You are a legal document analyzer. Analyze the provided text and identify distinct clauses or sections. For each clause, classify it as one of:

1. 'harmful' - Clauses that are clearly disadvantageous, unfair, or potentially harmful to one party
2. 'warning' - Clauses that require careful attention, may have risks, or need review
3. 'good' - Clauses that are beneficial, fair, or standard good practice
4. 'neutral' - Standard clauses with no particular risk or benefit

For each clause, provide:
- The exact text of the clause
- Classification (harmful/warning/good/neutral)
- Brief reasoning for the classification
- Confidence level (0.0 to 1.0)
- Approximate character positions in the original text

Respond with valid JSON only."""

            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=f"Analyze this legal document:\n\n{text}")])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=4000
                ),
            )

            if not response.text:
                raise ValueError("Empty response from Gemini")
            
            # Parse the JSON response
            analysis_data = json.loads(response.text)
            
            # Process and validate the response
            clauses = []
            if 'clauses' in analysis_data:
                for clause_data in analysis_data['clauses']:
                    clause = {
                        'text': clause_data.get('text', ''),
                        'classification': clause_data.get('classification', 'neutral'),
                        'reasoning': clause_data.get('reasoning', ''),
                        'confidence': float(clause_data.get('confidence', 0.5)),
                        'start_pos': clause_data.get('start_pos', 0),
                        'end_pos': clause_data.get('end_pos', 0)
                    }
                    clauses.append(clause)
            
            return clauses
            
        except Exception as e:
            self.logger.error(f"Clause classification failed: {e}")
            # Fallback: create basic analysis
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
            
            prompt = f"""Provide a comprehensive, easy-to-understand summary of this legal document.

Document Text:
{text[:2000]}...

Entities Found:
{entities_summary}

Clause Analysis:
- Harmful clauses: {clause_counts['harmful']}
- Warning clauses: {clause_counts['warning']}
- Good clauses: {clause_counts['good']}
- Neutral clauses: {clause_counts['neutral']}

Please provide:
1. Document type and purpose
2. Key parties involved
3. Main terms and conditions
4. Potential risks or concerns
5. Overall recommendation

Write in plain, simple language that non-lawyers can understand."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1000
                )
            )

            return response.text if response.text else "Could not generate summary"
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return f"Summary generation failed: {str(e)}"
    
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