import re
import logging
import hashlib
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

def strip_html(text):
    """Remove all HTML tags from text."""
    if not text:
        return ""
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

def normalize_whitespace(text):
    """Normalize whitespace in text."""
    if not text:
        return ""
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()

def normalize_text(text):
    """Apply all text normalization steps."""
    if not text:
        return ""
    
    # Strip HTML
    text = strip_html(text)
    
    # Normalize whitespace
    text = normalize_whitespace(text)
    
    return text

def is_indonesian(text, min_length=20):
    """Check if text is in Indonesian language."""
    if not text or len(text) < min_length:
        return False
    
    try:
        lang = detect(text)
        return lang == 'id'
    except LangDetectException:
        logger.warning("Language detection failed")
        return False

def generate_content_hash(title, summary):
    """Generate a hash for duplicate detection."""
    content = f"{title}|{summary}".lower()
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def clean_article(article):
    """Clean and normalize a single article."""
    cleaned = article.copy()
    
    # Normalize title
    cleaned['title'] = normalize_text(article.get('title', ''))
    
    # Normalize summary
    cleaned['summary'] = normalize_text(article.get('summary', ''))
    
    # Generate content hash for deduplication
    cleaned['content_hash'] = generate_content_hash(
        cleaned['title'], 
        cleaned['summary']
    )
    
    # Check if Indonesian
    combined_text = f"{cleaned['title']} {cleaned['summary']}"
    cleaned['is_indonesian'] = is_indonesian(combined_text)
    
    return cleaned

def deduplicate_articles(articles):
    """Remove duplicate articles based on content hash."""
    seen_hashes = set()
    seen_urls = set()
    unique_articles = []
    
    duplicates = 0
    
    for article in articles:
        content_hash = article.get('content_hash')
        url = article.get('url')
        
        # Check both content hash and URL for duplicates
        if content_hash in seen_hashes or url in seen_urls:
            duplicates += 1
            continue
        
        seen_hashes.add(content_hash)
        seen_urls.add(url)
        unique_articles.append(article)
    
    logger.info(f"Removed {duplicates} duplicate articles")
    return unique_articles

def clean_articles(articles):
    """Clean all articles and filter by language."""
    # Clean each article
    cleaned = [clean_article(article) for article in articles]
    
    # Deduplicate
    unique = deduplicate_articles(cleaned)
    
    # Filter for Indonesian only
    indonesian_only = [
        article for article in unique 
        if article.get('is_indonesian', False)
    ]
    
    stats = {
        "total_input": len(articles),
        "after_dedup": len(unique),
        "indonesian_only": len(indonesian_only),
        "removed_duplicates": len(articles) - len(unique),
        "removed_non_indonesian": len(unique) - len(indonesian_only)
    }
    
    logger.info(f"Cleaning complete: {len(articles)} → {len(indonesian_only)} articles")
    logger.info(f"Removed: {stats['removed_duplicates']} duplicates, {stats['removed_non_indonesian']} non-Indonesian")
    
    return indonesian_only, stats

if __name__ == "__main__":
    # For testing purposes
    logging.basicConfig(level=logging.INFO)
    
    test_articles = [
        {
            "title": "<b>Test Article</b>",
            "summary": "This is a test   summary with  extra   spaces",
            "url": "https://example.com/1",
            "source": "test"
        }
    ]
    
    cleaned, stats = clean_articles(test_articles)
    print(f"Stats: {stats}")
    if cleaned:
        print(f"Sample cleaned article: {cleaned[0]}")