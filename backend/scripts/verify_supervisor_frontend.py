#!/usr/bin/env python3

import os
import re

def verify_frontend_implementation():
    """Verify all required frontend components for supervisor implementation"""
    print('=== FRONTEND IMPLEMENTATION VERIFICATION ===')
    print()

    frontend_path = '/Users/amena/Documents/FYPCode/VisSpec/frontend/src'
    
    # Check App.jsx routing
    print('1. App.jsx Routing Configuration:')
    app_file = os.path.join(frontend_path, 'App.jsx')
    if os.path.exists(app_file):
        with open(app_file, 'r') as f:
            content = f.read()
        
        # Check supervisor routes
        supervisor_routes = [
            'path="/supervisor"',
            'path="/supervisor/review/:project_id"',
            'SupervisorDashboard',
            'SupervisorReview'
        ]
        
        print('   Required Routes:')
        for route in supervisor_routes:
            exists = route in content
            print(f'   ✅ {route}: {exists}')
        
        # Check role-based redirect
        role_redirect = 'decoded.role === \'supervisor\'' in content
        print(f'   ✅ Supervisor role redirect: {role_redirect}')
        print()
        
    else:
        print('   ❌ App.jsx not found')
        print()

    # Check MainLayout.jsx navigation
    print('2. MainLayout.jsx Navigation:')
    layout_file = os.path.join(frontend_path, 'components/MainLayout.jsx')
    if os.path.exists(layout_file):
        with open(layout_file, 'r') as f:
            content = f.read()
        
        # Check supervisor navigation items
        supervisor_nav_items = [
            'Dashboard',
            'Reviews', 
            'Reports',
            'Settings'
        ]
        
        # Check if supervisor role has different navigation
        supervisor_nav_check = 'currentUser.role === \'supervisor\'' in content
        
        print('   Supervisor Navigation:')
        print(f'   ✅ Role-based navigation: {supervisor_nav_check}')
        
        if supervisor_nav_check:
            # Extract supervisor navigation section
            supervisor_section = re.search(r'currentUser\.role === \'supervisor\'\s*\?\s*\[(.*?)\]:', content, re.DOTALL)
            if supervisor_section:
                nav_content = supervisor_section.group(1)
                for item in supervisor_nav_items:
                    exists = item in nav_content
                    print(f'   ✅ {item}: {exists}')
        
        print()
        
    else:
        print('   ❌ MainLayout.jsx not found')
        print()

    # Check SupervisorDashboard.jsx
    print('3. SupervisorDashboard.jsx:')
    dashboard_file = os.path.join(frontend_path, 'pages/SupervisorDashboard.jsx')
    if os.path.exists(dashboard_file):
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Check required features
        dashboard_features = [
            'apiClient.get(\'/api/supervisor/dashboard\')',
            'apiClient.get(\'/api/supervisor/metrics\')',
            'review_status',
            'quality_score',
            'defect_count',
            'Link to={`/supervisor/review/'
        ]
        
        print('   Required Features:')
        for feature in dashboard_features:
            exists = feature in content
            print(f'   ✅ {feature}: {exists}')
        print()
        
    else:
        print('   ❌ SupervisorDashboard.jsx not found')
        print()

    # Check SupervisorReview.jsx
    print('4. SupervisorReview.jsx:')
    review_file = os.path.join(frontend_path, 'pages/SupervisorReview.jsx')
    if os.path.exists(review_file):
        with open(review_file, 'r') as f:
            content = f.read()
        
        # Check required features
        review_features = [
            'apiClient.get(`/api/supervisor/review/${project_id}`)',
            'apiClient.post(`/api/supervisor/review/${project_id}`)',
            'decision',
            'comments',
            'Read-only traceability',
            'Submit Review'
        ]
        
        print('   Required Features:')
        for feature in review_features:
            exists = feature in content
            print(f'   ✅ {feature}: {exists}')
        print()
        
    else:
        print('   ❌ SupervisorReview.jsx not found')
        print()

    # Check notifications banner
    print('5. AnalystNotificationsBanner.jsx:')
    notif_file = os.path.join(frontend_path, 'pages/AnalystNotificationsBanner.jsx')
    if os.path.exists(notif_file):
        with open(notif_file, 'r') as f:
            content = f.read()
        
        # Check required features
        notif_features = [
            'apiClient.get(\'/api/notifications/unread\')',
            'apiClient.post(\'/api/notifications/mark-read\')',
            'review_approved',
            'review_changes_requested',
            'Mark read'
        ]
        
        print('   Required Features:')
        for feature in notif_features:
            exists = feature in content
            print(f'   ✅ {feature}: {exists}')
        print()
        
    else:
        print('   ❌ AnalystNotificationsBanner.jsx not found')
        print()

    # Check API service
    print('6. API Service Configuration:')
    api_file = os.path.join(frontend_path, 'services/api.js')
    if os.path.exists(api_file):
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check if JWT token is properly handled
        api_features = [
            'Authorization',
            'Bearer',
            'localStorage.getItem(\'token\')'
        ]
        
        print('   Required Features:')
        for feature in api_features:
            exists = feature in content
            print(f'   ✅ {feature}: {exists}')
        print()
        
    else:
        print('   ❌ API service not found')
        print()

if __name__ == "__main__":
    verify_frontend_implementation()
