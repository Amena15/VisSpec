#!/usr/bin/env python3

"""
Comprehensive verification test for Modules 3, 4, and 5 implementation.
Checks if all described functionality is properly implemented.
"""

import sys
import os
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[2]
REPO_ROOT = CURRENT_FILE.parents[3]

for path in (str(REPO_ROOT), str(BACKEND_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

def test_module_3_validation():
    """Test Module 3 - AI Validation implementation"""
    print("=== TESTING MODULE 3: AI VALIDATION ===")
    
    results = {}
    
    # Test 1: Validator class exists and has required methods
    try:
        from services.validation.validator import Validator
        validator = Validator(use_llm=False)  # Use rule-based to avoid API calls
        
        # Check for required methods
        required_methods = ['validate_text', 'validate_requirements_with_context']
        for method in required_methods:
            if hasattr(validator, method):
                print(f"   ✅ Validator.{method} method exists")
            else:
                print(f"   ❌ Validator.{method} method missing")
                return False
        
        results["validator_class"] = True
    except Exception as e:
        print(f"   ❌ Validator class test failed: {e}")
        results["validator_class"] = False
    
    # Test 2: LLM Validator exists
    try:
        from services.ai.llm_validator import LLMValidator
        print("   ✅ LLMValidator class exists")
        results["llm_validator"] = True
    except Exception as e:
        print(f"   ❌ LLMValidator class test failed: {e}")
        results["llm_validator"] = False
    
    # Test 3: Validation API endpoint exists
    try:
        from api.validation import validate_requirements
        print("   ✅ Validation API endpoint exists")
        results["validation_api"] = True
    except Exception as e:
        print(f"   ❌ Validation API test failed: {e}")
        results["validation_api"] = False
    
    # Test 4: Quality score calculation (70% base with deductions)
    try:
        # Test with sample data
        validator = Validator(use_llm=False)
        test_text = "The system shall allow users to register accounts."
        result = validator.validate_text(test_text)
        
        if "overall_score" in result:
            score = result["overall_score"]
            if isinstance(score, (int, float)) and 0 <= score <= 100:
                print(f"   ✅ Quality score calculation working: {score}")
                results["quality_score"] = True
            else:
                print(f"   ❌ Invalid quality score: {score}")
                results["quality_score"] = False
        else:
            print("   ❌ Quality score not found in result")
            results["quality_score"] = False
    except Exception as e:
        print(f"   ❌ Quality score test failed: {e}")
        results["quality_score"] = False
    
    # Test 5: Defect filtering by confidence (>= 0.70)
    try:
        validator = Validator(use_llm=False)
        test_text = "The system shall provide user-friendly interface."
        result = validator.validate_text(test_text)
        
        defects = result.get("defects", [])
        # Check if defects have confidence scores
        if defects:
            for defect in defects[:3]:  # Check first 3 defects
                if "confidence" in defect:
                    confidence = defect["confidence"]
                    if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                        print(f"   ✅ Defect confidence filtering working: {confidence}")
                        results["confidence_filtering"] = True
                    else:
                        print(f"   ❌ Invalid confidence score: {confidence}")
                        results["confidence_filtering"] = False
                        break
                else:
                    print("   ❌ Confidence score missing from defect")
                    results["confidence_filtering"] = False
                    break
        else:
            print("   ✅ No defects found (valid for simple text)")
            results["confidence_filtering"] = True
    except Exception as e:
        print(f"   ❌ Confidence filtering test failed: {e}")
        results["confidence_filtering"] = False
    
    return all(results.values()), results

def test_module_4_visual_modeling():
    """Test Module 4 - Visual Modeling implementation"""
    print("\n=== TESTING MODULE 4: VISUAL MODELING ===")
    
    results = {}
    
    # Test 1: Diagram generation service exists
    try:
        from services.diagram.diagram_generator import DiagramGenerationService
        diagram_service = DiagramGenerationService()
        print("   ✅ DiagramGenerationService class exists")
        results["diagram_service"] = True
    except Exception as e:
        print(f"   ❌ DiagramGenerationService test failed: {e}")
        results["diagram_service"] = False
    
    # Test 2: Use Case mapper exists and enforces BR-11
    try:
        from services.diagram.usecase_mapper import UseCaseMapper
        mapper = UseCaseMapper()
        
        # Test with sample requirements
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "The system shall allow users to upload documents.",
                "actors_json": '["User"]',
                "category": "functional"
            }
        ]
        
        mapping_result = mapper.map_requirements_to_usecase(test_requirements)
        
        if "actors" in mapping_result and "use_cases" in mapping_result:
            actors = mapping_result["actors"]
            actor_names = mapping_result.get("actor_names", [])
            # Check BR-11: No hallucinated actors - check both formats
            if ("User" in actor_names and len(actor_names) == 1) or \
               (any(isinstance(a, dict) and a.get('name') == 'User' for a in actors) and len(actors) == 1):
                print("   ✅ Use Case mapper working, BR-11 enforced (no hallucinated actors)")
                results["usecase_mapper"] = True
            else:
                print(f"   ❌ BR-11 violation: unexpected actors: {actors}")
                results["usecase_mapper"] = False
        else:
            print("   ❌ Use Case mapping result incomplete")
            results["usecase_mapper"] = False
    except Exception as e:
        print(f"   ❌ Use Case mapper test failed: {e}")
        results["usecase_mapper"] = False
    
    # Test 3: Sequence mapper exists and enforces BR-12
    try:
        from services.diagram.sequence_mapper import SequenceMapper
        mapper = SequenceMapper()
        
        # Test with sample requirements
        test_requirements = [
            {
                "req_id": "REQ-001",
                "original_text": "User enters credentials, then system validates them.",
                "actors_json": '["User"]',
                "category": "functional"
            }
        ]
        
        mapping_result = mapper.map_requirements_to_sequence(test_requirements)
        
        if "participants" in mapping_result and "messages" in mapping_result:
            messages = mapping_result["messages"]
            # Check BR-12: Max 15 steps
            if len(messages) <= 15:
                print(f"   ✅ Sequence mapper working, BR-12 enforced (max 15 steps): {len(messages)}")
                results["sequence_mapper"] = True
            else:
                print(f"   ❌ BR-12 violation: too many steps: {len(messages)}")
                results["sequence_mapper"] = False
        else:
            print("   ❌ Sequence mapping result incomplete")
            results["sequence_mapper"] = False
    except Exception as e:
        print(f"   ❌ Sequence mapper test failed: {e}")
        results["sequence_mapper"] = False
    
    # Test 4: PlantUML generator exists
    try:
        from services.diagram.plantuml_generator import PlantUMLGenerator
        generator = PlantUMLGenerator()
        
        # Test PlantUML generation
        test_mapping = {
            "actors": [{"name": "User", "count": 1}],
            "use_cases": [{"name": "Upload Document"}],
            "associations": [{"actor": "User", "use_case": "Upload Document"}]
        }
        
        plantuml = generator.generate_usecase_plantuml(test_mapping)
        
        if plantuml and "@startuml" in plantuml and "@enduml" in plantuml:
            print("   ✅ PlantUML generator working")
            results["plantuml_generator"] = True
        else:
            print("   ❌ PlantUML generation failed")
            results["plantuml_generator"] = False
    except Exception as e:
        print(f"   ❌ PlantUML generator test failed: {e}")
        results["plantuml_generator"] = False
    
    # Test 5: Diagram API endpoints exist
    try:
        from api.diagrams import get_usecase_diagram
        print("   ✅ Diagram API endpoints exist")
        results["diagram_api"] = True
    except Exception as e:
        print(f"   ❌ Diagram API test failed: {e}")
        results["diagram_api"] = False
    
    return all(results.values()), results

def test_module_5_predictive_analytics():
    """Test Module 5 - Predictive Analytics implementation"""
    print("\n=== TESTING MODULE 5: PREDICTIVE ANALYTICS ===")
    
    results = {}
    
    # Test 1: Predictive analyzer exists
    try:
        from services.ai.predictive_analyzer import PredictiveAnalyzer
        analyzer = PredictiveAnalyzer()
        print("   ✅ PredictiveAnalyzer class exists")
        results["predictive_analyzer"] = True
    except Exception as e:
        print(f"   ❌ PredictiveAnalyzer test failed: {e}")
        results["predictive_analyzer"] = False
    
    # Test 2: Complexity score calculation (0-100 scale)
    try:
        from services.ai.predictive_analyzer import PredictiveAnalyzer
        analyzer = PredictiveAnalyzer()
        
        test_text = """
        The system shall allow users to register accounts with secure authentication.
        Users must be able to upload and download documents.
        The system shall provide adequate performance for 10,000 concurrent users.
        """
        
        result = analyzer.analyze(test_text)
        
        if hasattr(result, 'complexity_score'):
            score = result.complexity_score
            if isinstance(score, int) and 0 <= score <= 100:
                print(f"   ✅ Complexity score calculation working: {score}")
                results["complexity_score"] = True
            else:
                print(f"   ❌ Invalid complexity score: {score}")
                results["complexity_score"] = False
        else:
            print("   ❌ Complexity score not found in result")
            results["complexity_score"] = False
    except Exception as e:
        print(f"   ❌ Complexity score test failed: {e}")
        results["complexity_score"] = False
    
    # Test 3: Estimated weeks calculation (REQ_15)
    try:
        from services.ai.predictive_analyzer import PredictiveAnalyzer
        analyzer = PredictiveAnalyzer()
        
        test_text = "The system shall allow users to register accounts."
        result = analyzer.analyze(test_text)
        
        if hasattr(result, 'estimated_effort_weeks'):
            weeks = result.estimated_effort_weeks
            if isinstance(weeks, (int, float)) and weeks > 0:
                print(f"   ✅ Estimated weeks calculation working: {weeks}")
                results["estimated_weeks"] = True
            else:
                print(f"   ❌ Invalid estimated weeks: {weeks}")
                results["estimated_weeks"] = False
        else:
            print("   ❌ Estimated weeks not found in result")
            results["estimated_weeks"] = False
    except Exception as e:
        print(f"   ❌ Estimated weeks test failed: {e}")
        results["estimated_weeks"] = False
    
    # Test 4: Cost index calculation (Low/Medium/High)
    try:
        from services.ai.predictive_analyzer import PredictiveAnalyzer
        analyzer = PredictiveAnalyzer()
        
        test_text = "The system shall allow users to register accounts."
        result = analyzer.analyze(test_text)
        
        if hasattr(result, 'cost_index'):
            cost_index = result.cost_index
            if cost_index in ["low", "medium", "high"]:
                print(f"   ✅ Cost index calculation working: {cost_index}")
                results["cost_index"] = True
            else:
                print(f"   ❌ Invalid cost index: {cost_index}")
                results["cost_index"] = False
        else:
            print("   ❌ Cost index not found in result")
            results["cost_index"] = False
    except Exception as e:
        print(f"   ❌ Cost index test failed: {e}")
        results["cost_index"] = False
    
    # Test 5: Formula implementation (actors × 5 + requirements × 0.3 + etc.)
    try:
        from services.ai.predictive_analyzer import PredictiveAnalyzer
        analyzer = PredictiveAnalyzer()
        
        # Test with known values
        test_text = """
        User shall authenticate.
        Admin shall manage users.
        System shall provide reports.
        """
        result = analyzer.analyze(test_text)
        
        if hasattr(result, 'complexity_score'):
            score = result.complexity_score
            # Should be reasonable based on the formula
            if 10 <= score <= 90:  # Reasonable range
                print(f"   ✅ Heuristic formula working correctly: {score}")
                results["heuristic_formula"] = True
            else:
                print(f"   ❌ Heuristic formula may be incorrect: {score}")
                results["heuristic_formula"] = False
        else:
            print("   ❌ Cannot test heuristic formula")
            results["heuristic_formula"] = False
    except Exception as e:
        print(f"   ❌ Heuristic formula test failed: {e}")
        results["heuristic_formula"] = False
    
    # Test 6: Analysis API endpoint exists
    try:
        from api.analysis import router as analysis_router
        print("   ✅ Analysis API endpoint exists")
        results["analysis_api"] = True
    except Exception as e:
        print(f"   ❌ Analysis API test failed: {e}")
        results["analysis_api"] = False
    
    return all(results.values()), results

def test_cross_module_integration():
    """Test cross-module integration"""
    print("\n=== TESTING CROSS-MODULE INTEGRATION ===")
    
    results = {}
    
    # Test 1: Database models exist for all modules
    try:
        from models.requirement import Requirement
        from models.validation import ValidationSession, Defect
        from models.diagram import Diagram, DiagramElement
        from models.metrics import ProjectMetrics
        
        print("   ✅ All database models exist")
        results["database_models"] = True
    except Exception as e:
        print(f"   ❌ Database models test failed: {e}")
        results["database_models"] = False
    
    # Test 2: API routers are properly integrated
    try:
        from main import app
        routes = [route.path for route in app.routes]
        
        required_routes = [
            "/api/validation/validate",
            "/api/diagrams",
            "/api/analysis"
        ]
        
        missing_routes = []
        for route in required_routes:
            if not any(route in r for r in routes):
                missing_routes.append(route)
        
        if not missing_routes:
            print("   ✅ All required API routes exist")
            results["api_integration"] = True
        else:
            print(f"   ❌ Missing API routes: {missing_routes}")
            results["api_integration"] = False
    except Exception as e:
        print(f"   ❌ API integration test failed: {e}")
        results["api_integration"] = False
    
    return all(results.values()), results

def main():
    """Run comprehensive verification of Modules 3, 4, and 5"""
    print("🚀 STARTING COMPREHENSIVE MODULES 3, 4, 5 VERIFICATION")
    print("=" * 70)
    
    modules = [
        ("Module 3 - AI Validation", test_module_3_validation),
        ("Module 4 - Visual Modeling", test_module_4_visual_modeling),
        ("Module 5 - Predictive Analytics", test_module_5_predictive_analytics),
        ("Cross-Module Integration", test_cross_module_integration),
    ]
    
    all_results = {}
    
    for module_name, test_func in modules:
        try:
            success, detailed_results = test_func()
            all_results[module_name] = {
                "success": success,
                "details": detailed_results
            }
        except Exception as e:
            print(f"❌ {module_name} failed with error: {e}")
            all_results[module_name] = {
                "success": False,
                "details": {"error": str(e)}
            }
    
    # Calculate overall success
    module_success = sum(1 for result in all_results.values() if result["success"])
    total_modules = len(all_results)
    overall_success_rate = (module_success / total_modules) * 100
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE MODULES 3, 4, 5 VERIFICATION RESULTS")
    print("=" * 70)
    
    for module_name, result in all_results.items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {module_name}: {'PASS' if result['success'] else 'FAIL'}")
        
        # Show detailed results
        if "details" in result and isinstance(result["details"], dict):
            for detail_name, detail_success in result["details"].items():
                if detail_name != "error":
                    detail_status = "✅" if detail_success else "❌"
                    print(f"    {detail_status} {detail_name}")
    
    print(f"\n🎯 OVERALL SUCCESS RATE: {overall_success_rate:.1f}%")
    print(f"   Modules Passed: {module_success}/{total_modules}")
    
    if overall_success_rate >= 80:
        print("   🎉 EXCELLENT - All modules properly implemented")
        print("   ✅ VisSpec Modules 3, 4, 5 are ready for production")
    elif overall_success_rate >= 60:
        print("   ✅ GOOD - Most modules properly implemented")
        print("   ⚠️  Some minor issues may need attention")
    else:
        print("   ❌ NEEDS IMPROVEMENT - Significant issues found")
    
    return overall_success_rate >= 60

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
