
import unittest
import json
import sys
import os

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.services.ai_decision_service import AIDecisionService, AIDecisionConfig, DecisionResponse

class TestAIDecisionService(unittest.TestCase):
    def setUp(self):
        # Mock config
        self.config = AIDecisionConfig(
            api_key="mock",
            base_url="mock",
            model="mock"
        )
        self.service = AIDecisionService(self.config)

    def test_parse_valid_json(self):
        """Test parsing valid JSON response"""
        valid_json = """
        {
            "decisions": [
                {
                    "operation": "buy",
                    "stock_code": "600519",
                    "stock_name": "Moutai",
                    "target_portion_of_balance": 0.1,
                    "max_price": 1800.0,
                    "reason": "Good signal",
                    "trading_strategy": "Hold"
                }
            ]
        }
        """
        result = self.service._parse_llm_response(valid_json)
        self.assertIn("decisions", result)
        self.assertEqual(len(result["decisions"]), 1)
        self.assertEqual(result["decisions"][0]["stock_code"], "600519")

    def test_parse_json_in_markdown(self):
        """Test parsing JSON wrapped in markdown"""
        markdown_json = """
        Here is the decision:
        ```json
        {
            "decisions": []
        }
        ```
        """
        result = self.service._parse_llm_response(markdown_json)
        self.assertIn("decisions", result)
        self.assertEqual(len(result["decisions"]), 0)

    def test_parse_invalid_schema(self):
        """Test parsing JSON with missing fields"""
        invalid_json = """
        {
            "decisions": [
                {
                    "operation": "buy",
                    "stock_code": "600519"
                    
                }
            ]
        }
        """
        # Missing required fields like stock_name, reason, etc.
        result = self.service._parse_llm_response(invalid_json)
        self.assertIn("parsing_error", result)
        self.assertIn("decisions", result)
        self.assertEqual(len(result["decisions"]), 0)

    def test_parse_malformed_json(self):
        """Test parsing invalid JSON syntax"""
        malformed = "{ decisions: [ ... "
        result = self.service._parse_llm_response(malformed)
        self.assertIn("parsing_error", result)
        self.assertIn("Invalid JSON format", result["parsing_error"])

if __name__ == '__main__':
    unittest.main()
