#!/usr/bin/env python3
"""
Migration script to add soft delete functionality to Scout Architect database.
Run this once to add the deleted_at columns.
"""
import psycopg2
import sys

def migrate():
    # Get connection parameters from environment or docker-compose
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="scout_architect",
        user="scout",
        password="scout_password"
    )
    
    cur = conn.cursor()
    
    # Add deleted_at column to term_plans if not exists
    try:
        cur.execute("""
            ALTER TABLE term_plans 
            ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
        """)
        print("✅ Added deleted_at to term_plans")
    except Exception as e:
        print(f"❌ Error adding to term_plans: {e}")
    
    # Add deleted_at column to meeting_plans if not exists
    try:
        cur.execute("""
            ALTER TABLE meeting_plans 
            ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
        """)
        print("✅ Added deleted_at to meeting_plans")
    except Exception as e:
        print(f"❌ Error adding to meeting_plans: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()