import json
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.signal.topic_modelling import analyze_topics

@pytest.fixture
def articles():
    # Load static test data
    data_path = Path(__file__).parent / "data" / "parsed" / "raw_articles.jsonl"
    loaded_articles = []
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    loaded_articles.append(json.loads(line))
        return loaded_articles
    else:
        pytest.fail(f"Test data not found at {data_path}")

def test_topic_modelling_output_format(articles):
    """Test that topic modelling returns correct dictionary structure."""
    if not articles:
        pytest.skip("No test articles available")
        
    # Run on a subset to save time
    subset = articles[:50]
    results = analyze_topics(subset)
    
    assert len(results) > 0, "Should generate results"
    
    # Check first result structure
    first_result = results[0]
    assert "article_id" in first_result
    assert "method_name" in first_result
    assert "topic_index" in first_result
    assert "keywords" in first_result
    
    assert first_result["method_name"] == "lda_tfidf"
    # Allow for both standard int and numpy int types
    assert isinstance(first_result["topic_index"], int) or hasattr(first_result["topic_index"], 'item')
    assert isinstance(first_result["keywords"], str)
    
def test_empty_input():
    """Test handling of empty input."""
    results = analyze_topics([])
    assert results == []
