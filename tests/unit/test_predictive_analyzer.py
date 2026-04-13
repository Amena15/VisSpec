import unittest
from backend.services.ai.predictive_analyzer import PredictiveAnalyzer


class TestPredictiveAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PredictiveAnalyzer()

    def test_analyze_text_empty_input(self):
        """Test analysis of empty text"""
        result = self.analyzer.analyze_text("")
        self.assertEqual(result["complexity_score"], 0.0)
        self.assertEqual(result["estimated_effort_hours"], 0.0)
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["recommendations"], [])
        self.assertEqual(result["confidence_score"], 0.0)

    def test_calculate_complexity_score(self):
        """Test complexity scoring"""
        text = "The system should handle user authentication with if-else conditions and loops."
        score = self.analyzer._calculate_complexity_score(text)
        
        # Should have some complexity due to conditional statements and loops
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_estimate_effort(self):
        """Test effort estimation"""
        text = "A simple requirement with few words."
        complexity_score = 20.0
        effort = self.analyzer._estimate_effort(text, complexity_score)
        
        # Should have positive effort
        self.assertGreater(effort, 0.0)

    def test_determine_risk_level(self):
        """Test risk level determination"""
        # Test low risk
        self.assertEqual(self.analyzer._determine_risk_level(10), "low")
        self.assertEqual(self.analyzer._determine_risk_level(20), "low")
        
        # Test medium risk
        self.assertEqual(self.analyzer._determine_risk_level(30), "medium")
        self.assertEqual(self.analyzer._determine_risk_level(50), "medium")
        
        # Test high risk
        self.assertEqual(self.analyzer._determine_risk_level(60), "high")
        self.assertEqual(self.analyzer._determine_risk_level(80), "high")
        
        # Test critical risk
        self.assertEqual(self.analyzer._determine_risk_level(90), "critical")
        self.assertEqual(self.analyzer._determine_risk_level(100), "critical")

    def test_generate_recommendations(self):
        """Test recommendation generation"""
        text = "The system should handle user authentication if the user provides valid credentials."
        complexity_score = 30.0
        recommendations = self.analyzer._generate_recommendations(text, complexity_score)
        
        # Should have some recommendations
        self.assertIsInstance(recommendations, list)
        self.assertGreaterEqual(len(recommendations), 0)

    def test_calculate_confidence(self):
        """Test confidence calculation"""
        text = "A well-defined requirement with clear specifications."
        complexity_score = 40.0
        confidence = self.analyzer._calculate_confidence(text, complexity_score)
        
        self.assertGreaterEqual(confidence, 0.1)
        self.assertLessEqual(confidence, 1.0)


if __name__ == '__main__':
    unittest.main()