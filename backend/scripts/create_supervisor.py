#!/usr/bin/env python3

import bcrypt
from sqlalchemy import create_engine
from models.user import User, UserRole
from models.user import _uuid, _now
from core.config import settings

def create_supervisor_account():
    """Create supervisor account with specified credentials"""
    # Create supervisor account
    email = 'supervisor@test.com'
    password = 'Supervisor123!'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        # Check if supervisor already exists
        existing = conn.execute(User.__table__.select().where(User.email == email)).fetchone()
        
        if existing:
            print('✅ Supervisor account already exists')
            print(f'   Email: {email}')
        else:
            # Insert supervisor
            supervisor_id = _uuid()
            
            conn.execute(User.__table__.insert(), {
                'user_id': supervisor_id,
                'email': email,
                'username': 'supervisor',
                'password_hash': password_hash,
                'role': UserRole.SUPERVISOR.value,
                'is_active': 1,
                'storage_quota_mb': 100,
                'storage_used_bytes': 0,
                'created_at': _now(),
                'updated_at': _now()
            })
            
            conn.commit()
            print('✅ Supervisor account created successfully')
            print(f'   Email: {email}')
            print(f'   Password: {password}')
            print(f'   User ID: {supervisor_id}')

if __name__ == "__main__":
    create_supervisor_account()
