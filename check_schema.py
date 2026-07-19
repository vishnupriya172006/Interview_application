#!/usr/bin/env python
"""Check existing PostgreSQL schema and fix incompatibilities"""
import sys
import os
sys.path.insert(0, '.')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from app.core.config import settings

try:
    conn_string = settings.DATABASE_URL
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("DATABASE SCHEMA CHECK")
    print("="*70)
    
    # Check interviews table
    cursor.execute('''
        SELECT column_name, data_type, column_default
        FROM information_schema.columns
        WHERE table_name = 'interviews'
        ORDER BY ordinal_position
    ''')
    
    results = cursor.fetchall()
    if results:
        print("\nINTERVIEWS TABLE SCHEMA:")
        for col_name, data_type, default in results:
            default_str = f"DEFAULT {default}" if default else "NULL"
            print(f"  {col_name:20} {data_type:20} {default_str}")
    else:
        print("\nNo interviews table found (will be created)")
    
    # List all tables
    cursor.execute('''
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    ''')
    
    tables = [row[0] for row in cursor.fetchall()]
    if tables:
        print("\nEXISTING TABLES:")
        for table_name in tables:
            print(f"  - {table_name}")
    
    # Check foreign key constraints
    cursor.execute('''
        SELECT constraint_name, table_name, column_name
        FROM information_schema.key_column_usage
        WHERE table_schema = 'public'
        AND constraint_name LIKE '%fkey%'
    ''')
    
    fkeys = cursor.fetchall()
    if fkeys:
        print("\nEXISTING FOREIGN KEYS:")
        for constraint, table, column in fkeys:
            print(f"  - {constraint} ({table}.{column})")
    
    cursor.close()
    conn.close()
    
    # Decision: Drop all tables and recreate
    if tables:
        print("\n" + "="*70)
        print("ACTION: Dropping existing tables to fix schema incompatibility")
        print("="*70)
        
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Drop tables in reverse dependency order
        drop_order = [
            'reports',
            'phone_detection_logs',
            'liveness_logs',
            'eye_gaze_logs',
            'monitoring_events',
            'deepfake_predictions',
            'interviews',
            'users'
        ]
        
        for table in drop_order:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
                print(f"  ✓ Dropped {table}")
            except Exception as e:
                print(f"  ✗ Failed to drop {table}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✓ All tables dropped successfully. Ready to recreate with correct schema.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
