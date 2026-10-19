"""
IEEE-Compliant Diagram Generation Service.

Main service that orchestrates the complete diagram generation workflow:
1. Requirement enrichment with LLM
2. Diagram element mapping (Use Case, Sequence, Activity)
3. PlantUML syntax generation
4. Database storage with traceability
5. Accuracy compliance checks (BR-11, BR-12)
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.diagram.requirement_enrichment import RequirementEnrichmentService
from backend.services.diagram.usecase_mapper import UseCaseMapper
from backend.services.diagram.sequence_mapper import SequenceMapper
from backend.services.diagram.activity_mapper import ActivityMapper
from backend.services.diagram.plantuml_generator import PlantUMLGenerator
# Shared traceability-enforcement predicates (single source of truth with
# scripts/04_rq3_traceability_experiment.py, so the RQ3 experiment measures the
# exact mechanism the application ships).
from backend.services.diagram.traceability_enforcement import grounded_actor, grounded_message
from backend.models.diagram import Diagram, DiagramElement
from backend.models.requirement import Requirement
from backend.models.validation import ValidationSession
from backend.core.logging import get_logger

logger = get_logger(__name__)


class DiagramGenerationService:
    """Main service for IEEE-compliant diagram generation."""
    
    def __init__(self):
        self.enrichment_service = RequirementEnrichmentService()
        self.usecase_mapper = UseCaseMapper()
        self.sequence_mapper = SequenceMapper()
        self.activity_mapper = ActivityMapper()
        self.plantuml_generator = PlantUMLGenerator()
    
    def generate_diagram(
        self,
        db: Session,
        project_id: str,
        validation_id: str,
        diagram_type: str,
        scenario: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete IEEE-compliant diagram with full traceability.
        
        Args:
            db: Database session
            project_id: Project identifier
            validation_id: Validation session identifier
            diagram_type: Type of diagram (usecase, sequence, activity)
            scenario: Optional scenario name for sequence diagrams
            
        Returns:
            Dictionary with diagram data and metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Fetch requirements from database
            requirements = self._fetch_requirements(db, project_id, validation_id)
            
            if not requirements:
                return {
                    'success': False,
                    'error': 'No requirements found for this project',
                    'diagram_id': None
                }
            
            # Step 2: Enrich requirements with metadata
            enriched_requirements = self.enrichment_service.enrich_requirements_batch(requirements)
            
            # Step 3: Map to diagram elements based on type
            if diagram_type == 'usecase':
                mapping_data = self.usecase_mapper.map_requirements_to_usecase(enriched_requirements)
            elif diagram_type == 'sequence':
                mapping_data = self.sequence_mapper.map_requirements_to_sequence(enriched_requirements, scenario)
            elif diagram_type == 'activity':
                mapping_data = self.activity_mapper.map_requirements_to_activity(enriched_requirements)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported diagram type: {diagram_type}',
                    'diagram_id': None
                }
            
            # Step 4: Perform accuracy compliance checks FIRST. This runs the real
            # traceability/hallucination check (Stage 5) and mutates `mapping_data`
            # in place, dropping any untraceable nodes before the diagram is drawn.
            compliance_result = self._check_compliance(mapping_data, diagram_type, enriched_requirements)

            # Step 5: Generate PlantUML syntax (only from verified, traceable nodes)
            if diagram_type == 'usecase':
                plantuml_syntax = self.plantuml_generator.generate_usecase_plantuml(mapping_data)
            elif diagram_type == 'sequence':
                plantuml_syntax = self.plantuml_generator.generate_sequence_plantuml(mapping_data)
            elif diagram_type == 'activity':
                plantuml_syntax = self.plantuml_generator.generate_activity_plantuml(mapping_data)

            # Step 6: Store diagram in database
            diagram_id = self._store_diagram(
                db,
                project_id,
                validation_id,
                diagram_type,
                scenario,
                plantuml_syntax,
                mapping_data,
                compliance_result
            )
            
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                'success': True,
                'diagram_id': diagram_id,
                'plantuml_syntax': plantuml_syntax,
                'mapping_data': mapping_data,
                'compliance': compliance_result,
                'generation_time_ms': generation_time_ms,
                'total_elements': len(mapping_data.get('use_cases', [])) + len(mapping_data.get('actors', [])) if diagram_type == 'usecase' else len(mapping_data.get('messages', []))
            }
            
        except Exception as e:
            logger.error(f"Diagram generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'diagram_id': None
            }
    
    def _fetch_requirements(self, db: Session, project_id: str, validation_id: str) -> List[Dict[str, Any]]:
        """Fetch requirements from database for a project and validation session."""
        requirements = db.query(Requirement).filter(
            Requirement.project_id == project_id,
            Requirement.validation_status.in_(['validated', 'passed'])
        ).all()
        
        return [
            {
                'req_id': req.req_id,
                'req_identifier': req.req_identifier,
                'original_text': req.original_text,
                'current_text': req.current_text,
                'actors_json': req.actors_json,
                'modal_verbs_json': req.modal_verbs_json,
                'category': req.category,
                'semantic_id': req.semantic_id,
                'module_name': req.module_name,
                'sequence_order': req.sequence_order
            }
            for req in requirements
        ]
    
    def _check_compliance(
        self,
        mapping_data: Dict[str, Any],
        diagram_type: str,
        enriched_requirements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform accuracy compliance checks AND real traceability (Stage 5) enforcement.

        BR-11: No hallucinated actors/use cases — every node must be traceable to a
               requirement that actually exists in the enriched requirement list.
        BR-12: Maximum 15 steps for sequence diagrams.

        This method MUTATES `mapping_data` in place: any actor or use case whose
        traceability link is null or invalid is dropped from the diagram so it can
        never be rendered in the PlantUML/Mermaid syntax. The number of dropped
        (rejected) nodes is returned as `hallucination_rejected_count` and persisted
        by the caller — a genuine measured value, not a hardcoded 0.
        """
        compliance_result = {
            'br_11_compliant': True,
            'br_12_compliant': True,
            'warnings': [],
            'errors': [],
            'hallucination_rejected_count': 0,
            'rejected_elements': [],
            'rejected_nodes': [],  # full node dicts, persisted as was_hallucination=1
        }

        # Build the set of valid, traceable requirement IDs from the enriched
        # requirement list. Any node whose source_req_id is not in this set is a
        # hallucination (an invented element with no grounding requirement).
        valid_req_ids = {
            req.get('req_id') for req in enriched_requirements
            if req.get('req_id') is not None
        }

        # For actor validation: collect every actor name actually mentioned in the
        # source requirements' actors_json, so an invented actor is detectable.
        source_actor_names = set()
        for req in enriched_requirements:
            actors_json = req.get('actors_json', '[]')
            try:
                actors = json.loads(actors_json) if isinstance(actors_json, str) else actors_json
                for actor in actors or []:
                    if isinstance(actor, str):
                        source_actor_names.add(actor.strip().lower())
                    elif isinstance(actor, dict) and actor.get('name'):
                        source_actor_names.add(str(actor['name']).strip().lower())
            except (json.JSONDecodeError, TypeError):
                continue

        def _is_traceable(node: Dict[str, Any]) -> bool:
            """A use case / message / activity node is traceable iff it carries a
            source_req_id that exists in the enriched requirement list."""
            src = node.get('source_req_id')
            return src is not None and src in valid_req_ids

        # Requirement text per req_id, used by the lexical grounding checks that
        # the RQ3 experiment (scripts/04) also applies via traceability_enforcement.
        req_texts: Dict[str, str] = {}
        for req in enriched_requirements:
            rid = req.get('req_id')
            txt = req.get('current_text') or req.get('original_text') or req.get('text')
            if rid is not None and txt:
                req_texts[rid] = txt

        if diagram_type == 'usecase':
            # --- BR-11: drop untraceable USE CASES (null / invalid source_req_id) ---
            kept_use_cases = []
            for uc in mapping_data.get('use_cases', []):
                if _is_traceable(uc):
                    kept_use_cases.append(uc)
                else:
                    compliance_result['hallucination_rejected_count'] += 1
                    compliance_result['rejected_elements'].append(
                        f"use_case:{uc.get('name', '?')}"
                    )
                    compliance_result['rejected_nodes'].append({
                        'element_type': 'use_case',
                        'element_name': uc.get('name'),
                        'source_req_id': uc.get('source_req_id'),
                    })
            mapping_data['use_cases'] = kept_use_cases

            # --- BR-11: drop actors not grounded in any requirement ---
            # Two grounding signals (same predicates the RQ3 experiment measures
            # via traceability_enforcement): the actor name appears in the
            # requirements' actors_json, OR its tokens appear in requirement text.
            # If the requirement set provided no actors at all, keep the mapper's
            # actors to avoid emptying the diagram.
            kept_actors = []
            for actor in mapping_data.get('actors', []):
                name = actor.get('name') if isinstance(actor, dict) else str(actor)
                grounded = (
                    (not source_actor_names)
                    or (str(name).strip().lower() in source_actor_names)
                    or (bool(req_texts) and grounded_actor(str(name), req_texts))
                )
                if grounded:
                    kept_actors.append(actor)
                else:
                    compliance_result['hallucination_rejected_count'] += 1
                    compliance_result['rejected_elements'].append(f"actor:{name}")
                    compliance_result['rejected_nodes'].append({
                        'element_type': 'actor',
                        'element_name': name,
                        'source_req_id': None,
                    })
            mapping_data['actors'] = kept_actors

            # Prune associations that reference dropped nodes.
            kept_uc_names = {uc.get('name') for uc in kept_use_cases}
            kept_actor_names = {
                (a.get('name') if isinstance(a, dict) else str(a)) for a in kept_actors
            }
            mapping_data['associations'] = [
                a for a in mapping_data.get('associations', [])
                if a.get('use_case') in kept_uc_names and a.get('actor') in kept_actor_names
            ]

            if not mapping_data['actors']:
                compliance_result['warnings'].append('No traceable actors found in use case diagram')
            if not mapping_data['use_cases']:
                compliance_result['warnings'].append('No traceable use cases found in use case diagram')

        elif diagram_type == 'sequence':
            # BR-12: Check step limit
            messages = mapping_data.get('messages', [])
            if len(messages) > 15:
                compliance_result['br_12_compliant'] = False
                compliance_result['errors'].append(f'Sequence diagram exceeds 15 steps: {len(messages)} steps')

            if mapping_data.get('truncated'):
                compliance_result['warnings'].append('Sequence diagram was truncated to 15 steps (BR-12)')

            # Stage 5 traceability: drop messages with no valid source requirement,
            # or whose text is not lexically grounded in the cited requirement
            # (same grounded_message predicate the RQ3 experiment applies).
            kept_messages = []
            for msg in messages:
                src = msg.get('source_req_id')
                lexically_grounded = (
                    not req_texts or grounded_message(str(msg.get('message', '')), src, req_texts)
                )
                if _is_traceable(msg) and lexically_grounded:
                    kept_messages.append(msg)
                else:
                    compliance_result['hallucination_rejected_count'] += 1
                    compliance_result['rejected_elements'].append(
                        f"message:{msg.get('message', '?')[:40]}"
                    )
                    compliance_result['rejected_nodes'].append({
                        'element_type': 'message',
                        'element_name': msg.get('message'),
                        'source_req_id': msg.get('source_req_id'),
                    })
            mapping_data['messages'] = kept_messages

        elif diagram_type == 'activity':
            # Stage 5 traceability: drop activities with no valid source requirement.
            kept_activities = []
            for act in mapping_data.get('activities', []):
                if _is_traceable(act):
                    kept_activities.append(act)
                else:
                    compliance_result['hallucination_rejected_count'] += 1
                    compliance_result['rejected_elements'].append(
                        f"activity:{act.get('name', '?')}"
                    )
                    compliance_result['rejected_nodes'].append({
                        'element_type': 'activity',
                        'element_name': act.get('name'),
                        'source_req_id': act.get('source_req_id'),
                    })
            mapping_data['activities'] = kept_activities

        # BR-11 is non-compliant if we had to reject any untraceable node.
        if compliance_result['hallucination_rejected_count'] > 0:
            compliance_result['br_11_compliant'] = False
            compliance_result['warnings'].append(
                f"Rejected {compliance_result['hallucination_rejected_count']} "
                f"untraceable element(s): {', '.join(compliance_result['rejected_elements'][:5])}"
            )

        return compliance_result
    
    def _store_diagram(
        self,
        db: Session,
        project_id: str,
        validation_id: str,
        diagram_type: str,
        scenario: Optional[str],
        plantuml_syntax: str,
        mapping_data: Dict[str, Any],
        compliance_result: Dict[str, Any]
    ) -> str:
        """Store diagram and elements in database with full traceability."""
        # Create diagram record
        diagram = Diagram(
            project_id=project_id,
            validation_id=validation_id,
            diagram_type=diagram_type,
            scenario_name=scenario,
            mermaid_syntax=plantuml_syntax,  # Store PlantUML in mermaid_syntax field for now
            syntax_valid=1 if compliance_result['br_11_compliant'] and compliance_result['br_12_compliant'] else 0,
            total_elements=self._count_elements(mapping_data, diagram_type),
            hallucination_rejected_count=compliance_result.get('hallucination_rejected_count', 0),
            generation_time_ms=None
        )
        
        db.add(diagram)
        db.flush()
        
        # Store diagram elements for traceability (survivors + rejected audit trail)
        self._store_diagram_elements(db, diagram.diagram_id, mapping_data, diagram_type, compliance_result)
        
        db.commit()
        
        return diagram.diagram_id
    
    def _count_elements(self, mapping_data: Dict[str, Any], diagram_type: str) -> int:
        """Count total elements in mapping data."""
        if diagram_type == 'usecase':
            return len(mapping_data.get('actors', [])) + len(mapping_data.get('use_cases', []))
        elif diagram_type == 'sequence':
            return len(mapping_data.get('participants', [])) + len(mapping_data.get('messages', []))
        elif diagram_type == 'activity':
            return len(mapping_data.get('activities', [])) + len(mapping_data.get('decisions', []))
        return 0
    
    def _store_diagram_elements(
        self,
        db: Session,
        diagram_id: str,
        mapping_data: Dict[str, Any],
        diagram_type: str,
        compliance_result: Optional[Dict[str, Any]] = None
    ):
        """Store diagram elements with traceability to requirements.

        Survivors stored here have already passed the Stage-5 traceability check in
        _check_compliance(), so they are recorded with was_hallucination=0 because
        each one is genuinely traceable. Rejected (untraceable) nodes are also
        persisted with was_hallucination=1 to provide a real audit trail that backs
        the hallucination_rejected_count stored on the diagram — the value is
        measured, never hardcoded.
        """
        compliance_result = compliance_result or {}

        if diagram_type == 'usecase':
            # Store use cases (all verified traceable in _check_compliance)
            for use_case in mapping_data.get('use_cases', []):
                element = DiagramElement(
                    diagram_id=diagram_id,
                    source_req_id=use_case.get('source_req_id'),
                    element_type='use_case',
                    element_name=use_case['name'],
                    was_hallucination=0  # survived Stage-5 traceability check
                )
                db.add(element)
            
            # Store actors (validated by name against source requirements)
            for actor in mapping_data.get('actors', []):
                element = DiagramElement(
                    diagram_id=diagram_id,
                    source_req_id=None,  # Actors are derived from multiple requirements
                    element_type='actor',
                    element_name=actor,
                    was_hallucination=0  # survived Stage-5 traceability check
                )
                db.add(element)
        
        elif diagram_type == 'sequence':
            # Store messages (all verified traceable)
            for message in mapping_data.get('messages', []):
                element = DiagramElement(
                    diagram_id=diagram_id,
                    source_req_id=message.get('source_req_id'),
                    element_type='message',
                    element_name=message['message'],
                    was_hallucination=0  # survived Stage-5 traceability check
                )
                db.add(element)
            
            # Store participants
            for participant in mapping_data.get('participants', []):
                element = DiagramElement(
                    diagram_id=diagram_id,
                    source_req_id=None,
                    element_type='participant',
                    element_name=participant['name'],
                    was_hallucination=0
                )
                db.add(element)
        
        elif diagram_type == 'activity':
            # Store activities (all verified traceable)
            for activity in mapping_data.get('activities', []):
                element = DiagramElement(
                    diagram_id=diagram_id,
                    source_req_id=activity.get('source_req_id'),
                    element_type='activity',
                    element_name=activity['name'],
                    was_hallucination=0  # survived Stage-5 traceability check
                )
                db.add(element)

        # Persist rejected (untraceable) nodes as a genuine audit trail.
        for node in compliance_result.get('rejected_nodes', []):
            element = DiagramElement(
                diagram_id=diagram_id,
                source_req_id=node.get('source_req_id'),
                element_type=node.get('element_type', 'unknown'),
                element_name=str(node.get('element_name')),
                was_hallucination=1  # rejected by Stage-5: null/invalid source_req_id
            )
            db.add(element)
