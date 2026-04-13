import unittest
from backend.services.ai.semantic_analyzer import SemanticAnalyzer


class TestSemanticAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SemanticAnalyzer()

    def test_analyze_text_empty_input(self):
        """Test analysis of empty text"""
        result = self.analyzer.analyze_text("")
        self.assertEqual(result["entities"], [])
        self.assertEqual(result["ambiguities"], [])
        self.assertEqual(result["confidence_score"], 0.0)

    def test_analyze_text_with_simple_content(self):
        """Test analysis of simple text"""
        text = "The user should be able to login to the system."
        result = self.analyzer.analyze_text(text)
        
        # Should have some results
        self.assertIsInstance(result, dict)
        self.assertIn("entities", result)
        self.assertIn("ambiguities", result)
        self.assertIn("confidence_score", result)
        self.assertGreaterEqual(result["confidence_score"], 0.0)
        self.assertLessEqual(result["confidence_score"], 1.0)

    def test_identify_ambiguities(self):
        """Test identification of ambiguous terms"""
        text = "The system should handle some requests maybe sometimes."
        ambiguities = self.analyzer._identify_ambiguities(text)
        
        # Should find at least one ambiguity
        self.assertGreaterEqual(len(ambiguities), 1)
        
        # Check that ambiguous terms are identified
        found_ambiguous_terms = [amb["term"] for amb in ambiguities]
        self.assertTrue(any("maybe" in term.lower() or "some" in term.lower() 
                           for term in found_ambiguous_terms))

    def test_calculate_confidence(self):
        """Test confidence calculation"""
        entities = [{"text": "user", "label": "ROLE", "start": 0, "end": 4}]
        ambiguities = [{"term": "maybe", "position": 10, "description": "Uncertainty"}]
        text = "The user maybe should do something"
        
        confidence = self.analyzer._calculate_confidence(entities, ambiguities, text)
        
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


if __name__ == '__main__':
    unittest.main()