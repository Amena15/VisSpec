"""
Hybrid Processing Service.
Orchestrates local preprocessing with cloud AI processing for optimal performance.
- Local: Basic text extraction, tokenization, actor identification (PyMuPDF + spaCy)
- Cloud: Heavy semantic extraction, defect detection, organization (Groq API + LLaMA 3)
"""
import json
import re
from typing import Dict, List, Any, Optional
from backend.core.logging import get_logger
from backend.services.document.parser import DocumentParser
from backend.services.ai.local_processor import local_processor
from backend.services.ai.llm_service import llm_service
from backend.services.ai.requirement_organizer import requirement_organizer

logger = get_logger(__name__)

class HybridProcessor:
    """
    Hybrid processing service that combines local and cloud AI capabilities.
    
    Architecture:
    1. Local Processing (Fast, No API costs):
       - Text extraction with PyMuPDF
       - Tokenization with spaCy
       - Basic actor identification
       - Text cleaning and normalization
    
    2. Cloud AI Processing (Powerful, API costs):
       - Semantic requirement extraction
       - Defect detection and analysis
       - Complex categorization
       - Organization and enrichment
    """
    
    def __init__(self):
        self.document_parser = DocumentParser()
        self.local_processor = local_processor
        self.llm_service = llm_service
        self.requirement_organizer = requirement_organizer
    
    def process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Main entry point for document processing.
        Executes the full hybrid pipeline.
        """
        logger.info(f"Starting hybrid document processing for: {filename}")
        
        try:
            # Phase 1: Local Processing (Fast, no API costs)
            local_result = self._local_processing_phase(file_content, filename)
            
            # Phase 2: Cloud AI Processing (Powerful, with API costs)
            cloud_result = self._cloud_processing_phase(local_result)
            
            # Phase 3: Integration and final processing
            final_result = self._integrate_results(local_result, cloud_result)
            
            logger.info(f"Hybrid processing completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"Hybrid processing failed: {e}")
            return {
                'error': str(e),
                'processing_status': 'failed',
                'local_processing': local_result if 'local_result' in locals() else None,
                'cloud_processing': None
            }
    
    def _local_processing_phase(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Phase 1: Local processing using PyMuPDF and spaCy.
        This phase is fast and doesn't require API calls.
        """
        logger.info("Starting local processing phase")
        
        # Step 1: Document parsing with PyMuPDF
        parse_result = self.document_parser.parse_full(file_content, filename)
        if 'error' in parse_result:
            raise Exception(f"Document parsing failed: {parse_result['error']}")
        
        # Step 2: Extract text for processing
        text = parse_result.get('cleaned_text', parse_result.get('text', ''))
        if not text:
            raise Exception("No text extracted from document")
        
        # Step 3: Local NLP preprocessing with spaCy
        nlp_result = self.local_processor.preprocess_requirements_text(text)
        
        # Step 4: Basic requirement extraction (rule-based)
        basic_requirements = self.document_parser.extract_requirements(text)
        
        local_result = {
            'document_info': {
                'filename': filename,
                'file_extension': parse_result.get('file_extension'),
                'page_count': parse_result.get('page_count'),
                'word_count': parse_result.get('word_count'),
                'is_scanned_pdf': parse_result.get('is_scanned_pdf', 0)
            },
            'text_extraction': {
                'original_text': text,
                'sections': parse_result.get('sections', []),
                'sections_found': parse_result.get('sections_found', [])
            },
            'local_nlp': nlp_result,
            'basic_requirements': basic_requirements,
            'processing_phase': 'local_completed',
            'processing_time_local': 'fast'  # For monitoring
        }
        
        logger.info(f"Local processing completed: {len(basic_requirements)} basic requirements found")
        return local_result
    
    def _cloud_processing_phase(self, local_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: Cloud AI processing using Groq API.
        This phase is powerful but requires API calls.
        """
        logger.info("Starting cloud AI processing phase")
        
        if not self.llm_service.is_available:
            logger.warning("Cloud AI service not available, using fallback processing")
            return self._fallback_cloud_processing(local_result)
        
        text = local_result['text_extraction']['original_text']
        
        try:
            # Step 1: Professional requirement extraction (LLM-powered)
            professional_extraction = self._extract_requirements_professionally(text)
            
            # Step 2: Advanced analysis and enrichment
            analysis_results = self._perform_advanced_analysis(text, professional_extraction)
            
            # Step 3: Organization and structuring
            organized_requirements = self._organize_requirements(professional_extraction, text)
            
            cloud_result = {
                'professional_extraction': professional_extraction,
                'advanced_analysis': analysis_results,
                'organized_requirements': organized_requirements,
                'processing_phase': 'cloud_completed',
                'cloud_ai_available': True
            }
            
            logger.info(f"Cloud processing completed: {len(professional_extraction)} professional requirements")
            return cloud_result
            
        except Exception as e:
            logger.error(f"Cloud processing failed: {e}")
            return self._fallback_cloud_processing(local_result)
    
    def _extract_requirements_professionally(self, text: str) -> List[Dict[str, Any]]:
        """Extract requirements using professional LLM prompts with enhanced filtering."""
        try:
            # First clean the text more aggressively
            cleaned_text = self.local_processor.clean_text(text)
            
            # Use the professional extraction from requirement_organizer
            extracted = self.requirement_organizer.extract_professional_requirements(
                cleaned_text, use_llm=True
            )
            
            # Post-process to filter out remaining noise and improve quality
            filtered_requirements = []
            for req in extracted:
                if self._is_valid_requirement(req.get('original_text', '')):
                    # Further clean the requirement text
                    req['original_text'] = self._clean_requirement_text(req.get('original_text', ''))
                    req['current_text'] = req['original_text']
                    filtered_requirements.append(req)
                else:
                    logger.debug(f"Filtered out invalid requirement: {req.get('original_text', '')[:100]}")
            
            logger.info(f"Extracted {len(filtered_requirements)} valid requirements from {len(extracted)} total")
            return filtered_requirements
            
        except Exception as e:
            logger.error(f"Professional extraction failed: {e}")
            # Fallback to basic requirements with enhanced filtering
            return self._extract_requirements_fallback(text)
    
    def _is_valid_requirement(self, text: str) -> bool:
        """Check if text is a valid requirement."""
        if not text or len(text.strip()) < 10:
            return False
        
        text_lower = text.lower().strip()
        
        # Must contain at least one modal verb
        modal_verbs = ['shall', 'must', 'should', 'will', 'may', 'might', 'could', 'can']
        if not any(modal in text_lower for modal in modal_verbs):
            return False
        
        # Filter out obvious document structure content (be more selective)
        strong_noise_indicators = [
            'this document details', 'this specification', 'the following section',
            'table 63:', 'figure 1:', 'section 2 –', 'appendix', 'glossary'
        ]
        
        if any(noise in text_lower for noise in strong_noise_indicators):
            return False
        
        # Only filter out table/figure references if they're the main content
        if re.match(r'^\s*(table|figure)\s+\d+', text_lower):
            return False
        
        return True
    
    def _clean_requirement_text(self, text: str) -> str:
        """Clean individual requirement text."""
        # Fix any remaining duplicate modal verbs
        text = re.sub(r'(shall|must|will|should|may|might|could|can)\1+', r'\1', text, flags=re.IGNORECASE)
        
        # Remove leading/trailing noise
        text = re.sub(r'^(?:The\s+)?(?:system|application|software)\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*(?:\.|\s)*$', '.', text)
        
        # Ensure it starts with "The system" for consistency
        if not text.lower().startswith('the system'):
            text = f"The system {text[0].lower()}{text[1:]}"
        
        # Clean up extra spaces and punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\.+\.', '.', text)
        
        return text.strip()
    
    def _extract_requirements_fallback(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced fallback requirement extraction when cloud AI is unavailable."""
        # Clean text first
        cleaned_text = self.local_processor.clean_text(text)
        
        # Enhanced local extraction - find requirement patterns directly
        requirements = self._extract_requirements_locally(cleaned_text)
        
        # Filter and enhance
        filtered_reqs = []
        for i, req_text in enumerate(requirements):
            if self._is_valid_requirement(req_text):
                cleaned_req = self._clean_requirement_text(req_text)
                req = {
                    'original_text': cleaned_req,
                    'current_text': cleaned_req,
                    'category': self._categorize_requirement(cleaned_req),
                    'category_confidence': 0.7,
                    'module_name': self._group_requirement_by_module(cleaned_req),
                    'semantic_id': f"FR-{self._get_module_prefix(cleaned_req)}-{i+1:02d}",
                    'actors': self._extract_actors_from_text(cleaned_req),
                    'modal_verbs': self._extract_modal_verbs_from_text(cleaned_req),
                    'vague_terms': self._extract_vague_terms_from_text(cleaned_req),
                    'word_count': len(cleaned_req.split()),
                    'sequence_order': i
                }
                filtered_reqs.append(req)
        
        return filtered_reqs
    
    def _extract_requirements_locally(self, text: str) -> List[str]:
        """Extract requirements using local pattern matching."""
        import re
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        requirements = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            # Check if sentence contains modal verbs indicating requirements
            modal_pattern = r'\b(shall|must|should|will|may)\b'
            if re.search(modal_pattern, sentence, re.IGNORECASE):
                requirements.append(sentence)
        
        return requirements
    
    def _categorize_requirement(self, text: str) -> str:
        """Categorize requirement based on keywords."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['interface', 'api', 'ui', 'user interface', 'screen', 'form']):
            return 'interface'
        elif any(word in text_lower for word in ['performance', 'response time', 'concurrent', 'availability', 'reliability', 'security']):
            return 'non_functional'
        elif any(word in text_lower for word in ['data', 'database', 'storage', 'backup', 'field', 'record']):
            return 'data'
        elif any(word in text_lower for word in ['constraint', 'limit', 'restrict', 'comply', 'standard']):
            return 'constraint'
        else:
            return 'functional'
    
    def _group_requirement_by_module(self, text: str) -> str:
        """Group requirement by module based on keywords."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['user', 'patient', 'customer', 'client']):
            return 'User Management'
        elif any(word in text_lower for word in ['auth', 'login', 'password', 'session', 'token']):
            return 'Authentication'
        elif any(word in text_lower for word in ['payment', 'billing', 'invoice', 'transaction']):
            return 'Payment & Billing'
        elif any(word in text_lower for word in ['appointment', 'schedule', 'booking', 'calendar']):
            return 'Appointment & Scheduling'
        elif any(word in text_lower for word in ['notification', 'email', 'alert', 'message']):
            return 'Notification & Communication'
        elif any(word in text_lower for word in ['audit', 'log', 'track', 'monitor']):
            return 'Audit & Logging'
        elif any(word in text_lower for word in ['admin', 'administrator', 'manage', 'configuration']):
            return 'System Administration'
        elif any(word in text_lower for word in ['performance', 'scalability', 'load', 'concurrent']):
            return 'Performance & Scalability'
        elif any(word in text_lower for word in ['security', 'encrypt', 'protect', 'privacy']):
            return 'Data Security & Compliance'
        else:
            return 'General'
    
    def _get_module_prefix(self, text: str) -> str:
        """Get module prefix for semantic ID."""
        module = self._group_requirement_by_module(text)
        prefixes = {
            'User Management': 'UM',
            'Authentication': 'AU',
            'Payment & Billing': 'PA',
            'Appointment & Scheduling': 'AP',
            'Notification & Communication': 'NO',
            'Audit & Logging': 'AU',
            'System Administration': 'SY',
            'Performance & Scalability': 'PE',
            'Data Security & Compliance': 'DA',
            'General': 'GE'
        }
        return prefixes.get(module, 'GE')
    
    def _extract_actors_from_text(self, text: str) -> List[str]:
        """Extract actors from requirement text."""
        actors = []
        text_lower = text.lower()
        
        actor_keywords = {
            'user': ['user', 'customer', 'client', 'patient', 'student', 'employee'],
            'admin': ['admin', 'administrator', 'manager', 'supervisor', 'operator'],
            'system': ['system', 'application', 'software', 'api', 'database', 'server'],
            'doctor': ['doctor', 'physician', 'medical staff'],
            'chemist': ['chemist', 'pharmacist', 'pharmacy'],
            'lab': ['lab', 'laboratory', 'lab technician']
        }
        
        for actor_type, keywords in actor_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                actors.append(actor_type.title())
        
        return list(set(actors))
    
    def _extract_modal_verbs_from_text(self, text: str) -> List[str]:
        """Extract modal verbs from requirement text."""
        import re
        modal_verbs = ['shall', 'must', 'should', 'will', 'may', 'might', 'could', 'can']
        found = []
        
        for modal in modal_verbs:
            if re.search(rf'\b{modal}\b', text, re.IGNORECASE):
                found.append(modal)
        
        return list(set(found))
    
    def _extract_vague_terms_from_text(self, text: str) -> List[str]:
        """Extract vague terms from requirement text."""
        vague_terms = [
            'appropriate', 'reasonable', 'timely', 'adequate', 'suitable', 'user-friendly',
            'efficient', 'fast', 'quick', 'easy', 'good', 'large', 'small', 'many', 'few'
        ]
        
        text_lower = text.lower()
        found = []
        
        for vague in vague_terms:
            if vague in text_lower:
                found.append(vague)
        
        return list(set(found))
    
    def _perform_advanced_analysis(self, text: str, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform advanced analysis using cloud AI."""
        analysis = {}
        
        # Combine requirement texts for analysis
        req_texts = [req.get('original_text', '') for req in requirements]
        combined_text = '\n'.join(req_texts)
        
        try:
            # Ambiguity detection
            analysis['ambiguity_analysis'] = self.llm_service.analyze_ambiguity(combined_text)
        except Exception as e:
            logger.warning(f"Ambiguity analysis failed: {e}")
            analysis['ambiguity_analysis'] = {'defects': []}
        
        try:
            # Complexity estimation
            analysis['complexity_analysis'] = self.llm_service.estimate_complexity(combined_text)
        except Exception as e:
            logger.warning(f"Complexity analysis failed: {e}")
            analysis['complexity_analysis'] = {'complexity_score': 0}
        
        return analysis
    
    def _organize_requirements(self, requirements: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Organize and enrich requirements using both local and cloud insights."""
        try:
            # Use requirement organizer for final enrichment
            organized = self.requirement_organizer.organize_and_enrich(
                requirements, text, use_llm=True
            )
            return organized
        except Exception as e:
            logger.warning(f"Requirement organization failed: {e}")
            return requirements
    
    def _fallback_cloud_processing(self, local_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback processing when cloud AI is not available."""
        logger.info("Using fallback cloud processing (rule-based only)")
        
        basic_requirements = local_result['basic_requirements']
        text = local_result['text_extraction']['original_text']
        
        # Use requirement organizer with LLM disabled
        organized_requirements = self.requirement_organizer.organize_and_enrich(
            basic_requirements, text, use_llm=False
        )
        
        return {
            'professional_extraction': organized_requirements,
            'advanced_analysis': {
                'ambiguity_analysis': {'defects': []},
                'complexity_analysis': {'complexity_score': 0}
            },
            'organized_requirements': organized_requirements,
            'processing_phase': 'fallback_completed',
            'cloud_ai_available': False
        }
    
    def _integrate_results(self, local_result: Dict[str, Any], cloud_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate local and cloud processing results.
        Combines the best of both approaches.
        """
        logger.info("Integrating local and cloud processing results")
        
        # Get final requirements from cloud processing
        final_requirements = cloud_result.get('organized_requirements', [])
        
        # Enhance with local NLP insights
        local_nlp = local_result.get('local_nlp', {})
        
        # Merge local actor identification with cloud results
        local_actors = local_nlp.get('actors', [])
        local_actor_names = {actor['text'].lower() for actor in local_actors}
        
        for req in final_requirements:
            # Add local processing insights
            req['local_insights'] = {
                'has_vague_terms': any(vague['text'].lower() in req.get('original_text', '').lower() 
                                     for vague in local_nlp.get('vague_terms', [])),
                'modal_verbs_local': [modal['text'] for modal in local_nlp.get('modal_verbs', []) 
                                    if modal['text'].lower() in req.get('original_text', '').lower()],
                'local_actors': [actor for actor in local_actors 
                               if actor['text'].lower() in req.get('original_text', '').lower()]
            }
        
        integrated_result = {
            'document_info': local_result['document_info'],
            'processing_summary': {
                'total_requirements': len(final_requirements),
                'local_processing': {
                    'status': 'completed',
                    'actors_found': len(local_actors),
                    'vague_terms_found': len(local_nlp.get('vague_terms', [])),
                    'modal_verbs_found': len(local_nlp.get('modal_verbs', []))
                },
                'cloud_processing': {
                    'status': cloud_result['processing_phase'],
                    'ai_available': cloud_result.get('cloud_ai_available', False),
                    'ambiguity_defects': len(cloud_result.get('advanced_analysis', {}).get('ambiguity_analysis', {}).get('defects', [])),
                    'complexity_score': cloud_result.get('advanced_analysis', {}).get('complexity_analysis', {}).get('complexity_score', 0)
                }
            },
            'requirements': final_requirements,
            'analysis': cloud_result.get('advanced_analysis', {}),
            'sections': local_result['text_extraction']['sections'],
            'processing_architecture': 'hybrid_local_cloud',
            'performance_metrics': {
                'local_processing_time': 'fast',
                'cloud_processing_time': 'variable',
                'total_phases': 2
            }
        }
        
        logger.info(f"Integration complete: {len(final_requirements)} final requirements")
        return integrated_result
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current status of processing components."""
        return {
            'local_processor': {
                'available': self.local_processor.is_available(),
                'spacy_model_loaded': self.local_processor.nlp is not None
            },
            'cloud_ai': {
                'available': self.llm_service.is_available,
                'service': 'Groq API',
                'model': getattr(self.llm_service, 'model', 'unknown')
            },
            'document_parser': {
                'pymupdf_available': True,  # Should be available based on requirements.txt
                'supported_formats': ['pdf', 'docx', 'txt']
            }
        }


# Global instance
hybrid_processor = HybridProcessor()
