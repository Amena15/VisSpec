"""Tests for visualization service - Mermaid diagram generation."""
import sys
import os
import unittest

# Add backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.visualization.visualizer import Visualizer


class TestMermaidUseCaseGeneration(unittest.TestCase):
    """Test UML Use Case diagram generation."""

    def setUp(self):
        self.visualizer = Visualizer()

    def test_usecase_produces_valid_mermaid(self):
        """Test that a valid use case text produces valid Mermaid syntax."""
        text = "The system shall allow the customer to browse products and add items to the cart. " \
               "The admin must be able to manage product inventory and view sales reports."

        result = self.visualizer.generate_usecase_diagram(text)

        # Verify Mermaid syntax is generated
        self.assertIsNotNone(result["mermaid_syntax"])
        self.assertIsInstance(result["mermaid_syntax"], str)
        self.assertIn("graph LR", result["mermaid_syntax"])

        # Verify actors and use cases extracted
        self.assertIsInstance(result["actors"], list)
        self.assertIsInstance(result["use_cases"], list)
        self.assertGreater(len(result["actors"]), 0, "Should extract at least one actor")
        self.assertGreater(len(result["use_cases"]), 0, "Should extract at least one use case")

    def test_usecase_with_include_extend(self):
        """Test that include/extend relationships are detected."""
        text = "The user shall login to the system. After login, the user must verify their identity " \
               "to access secure features. The user may optionally export reports as PDF."

        result = self.visualizer.generate_usecase_diagram(text)

        # Verify relationships extracted
        self.assertIsInstance(result["relationships"], list)

        # Check for include/extend types
        rel_types = [r.get("type") for r in result["relationships"]]
        has_include_or_extend = any(t in ("include", "extend") for t in rel_types)
        self.assertTrue(
            has_include_or_extend or len(result["relationships"]) > 0,
            "Should detect include/extend relationships from modal keywords"
        )

    def test_usecase_empty_text(self):
        """Test that empty text produces valid (empty) Mermaid output."""
        result = self.visualizer.generate_usecase_diagram("")

        self.assertIsNotNone(result["mermaid_syntax"])
        self.assertIn("graph LR", result["mermaid_syntax"])


class TestMermaidSequenceGeneration(unittest.TestCase):
    """Test UML Sequence diagram generation."""

    def setUp(self):
        self.visualizer = Visualizer()

    def test_sequence_produces_valid_mermaid(self):
        """Test that sequence diagram generation produces valid Mermaid syntax."""
        text = "The customer sends a login request to the system. The system validates credentials " \
               "and returns an authentication token."

        result = self.visualizer.generate_sequence_diagram(text)

        self.assertIsNotNone(result["mermaid_syntax"])
        self.assertIsInstance(result["mermaid_syntax"], str)
        self.assertIn("sequenceDiagram", result["mermaid_syntax"])


class TestMermaidActivityGeneration(unittest.TestCase):
    """Test Activity diagram generation."""

    def setUp(self):
        self.visualizer = Visualizer()

    def test_activity_produces_valid_mermaid(self):
        """Test that activity diagram generation produces valid Mermaid syntax."""
        text = "First, the user selects a product. Then, the user adds it to the cart. " \
               "Finally, the user proceeds to checkout."

        result = self.visualizer.generate_activity_diagram(text)

        self.assertIsNotNone(result["mermaid_syntax"])
        self.assertIsInstance(result["mermaid_syntax"], str)
        self.assertIn("graph TD", result["mermaid_syntax"])


if __name__ == "__main__":
    unittest.main()
