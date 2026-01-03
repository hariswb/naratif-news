
import logging
import re
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

logger = logging.getLogger(__name__)

class TopicModeller:
    METHOD_NAME = 'lda_tfidf'

    def __init__(self, n_topics=7, max_features=1000):
        self.n_topics = n_topics
        self.max_features = max_features
        self.stopwords = []
        self.acronym_dict = {}
        self.acronym_pattern = None
        
        self.vectorizer = None
        self.lda_model = None
        
        self._load_resources()

    def _load_resources(self):
        """Load stopwords and acronyms from data directory."""
        data_dir = Path(__file__).parent / "data"
        
        # Load Stopwords
        try:
            stopwords_path = data_dir / "stopword-id.csv"
            if stopwords_path.exists():
                stopwords_df = pd.read_csv(stopwords_path, header=None)
                self.stopwords = stopwords_df[0].tolist()
            else:
                logger.warning(f"Stopwords file not found at {stopwords_path}")
                self.stopwords = []
        except Exception as e:
            logger.error(f"Failed to load stopwords: {e}")
            self.stopwords = []

        # Load Acronyms
        try:
            acronym_path = data_dir / "acronym.csv"
            if acronym_path.exists():
                df_acronym = pd.read_csv(acronym_path)
                self.acronym_dict = dict(zip(df_acronym["acronym"], df_acronym["expansion"]))
                self.acronym_pattern = re.compile(r'\b(' + '|'.join(map(re.escape, self.acronym_dict.keys())) + r')\b')
            else:
                logger.warning(f"Acronym file not found at {acronym_path}")
        except Exception as e:
            logger.error(f"Failed to load acronyms: {e}")

    def preprocess_text(self, text):
        """Clean and preprocess text."""
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        
        # Replace acronyms
        if self.acronym_pattern:
            text = self.acronym_pattern.sub(lambda match: self.acronym_dict[match.group(0)], text)
        
        # Lowercase
        text = text.lower()
        
        # Remove HTML image tags
        text = re.sub(r'<img[^>]*>', '', text)
        
        # Remove mentions, URLs, numbers
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'\d+', '', text)
        
        # Clean punctuation and excess whitespace
        text = text.replace("b'", "").replace("-", " ")
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove specific unwanted terms
        text = text.replace("img", "").replace("src", "")
        
        return text

    def perform_modelling(self, articles):
        """
        Perform LDA topic modelling on the provided list of articles.
        articles: list of dicts, each must have 'id' and 'title'.
        """
        if not articles:
            logger.warning("No articles to process.")
            return []
            
        # Convert to DataFrame
        articles_df = pd.DataFrame(articles)
        
        if 'title' not in articles_df.columns:
            logger.error("Articles data missing 'title' column.")
            return []
        
        # Ensure ID exists, if not generate or use index (but prefer ID for mapping)
        if 'id' not in articles_df.columns:
             # If no ID, we can't map back easily, but let's proceed with index
             articles_df['id'] = articles_df.index

        # Preprocess texts
        articles_df['clean_text'] = articles_df['title'].apply(self.preprocess_text)
        
        # TF-IDF Vectorization
        self.vectorizer = TfidfVectorizer(stop_words=self.stopwords, max_features=self.max_features)
        try:
            X = self.vectorizer.fit_transform(articles_df['clean_text'])
        except ValueError as e:
            logger.error(f"Vectorizer error (possibly empty vocabulary): {e}")
            return []

        # LDA Topic Modeling
        self.lda_model = LatentDirichletAllocation(n_components=self.n_topics, random_state=42)
        self.lda_model.fit(X)
        
        # Assign topics
        topic_distributions = self.lda_model.transform(X)
        articles_df['topic'] = topic_distributions.argmax(axis=1)
        
        # Generate topic keywords
        feature_names = self.vectorizer.get_feature_names_out()
        topic_keywords = {}
        for topic_idx, topic in enumerate(self.lda_model.components_):
            top_words = [feature_names[i] for i in topic.argsort()[:-11:-1]]
            topic_keywords[topic_idx] = ", ".join(top_words)
            
        # Format results
        results = []
        for index, row in articles_df.iterrows():
            topic_idx = row['topic']
            results.append({
                "article_id": row['id'],
                "method_name": self.METHOD_NAME,
                "topic_index": int(topic_idx),
                "keywords": topic_keywords[topic_idx]
            })
            
        return results

def analyze_topics(articles):
    """
    Perform topic modelling on a list of article dictionaries.
    
    Args:
        articles (list): List of dicts with 'id' and 'title'.
        
    Returns:
        list: List of result dicts with article_id, topic_index, keywords.
    """
    if not articles:
        return []

    modeller = TopicModeller()
    results = modeller.perform_modelling(articles)
    
    logger.info(f"Topic modelling completed for {len(results)} articles.")
    return results

if __name__ == "__main__":
    # Test block
    import sys
    import os
    
    # Add project root to path to allow imports
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    sys.path.append(str(project_root))
    
    from pipeline.db import get_db_connection
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        db_conn = get_db_connection()
        with db_conn:
            # Fetch articles manually for testing
            import pandas as pd
            query = "SELECT id, title FROM articles"
            df = pd.read_sql(query, db_conn.conn)
            articles = df.to_dict('records')
            
            results = analyze_topics(articles)
            print(f"Generated {len(results)} results.")
            if results:
                print("Sample result:", results[0])
    except Exception as e:
        print(f"Error: {e}")
