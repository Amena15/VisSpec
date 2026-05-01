#!/usr/bin/env python3
"""
Unit tests for professional requirements extraction.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from services.ai.requirement_organizer import RequirementOrganizer
from services.ai.llm_service import GroqLLMService
from core.logging import get_logger

logger = get_logger(__name__)

def test_extract_professional_requirements():
    """Test the professional requirements extraction method."""
    print("Testing professional requirements extraction...")
    
    # Initialize the organizer
    organizer = RequirementOrganizer()
    
    # Test case 1: Simple functional requirement
    test_text_1 = "The system shall support user authentication."
    print(f"\nTest 1: Simple functional requirement")
    print(f"Input: {test_text_1}")
    
    try:
        result = organizer.extract_professional_requirements(test_text_1, use_llm=True)
        print(f"Result: {len(result)} requirements extracted")
        
        if result:
            for i, req in enumerate(result[:3]):  # Show first 3 results
                print(f"  {i+1}. Original: {req.get('original_text', 'N/A')}")
                print(f"  {i+1}. Category: {req.get('category', 'N/A')}")
                print(f"  {i+1}. Module: {req.get('module_name', 'N/A')}")
                print(f"  {i+1}. Semantic ID: {req.get('semantic_id', 'N/A')}")
        else:
            print("  No requirements extracted")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Test case 2: Mixed content with noise
    test_text_2 = """
    Table 1: Requirements Overview
    This document contains system requirements.
    
    The system shall process user data securely.
    Figure 1: System Architecture
    """
    print(f"\nTest 2: Mixed content with noise")
    print(f"Input: {test_text_2[:100]}...")
    
    try:
        result = organizer.extract_professional_requirements(test_text_2, use_llm=True)
        print(f"Result: {len(result)} requirements extracted")
        
        if result:
            for i, req in enumerate(result[:3]):  # Show first 3 results
                print(f"  {i+1}. Original: {req.get('original_text', 'N/A')}")
                print(f"  {i+1}. Category: {req.get('category', 'N/A')}")
                print(f"  {i+1}. Module: {req.get('module_name', 'N/A')}")
        else:
            print("  No requirements extracted")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Test case 3: Empty input
    test_text_3 = ""
    print(f"\nTest 3: Empty input")
    print(f"Input: '{test_text_3}'")
    
    try:
        result = organizer.extract_professional_requirements(test_text_3, use_llm=True)
        print(f"Result: {len(result)} requirements extracted")
        print(f"  Expected: 0 requirements (empty input)")
        
        if len(result) == 0:
            print("  ✓ PASS: Correctly handled empty input")
        else:
            print("  ✗ FAIL: Should not extract from empty input")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print()

if __name__ == "__main__":
    test_extract_professional_requirements()
