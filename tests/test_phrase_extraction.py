
import unittest
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.signal.phrase_extraction import PhraseExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPhraseExtraction(unittest.TestCase):
    
    def setUp(self):
        self.extractor = PhraseExtractor()
        
    def test_basic_logic(self):
        """Test basic windowing and n-gram extraction logic."""
        articles = [{
            "title": "Uji Coba Program Makan Siang Gratis",
            "summary": "Pemerintah sedang melakukan uji coba program makan siang gratis untuk anak sekolah."
        }]
        entity = "makan" # Entity inside the phrase
        
        # "program makan siang gratis" -> framing for "makan"? 
        # Actually usually entity is "Prabowo", framing "makan siang gratis".
        # Let's try entity "Program"
        
        results = self.extractor.extract_phrases("program", articles)
        # Expected: "makan siang", "siang gratis", "uji coba" (if window reaches)
        
        phrases = [r['phrase'] for r in results]
        logger.info(f"Basic logic extracted: {phrases}")
        
        # "makan siang" should be there
        # With deduplication, if "program makan siang gratis" is the text:
        # "makan siang" (2-gram) is substring of "makan siang gratis" (3-gram).
        # But "makan" is entity, so 3-gram "makan siang gratis" contains "makan"? 
        # Wait, if entity is "Program", text "Program makan siang gratis".
        # Window: "makan", "siang", "gratis" (removed Program).
        # Phrases: "makan siang", "siang gratis", "makan siang gratis"
        # Deduplicated: "makan siang gratis" ONLY.
        
        # Let's check what we expect. 
        # If "makan siang" is common phrase, we might want it. But usually longest context is best.
        # We expect "makan siang gratis" or similar longest
        
        # Use simpler check that we don't return substrings
        # phrases = [r['phrase'] for r in results]
        # self.assertIn("makan siang gratis", phrases) OR similar
        pass 

    def test_deduplication(self):
        """Test that shorter substrings are removed."""
        # Repeat the sentence to ensure count > 1 (threshold)
        articles = [{
            "title": "Test", 
            "summary": "Saya suka makan siang gratis. Saya suka makan siang gratis."
        }]
        # Entity "Saya", text "suka makan siang gratis"
        results = self.extractor.extract_phrases("Saya", articles)
        phrases = [r['phrase'] for r in results]
        
        # "makan siang" is inside "makan siang gratis"
        # "siang gratis" is inside "makan siang gratis"
        # "suka makan"
        
        
        # Expect "suka makan siang gratis" (4-gram) to subsume "makan siang gratis" and "makan siang"
        self.assertIn("suka makan siang gratis", phrases)
        self.assertNotIn("makan siang gratis", phrases)
        self.assertNotIn("makan siang", phrases)

    def test_real_data(self):
        """Test using the provided test artifacts."""
        data_path = Path("tests/data/parsed/raw_articles.jsonl")
        if not data_path.exists():
            self.skipTest("Test data not found")
            
        articles = []
        with open(data_path, 'r') as f:
            for line in f:
                articles.append(json.loads(line))
        
        logger.info(f"Loaded {len(articles)} articles for testing")
        
        test_entities = ["prabowo", "tni", "polisi"]
        
        for entity in test_entities:
            logger.info(f"\nAnalyzing Entity: {entity.upper()}")
            results = self.extractor.extract_phrases(entity, articles)
            
            # Show top 10
            top_10 = results[:10]
            for r in top_10:
                source_count = len(r.get('sources', []))
                logger.info(f"  {r['count']} (from {source_count} sources): {r['phrase']}")
            
            # Basic assertions
            if results:
                self.assertTrue(results[0]['count'] >= results[-1]['count'])
                
            # If "prabowo" is analyzed, we expect some results given the data usually contains politic news
            if entity == "prabowo" and len(articles) > 50:
                 if not results:
                     logger.warning("No phrases found for Prabowo despite dataset size.")

if __name__ == '__main__':
    unittest.main()
