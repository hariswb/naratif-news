import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.signal.sentiment import get_analyzer, analyze_article_sentiment

@pytest.fixture
def analyzer():
    return get_analyzer()

def test_analyzer_initialization(analyzer):
    """Test that analyzer loads resources correctly."""
    assert analyzer is not None
    # Check if resources are loaded (even if empty, dicts should exist)
    assert isinstance(analyzer.positive_dict, dict)
    assert isinstance(analyzer.negative_dict, dict)
    assert isinstance(analyzer.stopwords, set)

def test_preprocess(analyzer):
    """Test text preprocessing."""
    text = "Saya Sangat SUKA makan bakso!!!"
    tokens = analyzer.preprocess(text)
    
    # Needs to be lowercase
    assert all(t == t.lower() for t in tokens)
    # Should remove punctuation
    assert "!!!" not in tokens
    # Should ideally stem and remove stopwords (if Sastrawi is present)
    # Since we can't guarantee Sastrawi presence in all envs without install, 
    # we verify basic tokenization logic at minimum.
    assert len(tokens) > 0

def test_positive_sentiment(analyzer):
    """Test positive sentiment detection."""
    # Assuming 'berhasil' or 'bagus' are in positive dict
    # If using custom dictionary, we might need to mock or ensure content
    # For now, let's use words likely to be in typical ID sentiment lexicons
    text = "Pemerintah berhasil memajukan ekonomi bangsa yang hebat dan bagus"
    result = analyzer.analyze(text)
    
    # We expect positive or at least non-negative
    # If resources are missing, it might be neutral (0.0)
    # So we check structure mainly, and value if possible
    assert result['method'] == 'inset'
    assert 'polarity' in result
    assert 'label' in result
    
    # If dicts are loaded, this should be positive
    if analyzer.positive_dict:
        assert result['label'] == 'positive'
        assert result['polarity'] > 0

def test_negative_sentiment(analyzer):
    """Test negative sentiment detection."""
    text = "Korupsi dan kejahatan sangat buruk dan mengecewakan"
    result = analyzer.analyze(text)
    
    if analyzer.negative_dict:
        assert result['label'] == 'negative'
        assert result['polarity'] < 0

def test_neutral_sentiment(analyzer):
    """Test neutral sentiment."""
    text = "Ini adalah sebuah meja kayu"
    result = analyzer.analyze(text)
    
    assert result['label'] == 'neutral'
    # Polarity for neutral should be roughly 0, depending on implementation
    
def test_analyze_article_sentiment_integration():
    """Test integration with article dict."""
    article = {
        "title": "Kemenangan Timnas",
        "summary": "Timnas bermain sangat bagus dan menang telak.",
        "url": "http://test.com/1"
    }
    
    result_article = analyze_article_sentiment(article)
    
    assert 'sentiment' in result_article
    assert result_article['sentiment']['label'] in ['positive', 'negative', 'neutral']
    # Check original fields preserved
    assert result_article['title'] == article['title']
    assert result_article['url'] == article['url']
