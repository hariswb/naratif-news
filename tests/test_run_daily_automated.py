import subprocess
import time
import psycopg2
import shutil
from pathlib import Path
import os
import sys

def run_command(command, check=True):
    print(f"Running: {command}")
    subprocess.run(command, shell=True, check=check)

def get_test_db_connection():
    # Matches docker-compose-dev.yml
    return psycopg2.connect(
        dbname="media_pipeline",
        user="postgres",
        password="password",
        host="localhost",
        port=5433 
    )

def test_pipeline_execution():
    print("=== Starting Automated Test ===")
    
    # 1. Start Dev DB
    print("Starting dev database...")
    run_command("docker-compose -f docker-compose-dev.yml up -d")
    
    # Wait for DB to be ready
    print("Waiting for database...")
    for i in range(15):
        try:
            conn = get_test_db_connection()
            conn.close()
            print("Database ready!")
            break
        except Exception as e:
            # print(f"Wait... {e}")
            time.sleep(2)
    else:
        print("Database failed to start.")
        run_command("docker-compose -f docker-compose-dev.yml down -v")
        sys.exit(1)
        
    start_time = time.time()
    
    try:
        # 1.5 Run Migrations
        print("Running Alembic migrations...")
        env = os.environ.copy()
        env['POSTGRES_DB'] = 'media_pipeline'
        env['POSTGRES_USER'] = 'postgres'
        env['POSTGRES_PASSWORD'] = 'password'
        env['POSTGRES_HOST'] = 'localhost'
        env['POSTGRES_PORT'] = '5433'
        
        # Add DB_* vars for run_daily.py (pipeline/db.py)
        env['DB_NAME'] = env['POSTGRES_DB']
        env['DB_USER'] = env['POSTGRES_USER']
        env['DB_PASSWORD'] = env['POSTGRES_PASSWORD']
        env['DB_HOST'] = env['POSTGRES_HOST']
        env['DB_PORT'] = env['POSTGRES_PORT']
        
        # Run alembic using the same python interpreter
        print(f"Running Alembic: {sys.executable} -m alembic upgrade head")
        subprocess.run(f"{sys.executable} -m alembic upgrade head", shell=True, check=True, env=env)

        # 2. Run Pipeline with limit and test mode
        # Need to set ENV vars for DB connection to point to staging
        # env already has the DB vars set above
        
        print("Running pipeline script...")
        cmd = [sys.executable, "run_daily.py", "--limit", "10", "--test-mode"]
        subprocess.run(cmd, env=env, check=True)
        
        # 3. Verify Data
        print("Verifying database content...")
        conn = get_test_db_connection()
        cur = conn.cursor()
        
        # Check articles
        cur.execute("SELECT COUNT(*) FROM articles")
        article_count = cur.fetchone()[0]
        print(f"Articles in DB: {article_count}")
        
        # Check sentiment
        cur.execute("SELECT COUNT(*) FROM sentiment_analysis")
        sentiment_count = cur.fetchone()[0]
        print(f"Sentiment entries in DB: {sentiment_count}")
        
        # Check consistency
        cur.execute("""
            SELECT AVG(sa.id) 
            FROM sentiment_analysis sa 
            JOIN articles a ON sa.article_id = a.id
        """)
        joined = cur.fetchone()[0]
        print(f"Joined verify: {joined}")
        
        # Validate method name
        cur.execute("SELECT DISTINCT method_name FROM sentiment_analysis")
        methods = cur.fetchall()
        print(f"Methods found: {methods}")
        
        assert article_count > 0, "No articles found"
        assert article_count <= 10, "Article limit ignored"
        assert sentiment_count == article_count, "Mismatch between articles and sentiment"
        assert ('inset',) in methods, "Method name 'inset' not found"
        
        print("✅ VERIFICATION SUCCESSFUL")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
        
    finally:
        # 4. Cleanup
        print("Cleaning up...")
        run_command("docker-compose -f docker-compose-dev.yml down -v")
        
        # Remove test data
        test_data = Path("tests/data")
        if test_data.exists():
            shutil.rmtree(test_data)
            print("Removed test artifacts.")

if __name__ == "__main__":
    test_pipeline_execution()
