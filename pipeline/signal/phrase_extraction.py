
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
        
        # Prepare entity tokens for matching
        entity_tokens = word_tokenize(re.sub(r'[^\w\s]', '', entity_word.lower()))
        if not entity_tokens:
            return []
        
        for sentence in sentences:
            if entity_word.lower() in sentence.lower():
                # Tokenize sentence
                # Remove punctuation for the window analysis to yield clean phrases
                clean_sentence = re.sub(r'[^\w\s]', '', sentence)
                tokens = word_tokenize(clean_sentence.lower())
                
                # Find occurrences of the entity token sequence
                n = len(entity_tokens)
                for i in range(len(tokens) - n + 1):
                    if tokens[i:i+n] == entity_tokens:
                        # Found a match!
                        start = max(0, i - self.window_size)
                        end = min(len(tokens), i + n + self.window_size)
                        
                        window_tokens = tokens[start:end]
                        windows.append(window_tokens)
                        
        return windows

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
        Uses a maximal segment approach to reduce redundancy.
        """
        candidates = []
        text = self.clean_text(article_text)
        
        # Determine context windows for this specific entity
        windows = self.get_context_windows(text, entity_word)
        
        # Extract individual entity words for exclusion
        entity_tokens_clean = set(word_tokenize(re.sub(r'[^\w\s]', '', entity_word.lower())))
        
        for window in windows:
            # We want to find contiguous sequences of tokens that:
            # 1. Do not contain any entity token
            # 2. Are not entirely stopwords
            # 3. (Optional) have meaningful boundaries
            
            # Step 1: Split window by entity tokens
            segments = []
            current_segment = []
            for token in window:
                if token in entity_tokens_clean:
                    if current_segment:
                        segments.append(current_segment)
                        current_segment = []
                else:
                    current_segment.append(token)
            if current_segment:
                segments.append(current_segment)
                
            # Step 2: Process segments into phrases
            for seg in segments:
                # Trim stopwords from both ends
                start = 0
                while start < len(seg) and seg[start] in self.stopwords:
                    start += 1
                
                end = len(seg)
                while end > start and seg[end-1] in self.stopwords:
                    end -= 1
                    
                phrase_tokens = seg[start:end]
                
                # Minimum length 2, Maximum length say 6 to keep it a "phrase"
                # If too long, we can keep the whole thing or break it, but 
                # in a window of 7, 6 is reasonable.
                if 2 <= len(phrase_tokens) <= 8:
                    candidates.append(" ".join(phrase_tokens))
                elif len(phrase_tokens) > 8:
                    # For very long segments, take the parts closest to the entity?
                    # Or just take the first 6?
                    candidates.append(" ".join(phrase_tokens[:6]))
                    candidates.append(" ".join(phrase_tokens[-6:]))
            
        # Deduplicate and filter substrings
        return self._filter_subphrases(list(set(candidates)))

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
        
        # FINAL AGGREGATE DEDUPLICATION
        # This prevents having both "makan siang" and "makan siang gratis" in the final result 
        # even if they came from different articles.
        all_phrases = sorted(phrase_data.keys(), key=len, reverse=True)
        kept_phrases = self._filter_subphrases(all_phrases)
        
        # Filter phrase_data down to kept phrases
        phrase_data = {p: phrase_data[p] for p in kept_phrases}
                        
        # Sort by count desc
        sorted_phrases = sorted(phrase_data.items(), key=lambda x: x[1]['count'], reverse=True)
        
        # Format output
        results = []
        for phrase, data in sorted_phrases:
            # Saliency filter: common phrases are more interesting for framing
            if data['count'] > 1:
                results.append({
                    "phrase": phrase, 
                    "count": data['count'],
                    "sources": list(data['sources'])
                })
        
        return results

