
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
        """Test basic windowing and phrase extraction logic."""
        articles = [
            {
                "title": "Uji Coba Program Makan Siang Gratis",
                "summary": "Pemerintah sedang melakukan uji coba program makan siang gratis untuk anak sekolah."
            },
            {
                "title": "Uji Coba Lagi",
                "summary": "Pemerintah sedang melakukan uji coba program makan siang gratis untuk anak sekolah."
            }
        ]
        # Entity "program"
        # Remaining: "makan siang gratis untuk anak sekolah"
        # Trim stopwords: "makan siang gratis untuk anak sekolah" (if "untuk" is not stopword, or similar)
        
        results = self.extractor.extract_phrases("program", articles)
        phrases = [r['phrase'] for r in results]
        logger.info(f"Basic logic extracted: {phrases}")
        
        self.assertTrue(len(phrases) > 0)
        # The phrase should contain "makan siang gratis"
        self.assertTrue(any("makan siang gratis" in p for p in phrases))

    def test_deduplication(self):
        """Test that shorter substrings are removed across articles."""
        articles = [
            {
                "title": "A", 
                "summary": "Saya suka makan siang gratis."
            },
            {
                "title": "B",
                "summary": "Saya suka makan siang gratis."
            }
        ]
        # Entity "Saya"
        # Segment: "suka makan siang gratis"
        results = self.extractor.extract_phrases("Saya", articles)
        phrases = [r['phrase'] for r in results]
        
        # New logic extracts maximal segments. 
        # "suka makan siang gratis" is extracted.
        # Fragments like "makan siang" are NOT extracted by the new logic at all.
        self.assertIn("suka makan siang gratis", phrases)
        
        # Verify no tiny fragments are left if they are substrings
        for p in phrases:
            for other in phrases:
                if p != other:
                    self.assertNotIn(p, other)

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
