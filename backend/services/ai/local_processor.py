"""
Local NLP Processing Service.
Handles lightweight text preprocessing locally using spaCy:
- Tokenization
- Actor identification  
- Basic entity extraction
- Text cleaning and normalization
"""
import re
import json
from typing import Dict, List, Any, Optional, Set
import spacy
from core.logging import get_logger

logger = get_logger(__name__)

class LocalNLPProcessor:
    """Local NLP processor for lightweight text analysis."""
    
    def __init__(self):
        self.nlp = None
        self._load_spacy_model()
        
        # Common actor patterns for rule-based identification
        self.actor_patterns = {
            'users': ['user', 'customer', 'client', 'patient', 'student', 'employee'],
            'administrators': ['admin', 'administrator', 'manager', 'supervisor', 'operator'],
            'systems': ['system', 'application', 'software', 'api', 'database', 'server'],
            'external': ['third-party', 'external', 'vendor', 'partner', 'bank', 'payment gateway']
        }
        
        # Modal verbs for requirement strength detection
        self.modal_verbs = ['shall', 'must', 'should', 'will', 'may', 'might', 'could', 'can']
        
        # Vague terms to flag
        self.vague_terms = [
            'appropriate', 'reasonable', 'timely', 'adequate', 'suitable', 'user-friendly',
            'efficient', 'fast', 'quick', 'easy', 'good', 'large', 'small', 'many', 'few'
        ]
    
    def _load_spacy_model(self):
        """Load spaCy model with fallback."""
        try:
            # Try to load English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model")
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            self.nlp = None
    
    def is_available(self) -> bool:
        """Check if spaCy model is available."""
        return self.nlp is not None
    
    def tokenize_text(self, text: str) -> Dict[str, Any]:
        """
        Tokenize text and extract basic linguistic features.
        This is a lightweight local operation.
        """
        if not self.nlp:
            return self._fallback_tokenization(text)
        
        try:
            doc = self.nlp(text)
            
            # Extract tokens with basic features
            tokens = []
            for token in doc:
                tokens.append({
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'is_stop': token.is_stop,
                    'is_punct': token.is_punct,
                    'is_alpha': token.is_alpha
                })
            
            # Extract sentences
            sentences = [sent.text.strip() for sent in doc.sents]
            
            # Basic statistics
            return {
                'tokens': tokens,
                'sentences': sentences,
                'token_count': len(tokens),
                'sentence_count': len(sentences),
                'word_count': len([t for t in tokens if t['is_alpha']]),
                'processed_locally': True
            }
            
        except Exception as e:
            logger.error(f"spaCy tokenization failed: {e}")
            return self._fallback_tokenization(text)
    
    def _fallback_tokenization(self, text: str) -> Dict[str, Any]:
        """Fallback tokenization without spaCy."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        words = re.findall(r'\b\w+\b', text.lower())
        
        return {
            'tokens': [{'text': w, 'lemma': w, 'pos': 'UNKNOWN', 'is_stop': False, 'is_punct': False, 'is_alpha': True} for w in words],
            'sentences': sentences,
            'token_count': len(words),
            'sentence_count': len(sentences),
            'word_count': len(words),
            'processed_locally': False
        }
    
    def identify_actors(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify actors in the text using both spaCy NER and rule-based patterns.
        This runs locally and provides basic actor identification.
        """
        actors = []
        text_lower = text.lower()
        
        # Rule-based actor identification
        for category, patterns in self.actor_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Find the actual context where the pattern appears
                    matches = re.finditer(rf'\b({re.escape(pattern)})\w*\b', text, re.IGNORECASE)
                    for match in matches:
                        actors.append({
                            'text': match.group(),
                            'category': category,
                            'confidence': 0.8,
                            'method': 'rule_based',
                            'position': match.start()
                        })
        
        # spaCy NER if available
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'ORG', 'GPE']:
                        # Map spaCy labels to our actor categories
                        category = self._map_spacy_label_to_actor(ent.label_)
                        actors.append({
                            'text': ent.text,
                            'category': category,
                            'confidence': 0.7,
                            'method': 'spacy_ner',
                            'position': ent.start_char
                        })
            except Exception as e:
                logger.error(f"spaCy NER failed: {e}")
        
        # Remove duplicates and sort by confidence
        unique_actors = {}
        for actor in actors:
            key = (actor['text'].lower(), actor['category'])
            if key not in unique_actors or actor['confidence'] > unique_actors[key]['confidence']:
                unique_actors[key] = actor
        
        return sorted(unique_actors.values(), key=lambda x: x['confidence'], reverse=True)
    
    def _map_spacy_label_to_actor(self, spacy_label: str) -> str:
        """Map spaCy NER labels to our actor categories."""
        mapping = {
            'PERSON': 'users',
            'ORG': 'organizations',
            'GPE': 'external',
            'PRODUCT': 'systems'
        }
        return mapping.get(spacy_label, 'unknown')
    
    def extract_modal_verbs(self, text: str) -> List[Dict[str, Any]]:
        """Extract modal verbs that indicate requirement strength."""
        modal_verbs = []
        text_lower = text.lower()
        
        for modal in self.modal_verbs:
            matches = re.finditer(rf'\b{re.escape(modal)}\b', text_lower)
            for match in matches:
                modal_verbs.append({
                    'text': modal,
                    'position': match.start(),
                    'context': text[max(0, match.start()-20):match.end()+20]
                })
        
        return modal_verbs
    
    def detect_vague_terms(self, text: str) -> List[Dict[str, Any]]:
        """Detect vague and subjective terms."""
        vague_terms = []
        text_lower = text.lower()
        
        for vague in self.vague_terms:
            matches = re.finditer(rf'\b{re.escape(vague)}\w*\b', text_lower)
            for match in matches:
                vague_terms.append({
                    'text': match.group(),
                    'position': match.start(),
                    'context': text[max(0, match.start()-30):match.end()+30],
                    'suggestion': self._get_vague_term_suggestion(vague)
                })
        
        return vague_terms
    
    def _get_vague_term_suggestion(self, vague_term: str) -> str:
        """Get suggestion for replacing vague terms."""
        suggestions = {
            'appropriate': 'specify exact criteria',
            'reasonable': 'define measurable limits',
            'timely': 'specify time limits',
            'efficient': 'define performance metrics',
            'fast': 'specify response time',
            'user-friendly': 'list specific usability criteria'
        }
        return suggestions.get(vague_term, 'replace with specific, measurable criteria')
    
    def preprocess_requirements_text(self, text: str) -> Dict[str, Any]:
        """
        Complete local preprocessing pipeline for requirements text.
        This prepares text for cloud AI processing.
        """
        logger.info("Starting local NLP preprocessing")
        
        # Step 1: Tokenization and basic analysis
        tokenization_result = self.tokenize_text(text)
        
        # Step 2: Actor identification
        actors = self.identify_actors(text)
        
        # Step 3: Modal verb extraction
        modal_verbs = self.extract_modal_verbs(text)
        
        # Step 4: Vague term detection
        vague_terms = self.detect_vague_terms(text)
        
        # Step 5: Text cleaning
        cleaned_text = self.clean_text(text)
        
        result = {
            'original_text': text,
            'cleaned_text': cleaned_text,
            'tokenization': tokenization_result,
            'actors': actors,
            'modal_verbs': modal_verbs,
            'vague_terms': vague_terms,
            'processing_summary': {
                'actors_found': len(actors),
                'modal_verbs_found': len(modal_verbs),
                'vague_terms_found': len(vague_terms),
                'processed_locally': True
            }
        }
        
        logger.info(f"Local preprocessing complete: {len(actors)} actors, {len(modal_verbs)} modals, {len(vague_terms)} vague terms")
        return result
    
    def clean_text(self, text: str) -> str:
        """Enhanced text cleaning to fix artifacts and remove noise."""
        # Fix duplicate modal verbs (shallshall -> shall, mustmust -> must, etc.)
        text = re.sub(r'(shall|must|will|should|may|might|could|can)\1+', r'\1', text, flags=re.IGNORECASE)
        
        # Remove table and figure references completely
        text = re.sub(r'Table\s+\d+[:\-]?\s*.+?(?=\n|$)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Figure\s+\d+[:\-]?\s*.+?(?=\n|$)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Table\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Figure\s+\d+', '', text, flags=re.IGNORECASE)
        
        # Remove section headers and numbering
        text = re.sub(r'^\d+\.\d+\s+.+?(?=\n|$)', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Section\s+\d+[:\-]?\s*.+?(?=\n|$)', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'^\d+\.\s+.+?(?=\n|$)', '', text, flags=re.MULTILINE)
        
        # Remove document structure descriptions
        text = re.sub(r'This document details?.+?\.?\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'The following section describes?.+?\.?\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r'Section\s+\d+\s+–\s*.+?\.?\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove page numbers and headers/footers
        text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Page\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\b(?=\s*$)', '', text, flags=re.MULTILINE)  # Standalone numbers
        
        # Remove bullet points and list markers that aren't requirements
        text = re.sub(r'^[•\-\*]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # Remove lines that are too short to be requirements (likely headers/noise)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Keep lines that have reasonable length and contain requirement indicators
            if len(line) > 15 and any(modal in line.lower() for modal in self.modal_verbs):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()


# Global instance
local_processor = LocalNLPProcessor()
