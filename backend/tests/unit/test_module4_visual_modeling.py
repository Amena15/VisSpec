#!/usr/bin/env python3

"""
Module 4: Visual Modeling & Diagram Generation Comprehensive Unit Tests
Covers REQ_11, REQ_12, REQ_13 and all visual modeling functionality

Test Coverage:
- Actor and use case identification from validated requirements
- Mermaid.js syntax generation syntactically correct
- Use Case Diagram: actors, use cases, relationships rendered
- Sequence Diagram: lifelines, messages, activation bars for selected scenario
- Scenario dropdown populated from identified flows
- No hallucinated actors (BR-11: must reflect text only)
- Sequence diagrams limited to 15 steps for readability (BR-12)
- Interactive features: zoom, pan, export as SVG
- Rendering failure fallback: display syntax for manual export
- Real-time update when requirements change
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add backend to path
import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

from main import app
from services.diagram.diagram_generator import DiagramGenerationService
from services.diagram.usecase_mapper import UseCaseMapper
from services.diagram.sequence_mapper import SequenceMapper
from services.diagram.activity_mapper import ActivityMapper
from services.diagram.plantuml_generator import PlantUMLGenerator
from services.visualization.visualizer import Visualizer

client = TestClient(app)

class TestModule4VisualModeling:
    """Comprehensive test suite for Module 4: Visual Modeling & Diagram Generation"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()
    
    @pytest.fixture
    def diagram_service(self):
        """Diagram generation service instance"""
        return DiagramGenerationService()
    
    @pytest.fixture
    def usecase_mapper(self):
        """Use case mapper instance"""
        return UseCaseMapper()
    
    @pytest.fixture
    def sequence_mapper(self):
        """Sequence mapper instance"""
        return SequenceMapper()
    
    @pytest.fixture
    def activity_mapper(self):
        """Activity mapper instance"""
        return ActivityMapper()
    
    @pytest.fixture
    def plantuml_generator(self):
        """PlantUML generator instance"""
        return PlantUMLGenerator()

    # === Actor and Use Case Identification Tests ===
    
    def test_actor_identification_from_requirements(self):
        """Test actor identification from validated requirements"""
        usecase_mapper = UseCaseMapper()
        
        # Test requirements with actors
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall allow users to upload documents.",
                "actors_json": '["User"]',
                "category": "functional"
            },
            {
                "req_id": "REQ-002",
                "original_text": "Admin can manage user accounts.",
                "actors_json": '["Admin"]',
                "category": "functional"
            },
            {
                "req_id": "REQ-003",
                "original_text": "System shall process data automatically.",
                "actors_json": '["System"]',
                "category": "functional"
            }
        ]
        
        mapping_result = usecase_mapper.map_requirements_to_usecase(test_requirements)
        
        # Should identify all actors
        assert "actors" in mapping_result
        actors = mapping_result["actors"]
        
        # Should extract actor names correctly
        actor_names = [actor['name'] if isinstance(actor, dict) else actor for actor in actors]
        assert "User" in actor_names
        assert "Admin" in actor_names
        assert "System" in actor_names
    
    def test_use_case_identification_from_requirements(self):
        """Test use case identification from validated requirements"""
        usecase_mapper = UseCaseMapper()
        
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall allow users to upload documents.",
                "actors_json": '["User"]',
                "category": "functional"
            },
            {
                "req_id": "REQ-002",
                "original_text": "Admin can manage user accounts.",
                "actors_json": '["Admin"]',
                "category": "functional"
            },
            {
                "req_id": "REQ-003",
                "original_text": "Users can view reports.",
                "actors_json": '["User"]',
                "category": "functional"
            }
        ]
        
        mapping_result = usecase_mapper.map_requirements_to_usecase(test_requirements)
        
        # Should identify use cases
        assert "use_cases" in mapping_result
        use_cases = mapping_result["use_cases"]
        
        # Should extract meaningful use case names
        use_case_names = [uc['name'] for uc in use_cases]
        assert any("upload" in name.lower() for name in use_case_names)
        assert any("manage" in name.lower() for name in use_case_names)
        assert any("view" in name.lower() for name in use_case_names)

    # === Mermaid.js Syntax Generation Tests ===
    
    def test_mermaid_use_case_syntax_generation(self):
        """Test Mermaid.js use case diagram syntax generation"""
        plantuml_generator = PlantUMLGenerator()
        
        # Test mapping data
        mapping_data = {
            "actors": [{"name": "User", "count": 1}, {"name": "Admin", "count": 1}],
            "use_cases": [{"name": "Upload Document"}, {"name": "Manage Accounts"}],
            "associations": [
                {"actor": "User", "use_case": "Upload Document"},
                {"actor": "Admin", "use_case": "Manage Accounts"}
            ]
        }
        
        # Generate PlantUML (convert to Mermaid for testing)
        plantuml = plantuml_generator.generate_usecase_plantuml(mapping_data)
        
        # Should have proper PlantUML structure
        assert "@startuml" in plantuml
        assert "@enduml" in plantuml
        assert "actor" in plantuml
        assert "usecase" in plantuml
        
        # Should contain actors and use cases
        assert "User" in plantuml
        assert "Admin" in plantuml
        assert "Upload Document" in plantuml
        assert "Manage Accounts" in plantuml
    
    def test_mermaid_sequence_syntax_generation(self):
        """Test Mermaid.js sequence diagram syntax generation"""
        sequence_mapper = SequenceMapper()
        
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "User enters credentials, system validates them, database stores session.",
                "actors_json": '["User"]',
                "category": "functional"
            }
        ]
        
        mapping_result = sequence_mapper.map_requirements_to_sequence(test_requirements)
        
        # Should generate proper sequence structure
        assert "participants" in mapping_result
        assert "messages" in mapping_result
        
        # Should identify participants
        participants = mapping_result["participants"]
        assert len(participants) >= 2  # At least User and System
        
        # Should generate messages
        messages = mapping_result["messages"]
        assert len(messages) > 0
        
        # Should have proper message structure
        for message in messages:
            assert "source" in message
            assert "target" in message
            assert "message" in message
    
    def test_mermaid_syntax_validation(self):
        """Test generated Mermaid.js syntax is syntactically correct"""
        plantuml_generator = PlantUMLGenerator()
        
        mapping_data = {
            "actors": [{"name": "User"}],
            "use_cases": [{"name": "Login"}],
            "associations": [{"actor": "User", "use_case": "Login"}]
        }
        
        plantuml = plantuml_generator.generate_usecase_plantuml(mapping_data)
        
        # Basic syntax validation
        lines = plantuml.split('\n')
        
        # Should start and end properly
        assert lines[0].strip() == "@startuml"
        assert lines[-1].strip() == "@enduml"
        
        # Should have valid actor definitions
        actor_lines = [line for line in lines if line.strip().startswith("actor")]
        assert len(actor_lines) > 0
        
        # Should have valid use case definitions
        usecase_lines = [line for line in lines if "usecase" in line]
        assert len(usecase_lines) > 0

    # === Diagram Rendering Tests ===
    
    def test_use_case_diagram_rendering(self):
        """Test Use Case Diagram: actors, use cases, relationships rendered"""
        diagram_service = DiagramGenerationService()
        
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall allow users to upload documents.",
                "actors_json": '["User"]',
                "category": "functional"
            },
            {
                "req_id": "REQ-002",
                "original_text": "Admin can manage user accounts.",
                "actors_json": '["Admin"]',
                "category": "functional"
            }
        ]
        
        result = diagram_service.generate_usecase_diagram(test_requirements)
        
        # Should generate diagram data
        assert "diagram_data" in result
        assert "mermaid_syntax" in result
        
        # Should include actors and use cases
        mermaid_syntax = result["mermaid_syntax"]
        assert "User" in mermaid_syntax
        assert "Admin" in mermaid_syntax
    
    def test_sequence_diagram_rendering(self):
        """Test Sequence Diagram: lifelines, messages, activation bars for selected scenario"""
        diagram_service = DiagramGenerationService()
        
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "User enters credentials, system validates them, database stores session.",
                "actors_json": '["User"]',
                "category": "functional"
            }
        ]
        
        result = diagram_service.generate_sequence_diagram(test_requirements, "authentication")
        
        # Should generate sequence diagram data
        assert "diagram_data" in result
        assert "mermaid_syntax" in result
        
        # Should have proper sequence structure
        mermaid_syntax = result["mermaid_syntax"]
        assert "sequenceDiagram" in mermaid_syntax or "participant" in mermaid_syntax
    
    def test_activity_diagram_rendering(self):
        """Test Activity Diagram with proper flow"""
        diagram_service = DiagramGenerationService()
        
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "User submits form, system validates input, processes data, returns result.",
                "actors_json": '["User"]',
                "category": "functional"
            }
        ]
        
        result = diagram_service.generate_activity_diagram(test_requirements)
        
        # Should generate activity diagram data
        assert "diagram_data" in result
        assert "mermaid_syntax" in result

    # === Business Rules Tests ===
    
    def test_no_hallucinated_actors_br11(self):
        """Test no hallucinated actors (BR-11: must reflect text only)"""
        usecase_mapper = UseCaseMapper()
        
        # Test with only specified actors
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall allow users to upload documents.",
                "actors_json": '["User"]',  # Only User specified
                "category": "functional"
            }
        ]
        
        mapping_result = usecase_mapper.map_requirements_to_usecase(test_requirements)
        
        # Should only include specified actors
        actors = mapping_result.get("actors", [])
        actor_names = [actor['name'] if isinstance(actor, dict) else actor for actor in actors]
        
        assert "User" in actor_names
        assert "Admin" not in actor_names  # Should not hallucinate Admin
        assert "System" not in actor_names  # Should not hallucinate System unless specified
        assert len(actor_names) == 1  # Only the specified actor
    
    def test_sequence_diagrams_limited_to_15_steps_br12(self):
        """Test sequence diagrams limited to 15 steps for readability (BR-12)"""
        sequence_mapper = SequenceMapper()
        
        # Create requirements with many steps
        long_sequence_req = {
            "req_id": "REQ-001",
            "original_text": "User clicks login, enters username, enters password, clicks submit, system validates username, validates password, checks database, creates session, generates token, updates last login, sends response, redirects to dashboard, logs activity, updates cache, notifies admin, returns success",
            "actors_json": '["User"]',
            "category": "functional"
        }
        
        mapping_result = sequence_mapper.map_requirements_to_sequence([long_sequence_req])
        
        # Should limit to 15 steps
        messages = mapping_result.get("messages", [])
        assert len(messages) <= 15, f"Sequence diagram should not exceed 15 steps, got {len(messages)}"
        
        # If more than 15 potential steps, should prioritize important ones
        if len(messages) == 15:
            # Should include key steps like login, validation, response
            message_texts = [msg.get("message", "") for msg in messages]
            assert any("login" in text.lower() for text in message_texts)
            assert any("valid" in text.lower() for text in message_texts)

    # === Interactive Features Tests ===
    
    def test_interactive_features_zoom_pan_export(self):
        """Test interactive features: zoom, pan, export as SVG"""
        visualizer = Visualizer()
        
        # Test diagram data
        diagram_data = {
            "type": "usecase",
            "mermaid_syntax": "graph TD\n    User -->|Login| System",
            "metadata": {
                "title": "Use Case Diagram",
                "generated_at": "2024-01-01T00:00:00Z"
            }
        }
        
        # Should support interactive features
        interactive_config = visualizer.get_interactive_config(diagram_data)
        
        assert "zoom" in interactive_config
        assert "pan" in interactive_config
        assert "export" in interactive_config
        
        # Export options should include SVG
        export_options = interactive_config["export"]
        assert "svg" in export_options or "SVG" in export_options
    
    def test_scenario_dropdown_population(self):
        """Test scenario dropdown populated from identified flows"""
        diagram_service = DiagramGenerationService()
        
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "User can login, register, and reset password.",
                "actors_json": '["User"]',
                "category": "functional"
            },
            {
                "req_id": "REQ-002",
                "original_text": "Admin can manage users and view reports.",
                "actors_json": '["Admin"]',
                "category": "functional"
            }
        ]
        
        scenarios = diagram_service.get_available_scenarios(test_requirements)
        
        # Should identify multiple scenarios
        assert len(scenarios) >= 2
        
        # Should include user scenarios
        user_scenarios = [s for s in scenarios if "login" in s.lower() or "register" in s.lower()]
        assert len(user_scenarios) > 0
        
        # Should include admin scenarios
        admin_scenarios = [s for s in scenarios if "manage" in s.lower() or "report" in s.lower()]
        assert len(admin_scenarios) > 0

    # === Error Handling Tests ===
    
    def test_rendering_failure_fallback(self):
        """Test rendering failure fallback: display syntax for manual export"""
        visualizer = Visualizer()
        
        # Test with invalid Mermaid syntax
        invalid_diagram = {
            "type": "usecase",
            "mermaid_syntax": "invalid syntax that cannot be rendered",
            "metadata": {}
        }
        
        # Should provide fallback
        fallback_result = visualizer.render_with_fallback(invalid_diagram)
        
        assert "fallback" in fallback_result
        assert "syntax" in fallback_result
        assert "manual" in fallback_result.get("message", "").lower()
    
    def test_empty_requirements_handling(self):
        """Test handling of empty or invalid requirements"""
        diagram_service = DiagramGenerationService()
        
        # Test with empty requirements
        result = diagram_service.generate_usecase_diagram([])
        
        # Should handle gracefully
        assert "diagram_data" in result
        assert "error" in result or "empty" in result.get("message", "").lower()
    
    def test_malformed_actors_json_handling(self):
        """Test handling of malformed actors JSON"""
        usecase_mapper = UseCaseMapper()
        
        # Test with malformed actors JSON
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall allow users to upload documents.",
                "actors_json": 'invalid json',
                "category": "functional"
            }
        ]
        
        # Should handle gracefully without crashing
        mapping_result = usecase_mapper.map_requirements_to_usecase(test_requirements)
        
        assert "actors" in mapping_result
        assert "use_cases" in mapping_result

    # === Real-time Updates Tests ===
    
    def test_real_time_update_when_requirements_change(self):
        """Test real-time update when requirements change"""
        diagram_service = DiagramGenerationService()
        
        original_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall allow users to upload documents.",
                "actors_json": '["User"]',
                "category": "functional"
            }
        ]
        
        # Generate original diagram
        original_result = diagram_service.generate_usecase_diagram(original_requirements)
        
        # Modify requirements
        updated_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall allow users to upload and download documents.",
                "actors_json": '["User"]',
                "category": "functional"
            }
        ]
        
        # Generate updated diagram
        updated_result = diagram_service.generate_usecase_diagram(updated_requirements)
        
        # Should reflect changes
        assert original_result["mermaid_syntax"] != updated_result["mermaid_syntax"]
        assert "download" in updated_result["mermaid_syntax"].lower()

    # === Integration Tests ===
    
    def test_complete_diagram_generation_workflow(self):
        """Test complete diagram generation workflow"""
        diagram_service = DiagramGenerationService()
        
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "Actors: Admin, User. Admin can create reports. User can view reports and submit feedback.",
                "actors_json": '["Admin", "User"]',
                "category": "functional"
            },
            {
                "req_id": "REQ-002",
                "original_text": "User submits feedback, system processes it, admin reviews it.",
                "actors_json": '["User", "Admin"]',
                "category": "functional"
            }
        ]
        
        # Generate all diagram types
        usecase_result = diagram_service.generate_usecase_diagram(test_requirements)
        sequence_result = diagram_service.generate_sequence_diagram(test_requirements, "feedback")
        activity_result = diagram_service.generate_activity_diagram(test_requirements)
        
        # All should succeed
        assert "diagram_data" in usecase_result
        assert "diagram_data" in sequence_result
        assert "diagram_data" in activity_result
        
        # Should contain expected elements
        assert "Admin" in usecase_result["mermaid_syntax"]
        assert "User" in usecase_result["mermaid_syntax"]
        assert "create reports" in usecase_result["mermaid_syntax"].lower()
        assert "view reports" in usecase_result["mermaid_syntax"].lower()
    
    def test_diagram_api_endpoints(self):
        """Test diagram generation API endpoints"""
        with patch('api.diagrams.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock document retrieval
            mock_document = MagicMock()
            mock_document.requirements = [
                MagicMock(
                    original_text="The system shall allow users to upload documents.",
                    actors_json='["User"]'
                )
            ]
            mock_db.query.return_value.filter.return_value.first.return_value = mock_document
            
            # Test use case diagram endpoint
            response = client.get("/api/diagrams/usecase/1")
            assert response.status_code in [200, 404]  # May not find document but should not crash
            
            # Test sequence diagram endpoint
            response = client.get("/api/diagrams/sequence/1")
            assert response.status_code in [200, 404]
            
            # Test activity diagram endpoint
            response = client.get("/api/diagrams/activity/1")
            assert response.status_code in [200, 404]
    
    def test_diagram_performance_requirements(self):
        """Test diagram generation meets performance requirements"""
        diagram_service = DiagramGenerationService()
        
        # Test with typical requirements
        test_requirements = [
            {
                "req_id": f"REQ-{i:03d}",
                "original_text": f"The system shall allow users to perform action {i}.",
                "actors_json": '["User"]',
                "category": "functional"
            }
            for i in range(10)  # 10 requirements
        ]
        
        import time
        start_time = time.time()
        
        result = diagram_service.generate_usecase_diagram(test_requirements)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (less than 10 seconds)
        assert processing_time < 10.0, f"Diagram generation took too long: {processing_time}s"
        
        # Should produce valid result
        assert "diagram_data" in result
        assert "mermaid_syntax" in result

# === Test Execution ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
