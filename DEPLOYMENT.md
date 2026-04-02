# Deployment Guide - Energy Dashboard

This guide covers deploying the Energy Dashboard to production environments.

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Docker Deployment](#docker-deployment)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployments](#cloud-deployments)
6. [Environment Configuration](#environment-configuration)
7. [Database Setup](#database-setup)
8. [Post-Deployment Verification](#post-deployment-verification)
9. [Monitoring & Logging](#monitoring--logging)
10. [Troubleshooting](#troubleshooting)

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All tests pass locally and in CI/CD
- [ ] Code reviewed and merged to main branch
- [ ] Security scan completed (no vulnerabilities)
- [ ] Dependencies up to date and pinned
- [ ] Environment variables documented in `.env.production`
- [ ] Database migration scripts tested
- [ ] Backup strategy in place
- [ ] Monitoring and alerting configured
- [ ] Load testing completed
- [ ] Rollback plan documented

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker registry access (Docker Hub, AWS ECR, etc.)

### Building Docker Images

**Backend:**
```bash
cd backend
docker build -f ../infra/docker/backend.Dockerfile -t energy-dashboard-backend:1.0.0 .
```

**Frontend:**
```bash
cd frontend
docker build -f ../infra/docker/frontend.Dockerfile -t energy-dashboard-frontend:1.0.0 .
```

### Running Containers

**Backend:**
```bash
docker run -d \
  --name energy-dashboard-backend \
  -p 8000:8000 \
  --env-file .env.production \
  energy-dashboard-backend:1.0.0
```

**Frontend:**
```bash
docker run -d \
  --name energy-dashboard-frontend \
  -p 80:80 \
  energy-dashboard-frontend:1.0.0
```

### Docker Registry Push

```bash
# Login to registry
docker login

# Tag images
docker tag energy-dashboard-backend:1.0.0 yourusername/energy-dashboard-backend:1.0.0
docker tag energy-dashboard-frontend:1.0.0 yourusername/energy-dashboard-frontend:1.0.0

# Push images
docker push yourusername/energy-dashboard-backend:1.0.0
docker push yourusername/energy-dashboard-frontend:1.0.0
```

## Docker Compose Deployment

### Using docker-compose.yml

```bash
# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backend=3

# Stop services
docker-compose down
```

### Production docker-compose.yml

See `docker-compose.yml` in root directory. Key settings:

- PostgreSQL for persistent data
- Volume mounts for logs and data
- Environment configuration via .env.production
- Resource limits for containers
- Health checks for all services

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl CLI installed
- Container images in registry

### Deployment Files

Location: `infra/kubernetes/`

**Files:**
- `deployment.yaml` - Deployment manifests
- `service.yaml` - Service definitions
- `ingress.yaml` - Ingress configuration

### Deployment Steps

1. **Create namespace:**
   ```bash
   kubectl create namespace energy-dashboard
   ```

2. **Create secrets:**
   ```bash
   kubectl create secret generic energy-dashboard-secrets \
     --from-literal=env-file=<(.env.production) \
     -n energy-dashboard
   ```

3. **Deploy application:**
   ```bash
   kubectl apply -f infra/kubernetes/deployment.yaml -n energy-dashboard
   kubectl apply -f infra/kubernetes/service.yaml -n energy-dashboard
   kubectl apply -f infra/kubernetes/ingress.yaml -n energy-dashboard
   ```

4. **Verify deployment:**
   ```bash
   kubectl get pods -n energy-dashboard
   kubectl describe deployment backend -n energy-dashboard
   kubectl logs deployment/backend -n energy-dashboard
   ```

5. **Access application:**
   ```bash
   kubectl port-forward service/frontend 8080:80 -n energy-dashboard
   # Access at http://localhost:8080
   ```

### Scaling

```bash
# Scale backend to 3 replicas
kubectl scale deployment/backend --replicas=3 -n energy-dashboard

# Scale frontend to 2 replicas
kubectl scale deployment/frontend --replicas=2 -n energy-dashboard
```

### Rolling Updates

```bash
# Update image
kubectl set image deployment/backend \
  backend=yourusername/energy-dashboard-backend:1.1.0 \
  -n energy-dashboard

# Monitor rollout
kubectl rollout status deployment/backend -n energy-dashboard

# Rollback if needed
kubectl rollout undo deployment/backend -n energy-dashboard
```

## Cloud Deployments

### AWS Deployment

#### Using AWS ECS

1. **Create ECR repositories:**
   ```bash
   aws ecr create-repository --repository-name energy-dashboard-backend
   aws ecr create-repository --repository-name energy-dashboard-frontend
   ```

2. **Push images to ECR:**
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin <your-account>.dkr.ecr.<region>.amazonaws.com
   docker push <your-account>.dkr.ecr.<region>.amazonaws.com/energy-dashboard-backend:1.0.0
   ```

3. **Create ECS cluster, task definitions, and services**
   - Use AWS Console or CloudFormation
   - Configure RDS for PostgreSQL
   - Set up ALB for load balancing

4. **Configure environment:**
   - Store secrets in AWS Secrets Manager
   - Reference in task definitions

#### Using AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize application
eb init -p python-3.11 energy-dashboard

# Create environment
eb create production

# Deploy
eb deploy

# View logs
eb logs
```

### Google Cloud Deployment

1. **Create GCP project:**
   ```bash
   gcloud projects create energy-dashboard
   gcloud config set project energy-dashboard
   ```

2. **Enable services:**
   ```bash
   gcloud services enable container.googleapis.com
   gcloud services enable cloudsql.googleapis.com
   ```

3. **Push images to Container Registry:**
   ```bash
   docker tag energy-dashboard-backend gcr.io/energy-dashboard/backend:1.0.0
   docker push gcr.io/energy-dashboard/backend:1.0.0
   ```

4. **Deploy to Cloud Run or GKE:**
   - Cloud Run for serverless
   - GKE for managed Kubernetes

### Azure Deployment

1. **Create container registry:**
   ```bash
   az acr create --resource-group mygroup --name energydashboard --sku Basic
   ```

2. **Push images:**
   ```bash
   docker tag energy-dashboard-backend energydashboard.azurecr.io/backend:1.0.0
   docker push energydashboard.azurecr.io/backend:1.0.0
   ```

3. **Deploy to AKS or Container Instances:**
   - Use Azure CLI or Portal
   - Configure networking and security

## Environment Configuration

### Production .env.production

Key variables for production:

```env
APP_ENV=production
DEBUG=False
LOG_LEVEL=WARNING

API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

FRONTEND_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com

DATABASE_URL=postgresql://prod_user:password@prod-db:5432/energy_db
SQLALCHEMY_ECHO=False

SECRET_KEY=your_secure_random_key_here
ALGORITHM=HS256

# Monitoring
SENTRY_DSN=your_sentry_dsn
```

### Secrets Management

1. **AWS Secrets Manager:**
   ```python
   import boto3
   client = boto3.client('secretsmanager')
   secret = client.get_secret_value(SecretId='energy-dashboard/prod')
   ```

2. **Kubernetes Secrets:**
   ```bash
   kubectl get secret energy-dashboard-secrets -n energy-dashboard -o json
   ```

3. **HashiCorp Vault:**
   - Centralized secret management
   - Integrated with deployment tools

## Database Setup

### PostgreSQL Setup

1. **Create database:**
   ```sql
   CREATE DATABASE energy_db;
   CREATE USER energy_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE energy_db TO energy_user;
   ```

2. **Run migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Seed initial data:**
   ```bash
   python scripts/seed-data.py
   ```

### Backup Strategy

```bash
# Automated daily backup
0 2 * * * pg_dump energy_db | gzip > /backups/energy_db_$(date +\%Y\%m\%d).sql.gz

# Store backups offsite (S3, GCS, etc.)
aws s3 sync /backups s3://energy-dashboard-backups/
```

## Post-Deployment Verification

### Health Checks

```bash
# API health check
curl https://yourdomain.com/api/health

# Frontend availability
curl https://yourdomain.com/

# Database connectivity
kubectl exec -it pod/backend -- python -c "import sqlalchemy; print('Database OK')"
```

### Smoke Tests

```bash
# Run basic functionality tests
pytest tests/integration/test_deployment.py -v

# Load testing
locust -f tests/load_tests/locustfile.py --host https://yourdomain.com
```

### Monitoring Dashboards

- Set up Grafana dashboards
- Configure Prometheus metrics scraping
- Import dashboard templates

## Monitoring & Logging

### Application Logging

```python
# Centralized logging
import logging
logger = logging.getLogger(__name__)
logger.info("Application started")
logger.error("Error occurred", exc_info=True)
```

### Log Aggregation

**ELK Stack (Elasticsearch, Logstash, Kibana):**
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/*.log

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

**CloudWatch (AWS):**
```python
import watchtower
handler = watchtower.CloudWatchLogHandler()
logger.addHandler(handler)
```

### Metrics & Monitoring

```python
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.get("/data")
def get_data():
    request_count.inc()
    # ... endpoint logic ...
```

## Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check connectivity
psql -h db-host -U energy_user -d energy_db

# Verify credentials in .env.production
# Check network/firewall rules
```

**2. API Returns 502 Bad Gateway**
```bash
# Check backend logs
docker logs energy-dashboard-backend

# Verify backend is running
curl http://localhost:8000/health
```

**3. Frontend shows blank page**
```bash
# Check frontend logs
docker logs energy-dashboard-frontend

# Verify API endpoint in config
# Check browser console for errors
```

**4. Scheduler jobs not running**
```bash
# Check APScheduler logs
tail -f logs/app.log | grep APScheduler

# Verify cron syntax in configuration
# Check timezone settings
```

### Performance Issues

**High Memory Usage:**
- Check for memory leaks in code
- Implement pagination for large datasets
- Use database connection pooling
- Monitor with `docker stats`

**Slow API Response:**
- Enable query logging to identify slow queries
- Add database indexes
- Implement caching (Redis)
- Use CDN for static assets

**High CPU Usage:**
- Profile code with `cProfile`
- Optimize data processing logic
- Use async functions where applicable
- Implement rate limiting

### Rollback Procedure

```bash
# Docker Compose
docker-compose down
docker-compose up -d  # Uses previous image version

# Kubernetes
kubectl rollout undo deployment/backend -n energy-dashboard
kubectl rollout undo deployment/frontend -n energy-dashboard

# Database
# Restore from backup
psql energy_db < /backups/energy_db_backup.sql
```

---

**Last Updated**: April 2026
**Version**: 1.0
