#!/usr/bin/env python3

import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
from core.config import settings
import uuid
import bcrypt
from datetime import datetime

def create_test_student():
    """Create a test student account using correct column names"""
    
    # Database connection
    engine = create_engine(settings.DATABASE_URL)
    
    # Student account details
    email = 'student@test.com'
    password = 'Student123!'
    
    try:
        with engine.connect() as connection:
            # Check if student already exists
            result = connection.execute(text("SELECT email FROM users WHERE email = :email"), {"email": email})
            existing = result.fetchone()
            
            if existing:
                print(f"✅ Student account {email} already exists")
                return email
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert student with all required fields
            student_id = str(uuid.uuid4())
            query = text("""
                INSERT INTO users (user_id, email, password_hash, role, username, is_active, is_pre_provisioned, failed_login_attempts, storage_quota_mb, storage_used_bytes, created_at, updated_at)
                VALUES (:user_id, :email, :password_hash, :role, :username, :is_active, :is_pre_provisioned, :failed_login_attempts, :storage_quota_mb, :storage_used_bytes, :created_at, :updated_at)
            """)
            
            connection.execute(query, {
                "user_id": student_id,
                "email": email,
                "password_hash": password_hash,
                "role": "student",
                "username": "teststudent",
                "is_active": 1,
                "is_pre_provisioned": 0,
                "failed_login_attempts": 0,
                "storage_quota_mb": 1000,
                "storage_used_bytes": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            connection.commit()
            
            print(f"✅ Created test student account: {email}")
            print(f"   Password: {password}")
            return email
            
    except Exception as e:
        print(f"❌ Error creating student account: {e}")
        return None

if __name__ == "__main__":
    create_test_student()
