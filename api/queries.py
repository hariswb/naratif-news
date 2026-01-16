from sqlalchemy import func, desc, distinct, cast, Date, and_
from sqlalchemy.orm import Session, aliased
from pipeline.storage.models import Article, NamedEntityRecognition, SentimentAnalysis, EntityFraming
from typing import List, Optional

def get_trends_data(db: Session, entity_word: str, start_date, end_date):
    return db.query(
        cast(Article.published_at, Date).label('published_date'),
        SentimentAnalysis.label,
        func.count(Article.id).label('count')
    ).join(NamedEntityRecognition, Article.id == NamedEntityRecognition.article_id)\
     .join(SentimentAnalysis, Article.id == SentimentAnalysis.article_id)\
     .filter(func.lower(NamedEntityRecognition.word) == func.lower(entity_word))\
     .filter(Article.published_at.between(start_date, end_date))\
     .group_by('published_date', SentimentAnalysis.label)\
     .order_by('published_date')\
     .all()

def get_framing_data(db: Session, entity_word: str, start_date, end_date):
    return db.query(
        EntityFraming.framing_phrase,
        func.count(distinct(Article.id)).label('count')
    ).join(Article, Article.id == EntityFraming.article_id)\
     .filter(func.lower(EntityFraming.entity_word) == func.lower(entity_word))\
     .filter(Article.published_at.between(start_date, end_date))\
     .group_by(EntityFraming.framing_phrase)\
     .order_by(desc('count'), EntityFraming.framing_phrase)\
     .limit(50)\
     .all()

def get_network_data(db: Session, entity_word: str, start_date, end_date, min_score: float, max_score: float, entity_groups: Optional[List[str]] = None):
    # 1. Get IDs of articles containing the searched entity
    article_ids_query = db.query(NamedEntityRecognition.article_id)\
        .join(Article, Article.id == NamedEntityRecognition.article_id)\
        .filter(Article.published_at.between(start_date, end_date))\
        .filter(func.lower(NamedEntityRecognition.word) == func.lower(entity_word))\
        .subquery()

    # 2. Get nodes (entities within those articles)
    nodes_query = db.query(
        NamedEntityRecognition.word,
        func.max(NamedEntityRecognition.entity_group).label('entity_group'),
        func.count(distinct(NamedEntityRecognition.article_id)).label('count')
    ).filter(NamedEntityRecognition.article_id.in_(article_ids_query))\
     .filter(~NamedEntityRecognition.word.like('%#%'))\
     .filter(NamedEntityRecognition.score.between(min_score, max_score))
    
    if entity_groups:
        from sqlalchemy import or_
        nodes_query = nodes_query.filter(
            or_(
                NamedEntityRecognition.entity_group.in_(entity_groups),
                func.lower(NamedEntityRecognition.word) == func.lower(entity_word)
            )
        )
    
    # Limit nodes to avoid visual clutter (e.g., top 50 by count)
    # DEDUPLICATION LOGIC: 
    # Group by word only to ensure uniqueness in the visualization. 
    # Using func.max(entity_group) picks a representative group if the same word 
    # was tagged with different groups across articles (e.g. PER vs ORG).
    nodes = nodes_query.group_by(NamedEntityRecognition.word)\
                       .order_by(desc('count'))\
                       .limit(50)\
                       .all()
    
    node_words = [n.word for n in nodes]
    if not node_words:
        return [], []

    # 3. Get links (pairwise co-occurrences within those same articles)
    ner1 = aliased(NamedEntityRecognition)
    ner2 = aliased(NamedEntityRecognition)
    
    links_query = db.query(
        ner1.word.label('source'),
        ner2.word.label('target'),
        func.count(ner1.article_id).label('value')
    ).join(ner2, ner1.article_id == ner2.article_id)\
     .filter(ner1.article_id.in_(article_ids_query))\
     .filter(ner1.word < ner2.word)\
     .filter(ner1.word.in_(node_words))\
     .filter(ner2.word.in_(node_words))
     
    links = links_query.group_by(ner1.word, ner2.word)\
                       .all()

    return nodes, links
