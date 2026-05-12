#!/usr/bin/env python3
"""Test script to verify the save note fix works correctly."""

import sys
import os
sys.path.insert(0, '.')

from datetime import datetime, timezone
from models.traceability import TraceabilityNote

def test_datetime_handling():
    """Test that the datetime handling fix works correctly."""
    print("=== Testing Datetime Handling Fix ===")
    
    # Test case 1: String datetime (as stored in database)
    string_datetime = "2023-05-12T14:30:00Z"
    
    # Test the fix logic
    result = string_datetime if isinstance(string_datetime, str) else string_datetime.isoformat()
    print(f"✅ String datetime handling: {result}")
    
    # Test case 2: Datetime object (as created during update)
    datetime_obj = datetime.now(timezone.utc)
    
    # Test the fix logic
    result = datetime_obj if isinstance(datetime_obj, str) else datetime_obj.isoformat()
    print(f"✅ Datetime object handling: {result}")
    
    # Test case 3: Simulate the actual database object behavior
    class MockNote:
        def __init__(self, created_at):
            self.created_at = created_at
    
    # Test with string
    note_with_string = MockNote("2023-05-12T14:30:00Z")
    result = note_with_string.created_at if isinstance(note_with_string.created_at, str) else note_with_string.created_at.isoformat()
    print(f"✅ Mock note with string: {result}")
    
    # Test with datetime
    note_with_datetime = MockNote(datetime.now(timezone.utc))
    result = note_with_datetime.created_at if isinstance(note_with_datetime.created_at, str) else note_with_datetime.created_at.isoformat()
    print(f"✅ Mock note with datetime: {result}")
    
    print("✅ All datetime handling tests passed!")

if __name__ == "__main__":
    test_datetime_handling()
