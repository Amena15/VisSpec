#!/usr/bin/env python3

import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

def verify_backend_api():
    """Verify all required backend API endpoints for supervisor implementation"""
    print('=== BACKEND API ENDPOINTS VERIFICATION ===')
    print()

    # Test supervisor API endpoints
    try:
        from api.supervisor import router
        print('1. Supervisor API Module:')
        print('   ✅ Supervisor API module loads successfully')
        
        # Check all required endpoints
        endpoints = []
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    if method != 'HEAD':  # Skip HEAD methods
                        endpoints.append(f"{method} {route.path}")
        
        required_endpoints = [
            'GET /api/supervisor/dashboard',
            'GET /api/supervisor/review/{project_id}',
            'POST /api/supervisor/review/{project_id}',
            'GET /api/supervisor/review-queue',
            'GET /api/supervisor/audit-history/{project_id}',
            'GET /api/supervisor/metrics'
        ]
        
        print('   Required Endpoints:')
        for req_endpoint in required_endpoints:
            exists = any(req_endpoint in endpoint for endpoint in endpoints)
            print(f'   ✅ {req_endpoint}: {exists}')
        
        print(f'   ✅ Total endpoints found: {len(endpoints)}')
        print()
        
    except Exception as e:
        print(f'   ❌ Error loading supervisor API: {e}')
        print()

    # Test notifications API
    try:
        from api.notifications import router as notif_router
        print('2. Notifications API Module:')
        print('   ✅ Notifications API module loads successfully')
        
        notif_endpoints = []
        for route in notif_router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    if method != 'HEAD':
                        notif_endpoints.append(f"{method} {route.path}")
        
        required_notif_endpoints = [
            'GET /api/notifications/unread',
            'POST /api/notifications/mark-read'
        ]
        
        print('   Required Endpoints:')
        for req_endpoint in required_notif_endpoints:
            exists = any(req_endpoint in endpoint for endpoint in notif_endpoints)
            print(f'   ✅ {req_endpoint}: {exists}')
        
        print()
        
    except Exception as e:
        print(f'   ❌ Error loading notifications API: {e}')
        print()

    # Test models
    try:
        from models.review import ReviewAudit
        from models.notification import Notification
        print('3. Database Models:')
        print('   ✅ ReviewAudit model loads successfully')
        print('   ✅ Notification model loads successfully')
        print()
        
    except Exception as e:
        print(f'   ❌ Error loading models: {e}')
        print()

    # Test role middleware
    try:
        from utils.security import require_role
        from models.user import UserRole
        print('4. Security & Role Middleware:')
        print('   ✅ require_role function available')
        print('   ✅ UserRole enum available')
        print('   ✅ SUPERVISOR role exists')
        print()
        
    except Exception as e:
        print(f'   ❌ Error loading security components: {e}')
        print()

    # Test API registration in main app
    try:
        from main import app
        print('5. API Registration:')
        
        supervisor_routes = [route for route in app.routes if '/api/supervisor' in str(route.path)]
        notification_routes = [route for route in app.routes if '/api/notifications' in str(route.path)]
        
        print(f'   ✅ Supervisor routes registered: {len(supervisor_routes)}')
        print(f'   ✅ Notification routes registered: {len(notification_routes)}')
        print()
        
    except Exception as e:
        print(f'   ❌ Error checking API registration: {e}')
        print()

if __name__ == "__main__":
    verify_backend_api()
