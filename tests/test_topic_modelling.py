
import unittest
import json
import six
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.signal.topic_modelling import analyze_topics

class TestTopicModelling(unittest.TestCase):
    
    def setUp(self):
        # Load static test data
        data_path = Path(__file__).parent / "data" / "parsed" / "raw_articles.jsonl"
        self.articles = []
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.articles.append(json.loads(line))
        else:
            self.fail(f"Test data not found at {data_path}")
            
    def test_topic_modelling_output_format(self):
        """Test that topic modelling returns correct dictionary structure."""
        if not self.articles:
            self.skipTest("No test articles available")
            
        # Run on a subset to save time
        subset = self.articles[:50]
        results = analyze_topics(subset)
        
        self.assertTrue(len(results) > 0, "Should generate results")
        
        # Check first result structure
        print(results[0:10])
        first_result = results[0]
        self.assertIn("article_id", first_result)
        self.assertIn("method_name", first_result)
        self.assertIn("topic_index", first_result)
        self.assertIn("keywords", first_result)
        
        self.assertEqual(first_result["method_name"], "lda_tfidf")
        self.assertIsInstance(first_result["topic_index"], (int, int)) # Handle numpy ints
        self.assertIsInstance(first_result["keywords"], str)
        
    def test_empty_input(self):
        """Test handling of empty input."""
        results = analyze_topics([])
        self.assertEqual(results, [])

if __name__ == '__main__':
    unittest.main()
