import logging
from textblob import TextBlob
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

# Initialize translator (Indonesian to English)
translator = GoogleTranslator(source='id', target='en')

def translate_to_english(text, max_length=4900):
    """Translate Indonesian text to English for sentiment analysis."""
    if not text:
        return ""
    
    try:
        # Google Translate has a 5000 char limit
        if len(text) > max_length:
            text = text[:max_length]
        
        translated = translator.translate(text)
        return translated
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return text  # Return original if translation fails

def analyze_sentiment(text):
    """Analyze sentiment of text using TextBlob."""
    if not text:
        return {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "label": "neutral"
        }
    
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Classify polarity
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    
    return {
        "polarity": round(polarity, 3),
        "subjectivity": round(subjectivity, 3),
        "label": label
    }

def analyze_article_sentiment(article):
    """Analyze sentiment for a single article."""
    # Combine title and summary for sentiment analysis
    title = article.get('title', '')
    summary = article.get('summary', '')
    combined_text = f"{title}. {summary}"
    
    # Translate to English (sentiment analysis works better in English)
    translated_text = translate_to_english(combined_text)
    
    # Analyze sentiment
    sentiment = analyze_sentiment(translated_text)
    
    # Add sentiment to article
    article_with_sentiment = article.copy()
    article_with_sentiment['sentiment'] = sentiment
    
    return article_with_sentiment

def analyze_all_sentiments(articles):
    """Analyze sentiment for all articles."""
    articles_with_sentiment = []
    
    for idx, article in enumerate(articles, 1):
        try:
            article_with_sentiment = analyze_article_sentiment(article)
            articles_with_sentiment.append(article_with_sentiment)
            
            if idx % 10 == 0:
                logger.info(f"Analyzed sentiment for {idx}/{len(articles)} articles")
        except Exception as e:
            logger.error(f"Failed to analyze sentiment for article {idx}: {e}")
            # Add article without sentiment if analysis fails
            article_copy = article.copy()
            article_copy['sentiment'] = {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "label": "neutral"
            }
            articles_with_sentiment.append(article_copy)
    
    # Calculate stats
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    for article in articles_with_sentiment:
        label = article.get('sentiment', {}).get('label', 'neutral')
        sentiment_counts[label] += 1
    
    stats = {
        "total_analyzed": len(articles_with_sentiment),
        "sentiment_distribution": sentiment_counts
    }
    
    logger.info(f"Sentiment analysis complete: {stats}")
    return articles_with_sentiment, stats

if __name__ == "__main__":
    # For testing purposes
    logging.basicConfig(level=logging.INFO)
    
    test_article = {
        "title": "Ekonomi Indonesia Tumbuh Pesat",
        "summary": "Pertumbuhan ekonomi Indonesia mencapai rekor tertinggi tahun ini.",
        "url": "https://example.com/1",
        "source": "test"
    }
    
    result = analyze_article_sentiment(test_article)
    print(f"Article with sentiment: {result}")