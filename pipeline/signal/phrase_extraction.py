
import logging
import re
import csv
from pathlib import Path
import nltk
from nltk.util import ngrams
from nltk.tokenize import sent_tokenize, word_tokenize

logger = logging.getLogger(__name__)

class PhraseExtractor:
    """
    Extracts narrative framing phrases around specific entities.
    """
    
    def __init__(self, window_size=7):
        self.window_size = window_size
        self.stopwords = set()
        self._load_resources()
        
    def _load_resources(self):
        """Load stopwords and ensure NLTK data availability."""
        # Ensure NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        # Load Stopwords (reusing shared resource)
        data_dir = Path(__file__).parent / "data"
        stopwords_path = data_dir / "stopword-id.csv"
        
        try:
            if stopwords_path.exists():
                with open(stopwords_path, "r", encoding="utf-8") as f:
                    # Handle both simple list and CSV format if needed, though usually just lines
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            self.stopwords.add(row[0].strip().lower())
            else:
                logger.warning(f"Stopwords file not found at {stopwords_path}")
        except Exception as e:
            logger.error(f"Failed to load stopwords: {e}")

    def clean_text(self, text):
        """Basic text cleaning."""
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove special chars but keep sentence punctuation for tokenization later? 
        # Actually sent_tokenize needs punctuation. So we clean AFTER sentence split or handle carefully.
        # Let's clean lightly here, mostly for normalization.
        text = text.replace('\n', ' ').strip()
        return text

    def get_context_windows(self, text, entity_word):
        """
        Extract context windows around entity in the text.
        Returns list of token lists.
        """
        windows = []
        sentences = sent_tokenize(text)
        
        entity_lower = entity_word.lower()
        
        for sentence in sentences:
            if entity_lower in sentence.lower():
                # Tokenize sentence
                # Remove punctuation for the window analysis to yield clean phrases
                clean_sentence = re.sub(r'[^\w\s]', '', sentence)
                tokens = word_tokenize(clean_sentence.lower())
                
                # Find entity indices
                indices = [i for i, x in enumerate(tokens) if x == entity_lower]
                
                for idx in indices:
                    start = max(0, idx - self.window_size)
                    end = min(len(tokens), idx + self.window_size + 1)
                    
                    window_tokens = tokens[start:end]
                    # Remove the entity itself from the phrase? The plan says "co-occur with entity".
                    # Usually framing includes the entity in the syntax but the phrases we want are "program makan siang" (without Prabowo).
                    # The example: "program makan siang" (from "program makan siang gratis nasional")
                    # Let's keep the window as is for n-gram generation.
                    windows.append(window_tokens)
                    
        return windows

        return results

    def _filter_subphrases(self, phrases):
        """
        Filter out phrases that are substrings of longer phrases in the same list.
        Example: ["makan siang", "makan siang gratis"] -> ["makan siang gratis"]
        """
        if not phrases:
            return []
            
        # Sort by length (desc) so longest phrases come first
        sorted_phrases = sorted(list(set(phrases)), key=len, reverse=True)
        kept_phrases = []
        
        for phrase in sorted_phrases:
            # If phrase is part of any already kept phrase, skip it
            is_substring = False
            for kept in kept_phrases:
                if phrase in kept:
                    is_substring = True
                    break
            
            if not is_substring:
                kept_phrases.append(phrase)
                
        return kept_phrases

    def extract_from_article(self, article_text, entity_word):
        """
        Extract framing phrases for an entity from a single article text.
        Returns list of phrases.
        """
        candidates = []
        text = self.clean_text(article_text)
        
        # Determine context windows for this specific entity
        windows = self.get_context_windows(text, entity_word)
        
        for window in windows:
            # Generate 2-gram, 3-gram, 4-gram
            # We collect ALL candidates first, then filter
            window_phrases = []
            for n in range(2, 5):
                grams = ngrams(window, n)
                
                for gram in grams:
                    # Filter stopwords
                    if all(word in self.stopwords for word in gram):
                        continue
                    if gram[0] in self.stopwords or gram[-1] in self.stopwords:
                        continue
                    if entity_word.lower() in gram:
                        continue

                    phrase = " ".join(gram)
                    window_phrases.append(phrase)
            
            # Filter substrings per window to avoid "makan siang" AND "makan siang gratis" from same sentence
            candidates.extend(self._filter_subphrases(window_phrases))
                    
        return candidates

    def extract_phrases(self, entity_word, articles):
        """
        Extract relevant framing phrases for an entity from a list of articles.
        Aggregates results from single article extractions.
        """
        phrase_data = {}
        
        for article in articles:
            # Combine title and summary
            text = f"{article.get('title', '')}. {article.get('summary', '')}"
            
            # Use the single article extraction method
            phrases = self.extract_from_article(text, entity_word)
            
            for phrase in phrases:
                # Initialize if not exists
                if phrase not in phrase_data:
                    phrase_data[phrase] = {"count": 0, "sources": set()}
                
                phrase_data[phrase]["count"] += 1
                url = article.get('url')
                if url:
                    phrase_data[phrase]["sources"].add(url)
                        
        # Sort by count desc
        sorted_phrases = sorted(phrase_data.items(), key=lambda x: x[1]['count'], reverse=True)
        
        # Format output
        results = []
        for phrase, data in sorted_phrases:
            if data['count'] > 1:
                results.append({
                    "phrase": phrase, 
                    "count": data['count'],
                    "sources": list(data['sources'])
                })
        
        return results

