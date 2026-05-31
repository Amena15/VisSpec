#!/usr/bin/env python3

import sys
sys.path.append('.')
import bcrypt
from sqlalchemy import create_engine
from models.user import User, UserRole
from core.config import settings
import uuid
from datetime import datetime

def create_test_student():
    """Create a test student account for notification testing"""
    
    # Database connection
    engine = create_engine(settings.DATABASE_URL)
    
    # Student account details
    email = 'student@test.com'
    password = 'Student123!'
    
    try:
        with engine.connect() as connection:
            # Check if student already exists
            existing = connection.execute(
                "SELECT email FROM users WHERE email = %s", (email,)
            ).fetchone()
            
            if existing:
                print(f"✅ Student account {email} already exists")
                return email
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create student user
            student_data = {
                'user_id': str(uuid.uuid4()),
                'email': email,
                'password_hash': password_hash,
                'role': UserRole.STUDENT.value,
                'full_name': 'Test Student',
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert student
            columns = ', '.join(student_data.keys())
            placeholders = ', '.join(['%s'] * len(student_data))
            query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
            
            connection.execute(query, tuple(student_data.values()))
            connection.commit()
            
            print(f"✅ Created test student account: {email}")
            print(f"   Password: {password}")
            return email
            
    except Exception as e:
        print(f"❌ Error creating student account: {e}")
        return None

if __name__ == "__main__":
    create_test_student()
