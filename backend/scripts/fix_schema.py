#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.config import settings
from config.database import engine

print("Connecting to DB...")
with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE requirement_documents 
        ADD COLUMN IF NOT EXISTS extracted_text TEXT;
    """))
    conn.execute(text("""
        ALTER TABLE requirement_documents 
        ADD COLUMN IF NOT EXISTS content BYTEA;
    """))
    conn.commit()
    print("Added missing columns: extracted_text, content")

    # Verify
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'requirement_documents' 
        AND column_name IN ('extracted_text', 'content');
    """)).fetchall()
    print("Verification - columns now present:")
    for row in result:
        print(f"  {row[0]} ({row[1]}) nullable={row[2]}")
print("Schema fixed successfully!")

