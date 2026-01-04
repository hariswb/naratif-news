import logging
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

logger = logging.getLogger(__name__)

class NER:
    """
    Named Entity Recognition using cahya/bert-base-indonesian-NER.
    """
    METHOD_NAME = 'cahya/bert-base-indonesian-NER'
    MODEL_ID = "cahya/bert-base-indonesian-NER"

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.nlp = None
        self._load_model()

    def _load_model(self):
        """Load tokenizer and model."""
        try:
            logger.info(f"Loading NER model: {self.MODEL_ID}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_ID)
            self.model = AutoModelForTokenClassification.from_pretrained(self.MODEL_ID)
            self.nlp = pipeline("ner", model=self.model, tokenizer=self.tokenizer, aggregation_strategy="simple")
            logger.info("NER model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NER model: {e}")
            self.nlp = None

    def analyze(self, text):
        """
        Extract entities from text.
        Returns a list of dicts: {'entity_group': 'PER', 'word': 'Jokowi', 'score': 0.99, ...}
        """
        if not self.nlp or not text:
            return []
        
        try:
            # Truncate text to avoid model max length errors (usually 512 tokens)
            # Simple character truncation as a safeguard, model handles token truncation usually but good to be safe
            results = self.nlp(text[:2000]) # 2000 chars should be safely within 512 tokens mostly
            
            # Helper to convert numpy float32 to float for JSON serialization
            serialized_results = []
            for res in results:
                entity = {
                    "entity_group": res['entity_group'],
                    "word": res['word'],
                    "score": float(res['score']),
                    "start": res['start'],
                    "end": res['end']
                }
                serialized_results.append(entity)
                
            return serialized_results
        except Exception as e:
            logger.error(f"NER analysis failed: {e}")
            return []

# Global instance
_ner_analyzer = None

def get_ner_analyzer():
    global _ner_analyzer
    if _ner_analyzer is None:
        _ner_analyzer = NER()
    return _ner_analyzer

def analyze_article_ner(article):
    """Analyze NER for a single article."""
    analyzer = get_ner_analyzer()
    
    title = article.get('title', '')
    summary = article.get('summary', '')
    # Combine title and summary for better context, or just title? 
    # User's example showed titles. Let's do title + summary.
    combined_text = f"{title}. {summary}"
    
    entities = analyzer.analyze(combined_text)
    
    article_with_ner = article.copy()
    article_with_ner['ner'] = {
        "method": analyzer.METHOD_NAME,
        "entities": entities
    }
    
    return article_with_ner

def analyze_all_ner(articles):
    """Analyze NER for all articles."""
    articles_with_ner = []
    
    # Initialize analyzer once
    get_ner_analyzer()
    
    for idx, article in enumerate(articles, 1):
        try:
            result = analyze_article_ner(article)
            articles_with_ner.append(result)
            
            if idx % 10 == 0:
                logger.info(f"NER Analyzed {idx}/{len(articles)} articles")
        except Exception as e:
            logger.error(f"Failed to analyze article {idx} for NER: {e}")
            articles_with_ner.append(article)
            
    return articles_with_ner
