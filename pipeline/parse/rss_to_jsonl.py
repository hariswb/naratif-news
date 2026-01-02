import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def serialize_article(article):
    """Serialize article to JSON-compatible format."""
    serialized = article.copy()
    
    # Convert datetime to ISO string
    if isinstance(serialized.get("published"), datetime):
        serialized["published"] = serialized["published"].isoformat()
    
    return serialized

def articles_to_jsonl(articles, output_path):
    """Write articles to JSONL format (one article per line)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for article in articles:
            serialized = serialize_article(article)
            json_line = json.dumps(serialized, ensure_ascii=False)
            f.write(json_line + '\n')
    
    logger.info(f"Wrote {len(articles)} articles to {output_path}")
    return len(articles)

def load_jsonl(input_path):
    """Load articles from JSONL format."""
    articles = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                article = json.loads(line.strip())
                
                # Convert ISO string back to datetime if present
                if article.get("published"):
                    try:
                        article["published"] = datetime.fromisoformat(article["published"])
                    except (ValueError, TypeError):
                        article["published"] = None
                
                articles.append(article)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse line {line_num}: {e}")
    
    logger.info(f"Loaded {len(articles)} articles from {input_path}")
    return articles

def parse_to_jsonl(run_dir, articles):
    """Parse collected articles and save as JSONL."""
    parsed_dir = run_dir / "parsed"
    parsed_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = parsed_dir / "raw_articles.jsonl"
    count = articles_to_jsonl(articles, output_path)
    
    stats = {
        "total_articles": count,
        "output_file": str(output_path)
    }
    
    logger.info(f"Parse complete: {count} articles written to JSONL")
    return stats

if __name__ == "__main__":
    # For testing purposes
    logging.basicConfig(level=logging.INFO)
    
    # Test loading
    test_path = Path("data/runs/test/parsed/raw_articles.jsonl")
    if test_path.exists():
        articles = load_jsonl(test_path)
        print(f"Loaded {len(articles)} articles")
        if articles:
            print(f"Sample article: {articles[0]}")