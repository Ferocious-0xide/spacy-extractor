import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from config import DATABASE_URL, REDIS_URL

# Redis connection
redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None

def get_db_connection():
    """Create and return a database connection"""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def initialize_db():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Create documents table to store metadata
            cur.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    upload_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL
                )
            ''')
            
            # Create extracted_data table to store the structured data
            cur.execute('''
                CREATE TABLE IF NOT EXISTS extracted_data (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id),
                    entity_type TEXT NOT NULL,
                    entity_text TEXT NOT NULL,
                    confidence FLOAT,
                    page_num INTEGER,
                    position_data JSONB
                )
            ''')
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        conn.close()

def save_document_metadata(filename):
    """Save document metadata and return the document ID"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents (filename, status) VALUES (%s, %s) RETURNING id",
                (filename, "processing")
            )
            document_id = cur.fetchone()[0]
            return document_id
    finally:
        conn.close()

def update_document_status(document_id, status):
    """Update the processing status of a document"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET status = %s WHERE id = %s",
                (status, document_id)
            )
    finally:
        conn.close()

def save_extracted_entities(document_id, entities):
    """Save the extracted entities to the database"""
    if not entities:
        return
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for entity in entities:
                cur.execute(
                    """
                    INSERT INTO extracted_data 
                    (document_id, entity_type, entity_text, confidence, page_num, position_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        document_id,
                        entity['type'],
                        entity['text'],
                        entity.get('confidence', 0.0),
                        entity.get('page_num', 0),
                        entity.get('position', {})
                    )
                )
    finally:
        conn.close()

def get_document_data(document_id):
    """Get all extracted data for a document"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get document metadata
            cur.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
            document = cur.fetchone()
            
            if not document:
                return None
                
            # Get extracted entities
            cur.execute(
                "SELECT * FROM extracted_data WHERE document_id = %s ORDER BY page_num, id",
                (document_id,)
            )
            entities = cur.fetchall()
            
            return {
                "document": document,
                "entities": entities
            }
    finally:
        conn.close()

def get_all_documents():
    """Get a list of all documents"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM documents ORDER BY upload_date DESC")
            return cur.fetchall()
    finally:
        conn.close()