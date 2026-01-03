import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import date, datetime
from pipeline.storage.database import SessionLocal, engine, Base
from pipeline.storage.models import Article, SentimentAnalysis
import json

def verify_setup():
    session = SessionLocal()
    try:
        # cleanup
        session.query(SentimentAnalysis).delete()
        session.query(Article).delete()
        session.commit()
        
        # Insert Article
        article = Article(
            title="Test Article",
            url="http://example.com/test",
            source="Test Source",
            summary="A short summary",
            published_at=datetime.now(),
            run_id="run-001",
            run_date=date.today()
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        print(f"✅ Article inserted with ID: {article.id}")
        
        # Insert Signal (SentimentAnalysis)
        sentiment = SentimentAnalysis(
            article_id=article.id,
            method_name="inset",
            output={"polarity": 0.8, "label": "positive"}
        )
        session.add(sentiment)
        session.commit()
        session.refresh(sentiment)
        print(f"✅ Sentiment inserted with ID: {sentiment.id}")
        
        # Query and Verify
        retrieved_article = session.query(Article).filter(Article.url == "http://example.com/test").first()
        if retrieved_article and len(retrieved_article.sentiment_analyses) > 0:
            print(f"✅ Verification Successful: Found article '{retrieved_article.title}' with {len(retrieved_article.sentiment_analyses)} sentiment analysis.")
            print(f"   Output: {retrieved_article.sentiment_analyses[0].output}")
        else:
            print("❌ Verification Failed: Could not retrieve data.")
            
    except Exception as e:
        print(f"❌ Verification Failed with Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    verify_setup()
