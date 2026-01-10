import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pipeline.storage.models import Article, SentimentAnalysis, PipelineRun, RunStatistic, TopicModelling, NamedEntityRecognition, EntityFraming
from pipeline.storage.database import SessionLocal

logger = logging.getLogger(__name__)

def get_db_session():
    """Create a new SQLAlchemy session."""
    return SessionLocal()

def insert_articles(session: Session, articles, run_id, run_date):
    """
    Insert articles into database using SQLAlchemy ORM.
    Handles upsert on URL conflict.
    Returns: dict mapping url -> id
    """
    if not articles:
        return {}
        
    # Prepare data for bulk insert/upsert
    values = []
    for article in articles:
        values.append({
            'title': article.get('title'),
            'url': article.get('url'),
            'source': article.get('source'),
            'summary': article.get('summary'),
            'published_at': article.get('published'),
            'run_id': run_id,
            'run_date': run_date
        })
    
    # Use PostgreSQL specific insert for ON CONFLICT support
    stmt = pg_insert(Article).values(values)
    
    stmt = stmt.on_conflict_do_update(
        index_elements=['url'],
        set_={
            'title': stmt.excluded.title,
            'summary': stmt.excluded.summary
        }
    ).returning(Article.id, Article.url)
    
    try:
        result = session.execute(stmt)
        session.commit()
        
        url_to_id = {row.url: row.id for row in result}
        logger.info(f"Inserted/Updated {len(url_to_id)} articles")
        return url_to_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert articles: {e}")
        raise

def insert_sentiment_results(session: Session, sentiment_results):
    """
    Insert sentiment analysis results using ORM.
    sentiment_results: list of dicts {article_id, method_name, output: {polarity, label, raw_score}}
    """
    if not sentiment_results:
        return

    try:
        # Using bulk_insert_mappings is efficient for simple inserts
        mappings = []
        for res in sentiment_results:
            output = res['output']
            mappings.append({
                "article_id": res['article_id'],
                "method_name": res['method_name'],
                "polarity": output.get('polarity', 0.0),
                "label": output.get('label', 'neutral'),
                "score": output.get('raw_score', 0.0)
            })
        
        session.bulk_insert_mappings(SentimentAnalysis, mappings)
        session.commit()
        logger.info(f"Inserted {len(mappings)} sentiment results")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert sentiment results: {e}")
        raise

# ... (previous content)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert sentiment results: {e}")
        raise

def create_pipeline_run(session: Session, run_id, run_date):
    """Create a new pipeline run record."""
    try:
        new_run = PipelineRun(
            run_id=run_id,
            run_date=run_date,
            started_at=datetime.now(),
            status='running'
        )
        session.add(new_run)
        session.commit()
        session.refresh(new_run)
        logger.info(f"Created pipeline run: {run_id}")
        return new_run.id
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create pipeline run: {e}")
        raise

def update_pipeline_run(session: Session, run_id, stage=None, stats=None, status=None, errors=None):
    """Update pipeline run with stage completion and statistics."""
    try:
        # Retrieve the run object
        # Note: We query by run_id string, not primary key ID
        run = session.query(PipelineRun).filter(PipelineRun.run_id == run_id).first()
        
        if not run:
            logger.warning(f"Pipeline run {run_id} not found for update")
            return

        if stage:
            # Dynamically set the completed flag
            setattr(run, f"{stage}_completed", True)
        
        if stats:
            for key, value in stats.items():
                if hasattr(run, key):
                    setattr(run, key, value)
        
        if status:
            run.status = status
            if status == 'completed':
                run.completed_at = datetime.now()
        
        if errors:
            run.errors = errors
            
        session.commit()
        # logger.info(f"Updated pipeline run: {run_id}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update pipeline run: {e}")
        raise

def insert_run_statistics(session: Session, run_id, stage, stats):
    """Insert detailed statistics for a pipeline stage."""
    if not stats:
        return

    try:
        stat_objects = []
        for metric_name, metric_value in stats.items():
            details = None
            val = None
            
            if isinstance(metric_value, (int, float)):
                val = float(metric_value)
            else:
                details = metric_value  # JSON column handles dicts/lists
            
            stat = RunStatistic(
                run_id=run_id,
                stage=stage,
                metric_name=metric_name,
                metric_value=val,
                details=details
            )
            stat_objects.append(stat)
            
        session.add_all(stat_objects)
        session.commit()
        logger.info(f"Inserted statistics for stage: {stage}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert statistics: {e}")
        raise

def insert_topic_models(session: Session, topic_results):
    """
    Insert topic modelling results.
    topic_results: List of dicts with keys (article_id, method_name, topic_index, keywords)
    """
    if not topic_results:
        return
        
    try:
        # Prepare data for bulk insert
        mappings = []
        for result in topic_results:
            mappings.append({
                "article_id": result['article_id'],
                "method_name": result['method_name'],
                "topic_index": result['topic_index'],
                "keywords": result['keywords']
            })
            
        session.bulk_insert_mappings(TopicModelling, mappings)
        session.commit()
        logger.info(f"Inserted topic modelling results for {len(topic_results)} articles")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert topic models: {e}")
        raise

def insert_ner_results(session: Session, ner_results):
    """
    Insert NER results.
    ner_results: List of dicts with keys (article_id, method_name, output: [entities])
    """
    if not ner_results:
        return
        
    try:
        # Prepare data for bulk insert - flatten entities
        mappings = []
        for result in ner_results:
            article_id = result['article_id']
            method_name = result['method_name']
            entities = result.get('output', [])
            
            for entity in entities:
                mappings.append({
                    "article_id": article_id,
                    "method_name": method_name,
                    "entity_group": entity.get('entity_group', 'UNKNOWN'),
                    "word": entity.get('word', ''),
                    "score": entity.get('score', 0.0),
                    "start_char": entity.get('start', 0),
                    "end_char": entity.get('end', 0)
                })
            
        if mappings:
            session.bulk_insert_mappings(NamedEntityRecognition, mappings)
            session.commit()
            logger.info(f"Inserted {len(mappings)} NER entities")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert NER results: {e}")
        raise

def insert_framing_results(session: Session, framing_results):
    """
    Insert Entity Framing results.
    framing_results: List of dicts with keys (article_id, entity_word, framing_phrase, method_name)
    """
    if not framing_results:
        return
        
    try:
        # Prepare data for bulk insert
        mappings = []
        for result in framing_results:
            mappings.append({
                "article_id": result['article_id'],
                "entity_word": result['entity_word'],
                "framing_phrase": result['framing_phrase'],
                "method_name": result.get('method_name', 'ngram_window')
            })
            
        if mappings:
            session.bulk_insert_mappings(EntityFraming, mappings)
            session.commit()
            logger.info(f"Inserted {len(mappings)} framing phrases")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to insert framing results: {e}")
        raise

def delete_framing_for_articles(session: Session, article_ids: list):
    """
    Delete existing framing results for a list of articles.
    Used to ensure idempotency when re-running extraction.
    """
    if not article_ids:
        return
        
    try:
        session.query(EntityFraming).filter(EntityFraming.article_id.in_(article_ids)).delete(synchronize_session=False)
        session.commit()
        # logger.info(f"Deleted old framing results for {len(article_ids)} articles")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete old framing results: {e}")
        raise
