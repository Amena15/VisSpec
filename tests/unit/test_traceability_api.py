"""Unit tests for traceability API endpoints."""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), '../backend'))

from backend.api.traceability import router, save_traceability_note, get_traceability
from backend.models.user import User
from backend.models.project import Project
from backend.models.requirement import Requirement
from backend.models.traceability import TraceabilityNote


class TestTraceabilityAPI:
    """Test suite for traceability API endpoints."""
    
    def test_get_traceability_success(self, db_session):
        """Test successful traceability data retrieval."""
        # Create mock user and project
        mock_user = Mock(spec=User)
        mock_user.user_id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.is_active = 1
        
        # Create mock project
        mock_project = Mock(spec=Project)
        mock_project.project_id = "test-project-id"
        mock_project.owner_id = "test-user-id"
        
        # Create mock requirements
        mock_req1 = Mock(spec=Requirement)
        mock_req1.req_id = "req-1"
        mock_req1.project_id = "test-project-id"
        mock_req1.current_text = "Test requirement 1"
        mock_req1.original_text = "Original test requirement 1"
        mock_req1.sequence_order = 0
        
        mock_req2 = Mock(spec=Requirement)
        mock_req2.req_id = "req-2"
        mock_req2.project_id = "test-project-id"
        mock_req2.current_text = "Test requirement 2"
        mock_req2.original_text = "Original test requirement 2"
        mock_req2.sequence_order = 1
        
        # Mock database queries
        with patch('backend.api.traceability.db.query') as mock_query:
            mock_query.return_value.all.return_value = [mock_req1, mock_req2]
            
            with patch('backend.api.traceability.logger') as mock_logger:
                # Call the actual function
                result = get_traceability("test-project-id", mock_user, db_session)
                
                # Assertions
                assert result.project_id == "test-project-id"
                assert len(result.traceability) == 2
                assert result.traceability[0].req_id == "req-1"
                assert result.traceability[0].text == "Test requirement 1"
                assert result.traceability[1].req_id == "req-2"
                assert result.traceability[1].text == "Test requirement 2"
                
                print("✅ test_get_traceability_success passed")
                return True
    
    def test_save_note_success(self, db_session):
        """Test successful note saving."""
        # Create mock data
        mock_user = Mock(spec=User)
        mock_user.user_id = "test-user-id"
        
        mock_requirement = Mock(spec=Requirement)
        mock_requirement.req_id = "req-1"
        mock_requirement.project_id = "test-project-id"
        
        mock_note_data = Mock()
        mock_note_data.req_id = "req-1"
        mock_note_data.content = "Test note content"
        
        # Mock existing note
        mock_existing_note = Mock(spec=TraceabilityNote)
        mock_existing_note.note_id = "note-1"
        mock_existing_note.content = "Existing note"
        
        # Mock database queries
        with patch('backend.api.traceability.db.query') as mock_query:
            # Mock requirement query
            mock_query.return_value.filter.return_value.filter.return_value.first.return_value = mock_requirement
            
            # Mock existing note query
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_existing_note
            
            # Mock database operations
            with patch('backend.api.traceability.db.commit') as mock_commit:
                with patch('backend.api.traceability.db.refresh') as mock_refresh:
                    # Call the actual function
                    result = save_traceability_note(mock_note_data, mock_user, db_session)
                    
                    # Assertions
                    assert result.success is True
                    assert result.note_id == "note-1"
                    assert result.content == "Test note content"
                    
                    print("✅ test_save_note_success passed")
                    return True
    
    def test_save_note_requirement_not_found(self, db_session):
        """Test note saving when requirement not found."""
        # Create mock data
        mock_user = Mock(spec=User)
        mock_user.user_id = "test-user-id"
        
        mock_note_data = Mock()
        mock_note_data.req_id = "non-existent-req"
        mock_note_data.content = "Test note content"
        
        # Mock database query - requirement not found
        with patch('backend.api.traceability.db.query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            
            # Call the actual function
            result = save_traceability_note(mock_note_data, mock_user, db_session)
            
            # Should raise HTTPException for requirement not found
            assert result.success is False
            assert "Requirement not found" in result.detail
            
            print("✅ test_save_note_requirement_not_found passed")
            return True
    
    def test_api_error_handling(self, db_session):
        """Test API error handling."""
        # Create mock data
        mock_user = Mock(spec=User)
        mock_user.user_id = "test-user-id"
        
        # Mock database exception
        with patch('backend.api.traceability.db.query') as mock_query:
            mock_query.side_effect = Exception("Database connection failed")
            
            # Call the actual function
            with pytest.raises(Exception) as exc_info:
                get_traceability("test-project-id", mock_user, db_session)
            
            # Verify exception was raised
            assert "Failed to retrieve traceability data" in str(exc_info.value)
            
            print("✅ test_api_error_handling passed")
            return True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__], verbose=True)
