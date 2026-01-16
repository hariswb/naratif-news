from sqlalchemy import func, desc, distinct, cast, Date
from sqlalchemy.orm import Session, aliased
from pipeline.storage.models import Article, NamedEntityRecognition, SentimentAnalysis, EntityFraming

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
    ner1 = aliased(NamedEntityRecognition)
    ner2 = aliased(NamedEntityRecognition)
    
    query = db.query(
        ner2.word,
        ner2.entity_group,
        func.count(Article.id).label('count')
    ).join(ner1, Article.id == ner1.article_id)\
     .join(ner2, Article.id == ner2.article_id)\
     .filter(Article.published_at.between(start_date, end_date))\
     .filter(func.lower(ner1.word) == func.lower(entity_word))\
     .filter(func.lower(ner2.word) != func.lower(entity_word))\
     .filter(~ner2.word.like('%#%'))\
     .filter(ner2.score.between(min_score, max_score))

    if entity_groups:
        query = query.filter(ner2.entity_group.in_(entity_groups))

    return query.group_by(ner2.word, ner2.entity_group)\
                .order_by(desc('count'))\
                .limit(100)\
                .all()
