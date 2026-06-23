# VisSpec: Deployment & Launch Guide
**Version:** 1.0  
**Last Updated:** 2026-06-23

---

## Quick Start (Local Testing)

### Prerequisites
- Python 3.13+
- Node 18+ LTS
- PostgreSQL 14+
- Git

### 1. Backend Setup & Launch

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY

# Run database migrations
alembic upgrade head

# Start backend server
python main.py
# Server runs on http://localhost:8000
```

**Verify Backend:**
```bash
curl http://localhost:8000/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"yousef@visspec.com","password":"Yousef@2026"}'

# Expected: JWT token in response
```

### 2. Frontend Setup & Launch

```bash
# In new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend runs on http://localhost:3002

# Or build for production
npm run build
npm run preview  # Preview production build locally
```

**Verify Frontend:**
- Open http://localhost:3002 in browser
- Should see login page
- Login with yousef@visspec.com / Yousef@2026
- Should redirect to dashboard

---

## Production Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose -f docker-compose.test.yml up -d

# Verify services
docker-compose logs backend  # Check backend startup
docker-compose logs frontend # Check frontend startup

# Run migrations
docker exec visspec-backend alembic upgrade head

# Verify
curl http://localhost:8000/api/health
```

### Option 2: Manual Cloud Deployment

#### Backend (e.g., AWS EC2, Heroku, Railway)

1. **Clone repository to server:**
   ```bash
   git clone <repo-url> /app/visspec
   cd /app/visspec/backend
   ```

2. **Setup environment:**
   ```bash
   python3 -m venv /var/www/visspec/venv
   source /var/www/visspec/venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cat > /var/www/visspec/.env << 'ENVEOF'
   DATABASE_URL=postgresql+asyncpg://user:password@db.example.com:5432/visspec
   JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxx
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   CORS_ORIGINS=["https://visspec.example.com"]
   ENVEOF
   ```

4. **Setup systemd service:**
   ```bash
   cat > /etc/systemd/system/visspec-backend.service << 'SVCEOF'
   [Unit]
   Description=VisSpec Backend API
   After=network.target postgresql.service
   
   [Service]
   Type=notify
   User=www-data
   WorkingDirectory=/var/www/visspec
   ExecStart=/var/www/visspec/venv/bin/python main.py
   Restart=on-failure
   RestartSec=10
   StandardOutput=journal
   StandardError=journal
   
   [Install]
   WantedBy=multi-user.target
   SVCEOF
   
   systemctl daemon-reload
   systemctl enable visspec-backend
   systemctl start visspec-backend
   ```

5. **Setup reverse proxy (nginx):**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name api.visspec.example.com;
       
       ssl_certificate /etc/letsencrypt/live/api.visspec.example.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/api.visspec.example.com/privkey.pem;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_http_version 1.1;
           proxy_set_header Connection "";
           
           # WebSocket support (if needed)
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
       
       # Security headers
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
       add_header X-Content-Type-Options "nosniff" always;
       add_header X-Frame-Options "DENY" always;
       add_header X-XSS-Protection "1; mode=block" always;
   }
   ```

#### Frontend (e.g., Vercel, Netlify, AWS S3 + CloudFront)

1. **Build production bundle:**
   ```bash
   cd frontend
   npm run build
   # Creates optimized dist/ folder
   ```

2. **Deploy to CDN/Static Host:**
   
   **Option A: Vercel (Recommended)**
   ```bash
   npm install -g vercel
   vercel --prod
   ```
   
   **Option B: Netlify**
   ```bash
   npm run build
   netlify deploy --prod --dir=dist
   ```
   
   **Option C: AWS S3 + CloudFront**
   ```bash
   aws s3 sync dist/ s3://visspec-frontend-bucket/ --delete
   aws cloudfront create-invalidation --distribution-id E123ABC --paths "/*"
   ```

3. **Configure environment:**
   ```bash
   # Set VITE_API_BASE_URL to production backend URL
   echo "VITE_API_BASE_URL=https://api.visspec.example.com" > frontend/.env.production
   npm run build
   ```

#### Database Setup (PostgreSQL)

```bash
# Create database and user
createdb visspec
createuser visspec_app -P  # Creates user with password prompt

# Grant privileges
psql -c "GRANT ALL PRIVILEGES ON DATABASE visspec TO visspec_app;"
psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO visspec_app;"

# Run migrations
cd backend
DATABASE_URL="postgresql://visspec_app:password@localhost:5432/visspec" \
  alembic upgrade head
```

---

## Post-Deployment Verification

### Health Checks

```bash
# Backend health
curl https://api.visspec.example.com/api/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"yousef@visspec.com","password":"Yousef@2026"}'

# Should return: {"access_token":"...", "token_type":"bearer"}

# Frontend health
curl https://visspec.example.com/
# Should return HTML content (status 200)
```

### Smoke Tests

1. **Login Flow:**
   - Navigate to https://visspec.example.com
   - Login with yousef@visspec.com / Yousef@2026
   - Verify token is stored in localStorage
   - Verify redirect to /dashboard

2. **Document Upload:**
   - Upload test document (SRS.txt)
   - Verify file appears in document list
   - Check backend logs for processing

3. **Analysis:**
   - Select document
   - Trigger AI validation
   - Verify results display without errors
   - Check browser console for JS errors

4. **Report Export:**
   - Generate report
   - Verify PDF downloads
   - Check file is valid (open in PDF reader)

### Log Verification

```bash
# Backend logs
journalctl -u visspec-backend -f

# Frontend logs (in browser console)
# Check for any ERROR or WARN messages
```

---

## Monitoring & Maintenance

### Application Monitoring

1. **Error Tracking (Sentry or similar):**
   ```python
   # In backend/main.py
   import sentry_sdk
   sentry_sdk.init("https://key@sentry.example.com/project")
   ```

2. **Performance Monitoring (DataDog):**
   - Monitor API response times
   - Track database query performance
   - Alert on errors (5xx) > threshold

3. **Frontend Monitoring:**
   - Setup Google Analytics or equivalent
   - Monitor page load times
   - Track user interactions

### Database Maintenance

```bash
# Weekly: Analyze and vacuum
psql visspec -c "VACUUM ANALYZE;"

# Daily backup:
pg_dump visspec | gzip > /backups/visspec_$(date +%Y%m%d).sql.gz

# Retention: Keep 30 days of backups
find /backups -name "visspec_*.sql.gz" -mtime +30 -delete
```

### Security Updates

```bash
# Check for dependency updates
cd backend
pip list --outdated
pip install --upgrade <package>

cd ../frontend
npm outdated
npm update

# Test after updates
pytest tests/unit/
npm run test
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
journalctl -u visspec-backend -n 50

# Common issues:
# 1. Database connection: Check DATABASE_URL, postgres running
# 2. Port in use: sudo lsof -i :8000
# 3. Missing env var: Check .env file
# 4. Migration failed: alembic current, alembic downgrade base, alembic upgrade head
```

### Frontend Not Loading

```bash
# Check browser console (F12) for errors
# Verify VITE_API_BASE_URL is correct
# Check nginx/server response: curl -I https://visspec.example.com
# Check CDN cache: Invalidate CloudFront distribution
```

### API Errors

```bash
# Check backend is responding
curl -v https://api.visspec.example.com/api/health

# Check JWT token valid
curl -H "Authorization: Bearer <token>" https://api.visspec.example.com/api/documents

# Check CORS headers (browser console)
# Verify CORS_ORIGINS in .env includes frontend URL
```

---

## Rollback Procedure

If issues occur post-deployment:

```bash
# Backend rollback
systemctl stop visspec-backend
cd /var/www/visspec
git checkout HEAD~1  # Previous commit
source venv/bin/activate
pip install -r requirements.txt
systemctl start visspec-backend

# Database rollback (if migration failed)
alembic current  # Check current revision
alembic downgrade -1  # Downgrade one revision

# Frontend rollback
# For Vercel/Netlify: Automatic - click previous deployment
# For S3: Keep previous dist/ backup, sync again to S3
```

---

## Performance Optimization

### Backend
- Enable Redis caching for frequent queries
- Use connection pooling (SQLAlchemy pool_pre_ping)
- Setup Gunicorn with multiple workers: `gunicorn main:app --workers 4`
- Enable gzip compression in nginx

### Frontend
- Enable service workers for offline support
- Configure resource hints (dns-prefetch, preconnect)
- Lazy-load route components
- Compress images (WebP format)

---

## Support & Escalation

### Critical Issues (System Down)
1. Page on-call engineer immediately
2. Check backend logs: `journalctl -u visspec-backend -f`
3. Check database: `psql visspec -c "SELECT 1;"`
4. Failover to backup if available

### High Priority (Features Broken)
1. Reproduce issue locally if possible
2. Check recent deployments for regression
3. Review error logs for patterns
4. Deploy hotfix if simple, or rollback

### Normal Priority
1. Create bug report with reproduction steps
2. Add to sprint backlog
3. Plan fix for next release

---

## Version Management

Current version: 1.0.0

Update version after deployment:
```bash
# Tag release
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0

# Update version in:
# - frontend/package.json
# - backend/setup.py (if applicable)
# - CHANGELOG.md
```

---

*End of Deployment Guide*
