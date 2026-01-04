import logging
import json
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from pipeline.signal.ner import analyze_article_ner, get_ner_analyzer

def load_test_articles():
    """Load articles from test data."""
    data_path = Path(__file__).parent / "data/parsed/raw_articles.jsonl"
    if not data_path.exists():
        pytest.skip(f"Test data not found at {data_path}. Run populate_test_data.py first.")
    
    articles = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))
    return articles

def test_ner_model_loading():
    """Test that NER model loads correctly."""
    analyzer = get_ner_analyzer()
    assert analyzer.model is not None
    assert analyzer.tokenizer is not None
    assert analyzer.nlp is not None

def test_ner_extraction():
    """Test entity extraction on a sample text."""
    analyzer = get_ner_analyzer()
    
    # Test text with known entities
    text = "Jokowi mengunjungi Jakarta minggu lalu."
    result = analyzer.analyze(text)
    
    # Check if we got results
    assert len(result) > 0
    
    # Check for specific entities (approximate)
    # Note: Model output format might vary, but should contain 'Jokowi' (PER) and 'Jakarta' (LOC/GPE)
    found_jokowi = any(e['word'].lower() == 'jokowi' for e in result)
    # found_jakarta = any('jakarta' in e['word'].lower() for e in result) # Subword tokenization might split it
    
    # Allow for subword toknization variations, but Jokowi is usually a single token or close
    assert found_jokowi, f"Expected 'Jokowi' in results, got: {result}"

def test_analyze_article_ner_integration():
    """Test integration with article dictionary."""
    articles = load_test_articles()
    if not articles:
        pytest.skip("No test articles found.")
        
    # Take the first article
    article = articles[0]
    
    # Analyze
    result_article = analyze_article_ner(article)
    
    # Check structure
    assert 'ner' in result_article
    assert 'method' in result_article['ner']
    assert result_article['ner']['method'] == 'cahya/bert-base-indonesian-NER'
    assert 'entities' in result_article['ner']
    assert isinstance(result_article['ner']['entities'], list)

if __name__ == "__main__":
    # Manually run if executed as script
    setup_logging()
    test_ner_model_loading()
    test_ner_extraction()
    test_analyze_article_ner_integration()
    print("All tests passed!")

def setup_logging():
    logging.basicConfig(level=logging.INFO)
