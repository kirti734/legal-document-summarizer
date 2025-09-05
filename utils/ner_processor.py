import spacy
import re
import logging
from collections import defaultdict

class NERProcessor:
    """Handles Named Entity Recognition for legal documents."""
    
    def __init__(self):
        """Initialize NER processor with spaCy model."""
        self.logger = logging.getLogger(__name__)
        
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            
            # Add custom legal entity patterns
            self._add_legal_patterns()
            
        except IOError:
            self.logger.error("spaCy model 'en_core_web_sm' not found")
            raise Exception("spaCy English model not installed. Please install it using: python -m spacy download en_core_web_sm")
    
    def _add_legal_patterns(self):
        """Add custom patterns for legal entity recognition."""
        from spacy.matcher import Matcher
        
        # Initialize matcher
        self.matcher = Matcher(self.nlp.vocab)
        
        # Contract terms patterns
        contract_patterns = [
            [{"LOWER": {"IN": ["agreement", "contract", "terms", "conditions"]}},
             {"IS_ALPHA": True, "OP": "*"}],
            [{"LOWER": "hereby"}, {"LOWER": {"IN": ["agrees", "acknowledges", "represents"]}},
             {"IS_ALPHA": True, "OP": "*"}],
            [{"LOWER": {"IN": ["shall", "will", "must"]}}, {"IS_ALPHA": True, "OP": "+"}],
            [{"LOWER": "subject"}, {"LOWER": "to"}, {"IS_ALPHA": True, "OP": "+"}]
        ]
        
        # Legal references patterns
        legal_ref_patterns = [
            [{"LOWER": {"IN": ["section", "clause", "article", "paragraph"]}},
             {"LIKE_NUM": True}],
            [{"LOWER": {"IN": ["pursuant", "according"]}}, {"LOWER": "to"},
             {"IS_ALPHA": True, "OP": "+"}],
            [{"TEXT": {"REGEX": r"§\d+"}}],  # Section symbols
            [{"IS_ALPHA": True}, {"LOWER": {"IN": ["law", "act", "statute", "regulation"]}}]
        ]
        
        # Add patterns to matcher
        self.matcher.add("CONTRACT_TERM", contract_patterns)
        self.matcher.add("LEGAL_REF", legal_ref_patterns)
    
    def extract_entities(self, text):
        """
        Extract named entities from text.
        
        Args:
            text (str): Input text
            
        Returns:
            dict: Dictionary of entity types and their instances
        """
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            entities = defaultdict(list)
            
            # Extract standard NER entities
            for ent in doc.ents:
                entity_type = self._map_entity_type(ent.label_)
                if entity_type:
                    entities[entity_type].append({
                        'text': ent.text.strip(),
                        'confidence': 1.0,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
            
            # Extract custom legal patterns
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                label = self.nlp.vocab.strings[match_id]
                span = doc[start:end]
                entities[label].append({
                    'text': span.text.strip(),
                    'confidence': 0.8,
                    'start': span.start_char,
                    'end': span.end_char
                })
            
            # Extract monetary amounts with regex
            money_entities = self._extract_monetary_amounts(text)
            entities['MONEY'].extend(money_entities)
            
            # Extract dates with regex
            date_entities = self._extract_dates(text)
            entities['DATE'].extend(date_entities)
            
            # Remove duplicates and sort by confidence
            for entity_type in entities:
                entities[entity_type] = self._deduplicate_entities(entities[entity_type])
            
            return dict(entities)
            
        except Exception as e:
            self.logger.error(f"NER processing failed: {str(e)}")
            return {}
    
    def _map_entity_type(self, spacy_label):
        """Map spaCy entity labels to legal document categories."""
        mapping = {
            'PERSON': 'PERSON',
            'ORG': 'ORGANIZATION',
            'DATE': 'DATE',
            'MONEY': 'MONEY',
            'GPE': 'LOCATION',
            'LAW': 'LEGAL_REF',
            'EVENT': 'EVENT',
            'PRODUCT': 'PRODUCT',
            'WORK_OF_ART': 'DOCUMENT'
        }
        return mapping.get(spacy_label, None)
    
    def _extract_monetary_amounts(self, text):
        """Extract monetary amounts using regex patterns."""
        money_patterns = [
            r'\$[\d,]+\.?\d*',  # $1,000.00
            r'USD\s*[\d,]+\.?\d*',  # USD 1000
            r'[\d,]+\.?\d*\s*dollars?',  # 1000 dollars
            r'[\d,]+\.?\d*\s*USD',  # 1000 USD
        ]
        
        entities = []
        for pattern in money_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group().strip(),
                    'confidence': 0.9,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def _extract_dates(self, text):
        """Extract dates using regex patterns."""
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{2,4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{2,4}\b',  # Month DD, YYYY
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4}\b',  # DD Month YYYY
        ]
        
        entities = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group().strip(),
                    'confidence': 0.9,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def _deduplicate_entities(self, entities):
        """Remove duplicate entities and sort by confidence."""
        if not entities:
            return []
        
        # Remove exact duplicates
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity['text'].lower(), entity['start'], entity['end'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        # Sort by confidence (highest first)
        return sorted(unique_entities, key=lambda x: x['confidence'], reverse=True)
    
    def generate_summary(self, text, entities):
        """
        Generate a simplified summary of the legal document.
        
        Args:
            text (str): Original text
            entities (dict): Extracted entities
            
        Returns:
            str: Simplified summary
        """
        try:
            summary_parts = []
            
            # Document type detection
            doc_type = self._detect_document_type(text)
            summary_parts.append(f"Document Type: {doc_type}")
            
            # Key parties
            if 'PERSON' in entities and entities['PERSON']:
                persons = [e['text'] for e in entities['PERSON'][:3]]  # Limit to top 3
                summary_parts.append(f"Key Individuals: {', '.join(persons)}")
            
            if 'ORGANIZATION' in entities and entities['ORGANIZATION']:
                orgs = [e['text'] for e in entities['ORGANIZATION'][:3]]
                summary_parts.append(f"Organizations Involved: {', '.join(orgs)}")
            
            # Financial information
            if 'MONEY' in entities and entities['MONEY']:
                amounts = [e['text'] for e in entities['MONEY'][:3]]
                summary_parts.append(f"Financial Terms: {', '.join(amounts)}")
            
            # Important dates
            if 'DATE' in entities and entities['DATE']:
                dates = [e['text'] for e in entities['DATE'][:3]]
                summary_parts.append(f"Key Dates: {', '.join(dates)}")
            
            # Contract terms
            if 'CONTRACT_TERM' in entities and entities['CONTRACT_TERM']:
                terms = [e['text'] for e in entities['CONTRACT_TERM'][:2]]
                summary_parts.append(f"Contract Terms: {', '.join(terms)}")
            
            # Legal references
            if 'LEGAL_REF' in entities and entities['LEGAL_REF']:
                refs = [e['text'] for e in entities['LEGAL_REF'][:2]]
                summary_parts.append(f"Legal References: {', '.join(refs)}")
            
            # Generate final summary
            if summary_parts:
                summary = "Document Summary:\n\n" + "\n".join(f"• {part}" for part in summary_parts)
            else:
                summary = "This appears to be a legal document. Key information could not be automatically extracted. Please review the original text and identified entities for important details."
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {str(e)}")
            return "Summary could not be generated. Please review the extracted text and entities."
    
    def _detect_document_type(self, text):
        """Detect the type of legal document."""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['contract', 'agreement', 'hereby agrees']):
            return "Contract/Agreement"
        elif any(term in text_lower for term in ['lease', 'rental', 'tenant', 'landlord']):
            return "Lease Agreement"
        elif any(term in text_lower for term in ['employment', 'employee', 'employer', 'job']):
            return "Employment Document"
        elif any(term in text_lower for term in ['invoice', 'bill', 'payment due', 'amount owed']):
            return "Invoice/Bill"
        elif any(term in text_lower for term in ['will', 'testament', 'beneficiary', 'estate']):
            return "Will/Testament"
        elif any(term in text_lower for term in ['license', 'permit', 'authorization']):
            return "License/Permit"
        else:
            return "Legal Document"
