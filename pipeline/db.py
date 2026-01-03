import psycopg2
from psycopg2.extras import execute_batch
import logging
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manage PostgreSQL database connections."""
    
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
    
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            # logger.info("Database connection established")
            return self.conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            # logger.info("Database connection closed")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def get_db_connection():
    """Create database connection from environment variables."""
    return DatabaseConnection(
        dbname=os.getenv('DB_NAME', 'media_monitoring'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432))
    )

def insert_articles(db_conn, articles, run_id, run_date):
    """
    Insert articles into database and return mapping of url -> id.
    Strictly follows schema: url, title, summary, source, published_at, run_id, run_date.
    """
    insert_query = """
        INSERT INTO articles (
            url, title, summary, source, published_at,
            run_id, run_date
        ) VALUES %s
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            summary = EXCLUDED.summary
        RETURNING id, url
    """
    
    data = []
    for article in articles:
        data.append((
            article.get('url'),
            article.get('title'),
            article.get('summary'),
            article.get('source'),
            article.get('published'),
            run_id,
            run_date
        ))
    
    url_to_id = {}
    
    try:
        with db_conn.conn.cursor() as cursor:
            # execute_batch doesn't support RETURNING easily with result retrieval
            # So we use executemany or loop. efficiently we want to get IDs.
            # actually execute_batch with returning is complex.
            # Let's use simple loop for now or fetch back?
            # Or use 'executemany' which might not return results in all drivers.
            # Alternative: INSERT ... RETURNING id, url
            
            # For simplicity and correctness with RETURNING, let's iterate or find batch way.
            # psycopg2 'execute_values' is better for this.
            from psycopg2.extras import execute_values
            
            result = execute_values(
                cursor, 
                insert_query, 
                data, 
                template=None, 
                page_size=100, 
                fetch=True
            )
            
            for row in result:
                url_to_id[row[1]] = row[0]
                
            db_conn.conn.commit()
            logger.info(f"Inserted/Updated {len(url_to_id)} articles")
            return url_to_id

    except Exception as e:
        db_conn.conn.rollback()
        logger.error(f"Failed to insert articles: {e}")
        raise

def insert_sentiment_results(db_conn, sentiment_results):
    """
    Insert sentiment analysis results.
    sentiment_results: list of dicts {article_id, method_name, output}
    """
    insert_query = """
        INSERT INTO sentiment_analysis (
            article_id, method_name, output
        ) VALUES %s
    """
    
    data = []
    for res in sentiment_results:
        data.append((
            res['article_id'],
            res['method_name'],
            json.dumps(res['output'])
        ))
        
    try:
        with db_conn.conn.cursor() as cursor:
            from psycopg2.extras import execute_values
            execute_values(cursor, insert_query, data)
            db_conn.conn.commit()
            logger.info(f"Inserted {len(data)} sentiment results")
    except Exception as e:
        db_conn.conn.rollback()
        logger.error(f"Failed to insert sentiment results: {e}")
        raise

def create_pipeline_run(db_conn, run_id, run_date):
    """Create a new pipeline run record."""
    insert_query = """
        INSERT INTO pipeline_runs (
            run_id, run_date, started_at, status
        ) VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    try:
        with db_conn.conn.cursor() as cursor:
            cursor.execute(insert_query, (run_id, run_date, datetime.now(), 'running'))
            run_pk = cursor.fetchone()[0]
            db_conn.conn.commit()
            logger.info(f"Created pipeline run: {run_id}")
            return run_pk
    except Exception as e:
        db_conn.conn.rollback()
        logger.error(f"Failed to create pipeline run: {e}")
        raise

def update_pipeline_run(db_conn, run_id, stage=None, stats=None, status=None, errors=None):
    """Update pipeline run with stage completion and statistics."""
    updates = []
    params = []
    
    if stage:
        updates.append(f"{stage}_completed = TRUE")
    
    if stats:
        for key, value in stats.items():
            if key in ['total_sources', 'total_fetched', 'total_parsed', 'total_cleaned', 'total_analyzed']:
                updates.append(f"{key} = %s")
                params.append(value)
    
    if status:
        updates.append("status = %s")
        params.append(status)
        
        if status == 'completed':
            updates.append("completed_at = %s")
            params.append(datetime.now())
    
    if errors:
        updates.append("errors = %s")
        params.append(errors)
    
    if not updates:
        return
    
    params.append(run_id)
    update_query = f"""
        UPDATE pipeline_runs 
        SET {', '.join(updates)}
        WHERE run_id = %s
    """
    
    try:
        with db_conn.conn.cursor() as cursor:
            cursor.execute(update_query, params)
            db_conn.conn.commit()
            # logger.info(f"Updated pipeline run: {run_id}")
    except Exception as e:
        db_conn.conn.rollback()
        logger.error(f"Failed to update pipeline run: {e}")
        raise

def insert_run_statistics(db_conn, run_id, stage, stats):
    """Insert detailed statistics for a pipeline stage."""
    insert_query = """
        INSERT INTO run_statistics (
            run_id, stage, metric_name, metric_value, details
        ) VALUES (%s, %s, %s, %s, %s::jsonb)
    """
    
    data = []
    for metric_name, metric_value in stats.items():
        if isinstance(metric_value, (int, float)):
            data.append((run_id, stage, metric_name, metric_value, None))
        else:
            data.append((run_id, stage, metric_name, None, json.dumps(metric_value)))
    
    try:
        with db_conn.conn.cursor() as cursor:
            execute_batch(cursor, insert_query, data)
            db_conn.conn.commit()
            logger.info(f"Inserted statistics for stage: {stage}")
    except Exception as e:
        db_conn.conn.rollback()
        logger.error(f"Failed to insert statistics: {e}")
        raise