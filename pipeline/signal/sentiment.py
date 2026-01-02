import logging
import re
from pathlib import Path
import csv

try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    from nltk.tokenize import word_tokenize
    import nltk
except ImportError:
    # Fallback for environments where dependencies might be missing during initial setup
    StemmerFactory = None
    word_tokenize = None
    nltk = None

logger = logging.getLogger(__name__)

class IndinesianSentimentAnalyzer:
    def __init__(self):
        self.positive_dict = {}
        self.negative_dict = {}
        self.stopwords = set()
        self.stemmer = None
        
        # Initialize resources
        self._load_resources()
        
    def _load_resources(self):
        """Load dictionaries and initialize stemmer."""
        data_dir = Path(__file__).parent / "data"
        
        # Ensure NLTK data is available (quietly)
        if nltk:
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
        
        # Initialize Stemmer
        if StemmerFactory:
            factory = StemmerFactory()
            self.stemmer = factory.create_stemmer()
        else:
            logger.warning("PySastrawi not installed. Stemming disabled.")
            
        # Load Stopwords
        try:
            stopwords_path = data_dir / "stopword-id.csv"
            if stopwords_path.exists():
                with open(stopwords_path, "r", encoding="utf-8") as f:
                    # Assuming one word per line or simple CSV
                    self.stopwords = set(line.strip().lower() for line in f if line.strip())
            else:
                logger.warning(f"Stopwords file not found at {stopwords_path}")
        except Exception as e:
            logger.error(f"Failed to load stopwords: {e}")

        # Load Dictionaries
        self.positive_dict = self._load_dictionary(data_dir / "positive.tsv")
        self.negative_dict = self._load_dictionary(data_dir / "negative.tsv")
        
        logger.info(f"Loaded resources: {len(self.stopwords)} stopwords, "
                   f"{len(self.positive_dict)} positive words, "
                   f"{len(self.negative_dict)} negative words")

    def _load_dictionary(self, path):
        """Load sentiment dictionary from TSV."""
        sentiment_dict = {}
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    # Skip header if present (heuristic: check first line)
                    lines = f.readlines()
                    start_idx = 0
                    if lines and "weight" in lines[0].lower():
                        start_idx = 1
                        
                    for line in lines[start_idx:]:
                        parts = line.strip().split("\t")
                        if len(parts) >= 2:
                            word = parts[0].strip().lower()
                            try:
                                weight = float(parts[1])
                                sentiment_dict[word] = weight
                            except ValueError:
                                continue
            else:
                logger.warning(f"Dictionary file not found at {path}")
        except Exception as e:
            logger.error(f"Failed to load dictionary {path}: {e}")
        return sentiment_dict

    def preprocess(self, text):
        """Clean, tokenize, remove stopwords, and stem text."""
        if not text:
            return []
            
        # Basic cleanup
        text = text.lower()
        text = re.sub(r'http\S+', '', text)  # Remove URLs
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        
        # Tokenize
        if word_tokenize:
            tokens = word_tokenize(text)
        else:
            tokens = text.split()
            
        # Remove stopwords
        tokens = [word for word in tokens if word not in self.stopwords]
        
        # Stem
        if self.stemmer:
            tokens = [self.stemmer.stem(word) for word in tokens]
            
        return tokens

    def analyze(self, text):
        """Calculate sentiment score for text."""
        tokens = self.preprocess(text)
        
        score = 0.0
        for token in tokens:
            score += self.positive_dict.get(token, 0)
            score += self.negative_dict.get(token, 0)
            
        # Normalize
        normalized_score = 0.0
        label = "neutral"
        
        if score > 0:
            normalized_score = 1.0
            label = "positive"
        elif score < 0:
            normalized_score = -1.0
            label = "negative"
            
        return {
            "polarity": normalized_score,
            "subjectivity": 0.0, # Dictionary approach doesn't easily yield subjectivity
            "label": label,
            "raw_score": score
        }

# Global analyzer instance
_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = IndinesianSentimentAnalyzer()
    return _analyzer

def analyze_article_sentiment(article):
    """Analyze sentiment for a single article."""
    analyzer = get_analyzer()
    
    title = article.get('title', '')
    summary = article.get('summary', '')
    combined_text = f"{title}. {summary}"
    
    sentiment = analyzer.analyze(combined_text)
    
    # Add sentiment to article
    article_with_sentiment = article.copy()
    article['sentiment'] = sentiment # Modify in place or copy? 
    # Logic follows original: return new dict with sentiment
    article_with_sentiment['sentiment'] = sentiment
    
    return article_with_sentiment

def analyze_all_sentiments(articles):
    """Analyze sentiment for all articles."""
    articles_with_sentiment = []
    
    for idx, article in enumerate(articles, 1):
        try:
            result = analyze_article_sentiment(article)
            articles_with_sentiment.append(result)
            
            if idx % 50 == 0:
                logger.info(f"Analyzed {idx}/{len(articles)} articles")
        except Exception as e:
            logger.error(f"Failed to analyze article {idx}: {e}")
            # Fallback
            fallback = article.copy()
            fallback['sentiment'] = {"polarity": 0, "subjectivity": 0, "label": "error"}
            articles_with_sentiment.append(fallback)
            
    # Calculate stats
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    for article in articles_with_sentiment:
        label = article.get('sentiment', {}).get('label', 'neutral')
        if label not in sentiment_counts:
            sentiment_counts[label] = 0
        sentiment_counts[label] += 1
        
    stats = {
        "total_analyzed": len(articles_with_sentiment),
        "sentiment_distribution": sentiment_counts
    }
    
    logger.info(f"Sentiment analysis complete: {stats}")
    return articles_with_sentiment, stats

if __name__ == "__main__":
    # Test block
    logging.basicConfig(level=logging.INFO)
    
    test_text = "Pemerintah berhasil meningkatkan ekonomi rakyat. Terima kasih banyak."
    test_article = {
        "title": "Ekonomi Bagus",
        "summary": "Pemerintah berhasil meningkatkan ekonomi.",
        "url": "http://test.com"
    }
    
    print("Initializing analyzer...")
    analyzer = get_analyzer()
    print(f"Test text: {test_text}")
    print(f"Score: {analyzer.analyze(test_text)}")
    
    print("\nTest article analysis:")
    print(analyze_article_sentiment(test_article))