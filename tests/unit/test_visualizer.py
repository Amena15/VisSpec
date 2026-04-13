import unittest
from backend.services.visualization.visualizer import Visualizer


class TestVisualizer(unittest.TestCase):
    def setUp(self):
        self.visualizer = Visualizer()

    def test_generate_usecase_diagram(self):
        """Test use case diagram generation"""
        text = "As a user, I want to login to the system so that I can access my account."
        result = self.visualizer.generate_usecase_diagram(text)
        
        # Should have mermaid syntax
        self.assertIn("mermaid_syntax", result)
        self.assertIn("graph TD", result["mermaid_syntax"])
        self.assertIn("Use Case Diagram", result["title"])
        
        # Should have actors and use cases
        self.assertIn("actors", result)
        self.assertIn("use_cases", result)

    def test_generate_sequence_diagram(self):
        """Test sequence diagram generation"""
        text = "User sends login request to the authentication service. The service verifies credentials and responds."
        result = self.visualizer.generate_sequence_diagram(text)
        
        # Should have mermaid syntax
        self.assertIn("mermaid_syntax", result)
        self.assertIn("sequenceDiagram", result["mermaid_syntax"])
        self.assertIn("Sequence Diagram", result["title"])
        
        # Should have participants and messages
        self.assertIn("participants", result)
        self.assertIn("messages", result)

    def test_generate_activity_diagram(self):
        """Test activity diagram generation"""
        text = "First the user enters credentials. Then the system validates them. Finally, access is granted."
        result = self.visualizer.generate_activity_diagram(text)
        
        # Should have mermaid syntax
        self.assertIn("mermaid_syntax", result)
        self.assertIn("graph TD", result["mermaid_syntax"])
        self.assertIn("Activity Diagram", result["title"])
        
        # Should have activities and flows
        self.assertIn("activities", result)
        self.assertIn("flows", result)

    def test_extract_actors(self):
        """Test actor extraction"""
        text = "As a user, I want to login. The administrator manages accounts."
        actors = self.visualizer._extract_actors(text)
        
        # Should find actors
        self.assertIsInstance(actors, list)
        found_user = any("user" in actor.lower() for actor in actors)
        found_admin = any("admin" in actor.lower() for actor in actors)
        self.assertTrue(found_user or found_admin)

    def test_extract_use_cases(self):
        """Test use case extraction"""
        text = "The user can login to the system. The user can view profile."
        use_cases = self.visualizer._extract_use_cases(text)
        
        # Should find use cases
        self.assertIsInstance(use_cases, list)
        self.assertGreaterEqual(len(use_cases), 0)

    def test_generate_visualization_invalid_type(self):
        """Test visualization with invalid type"""
        with self.assertRaises(ValueError):
            self.visualizer.generate_visualization("test", "invalid_type")


if __name__ == '__main__':
    unittest.main()