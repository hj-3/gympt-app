# Backend API - Deployment Guide

## Deployment Overview

The backend-api service is deployed using GitOps with Argo CD to Amazon EKS clusters.

**Deployment Pipeline:**
```
Code Push → GitHub Actions → Build Image → Push to ECR → Update GitOps → Argo CD Sync → EKS Deployment
```

---

## Environments

| Environment | Cluster | Namespace | URL |
|-------------|---------|-----------|-----|
| Local | Docker Compose | N/A | http://localhost:8080 |
| Dev | `gympt-dev-eks` | `gympt-dev` | https://api.dev.gympt.example.com |
| Prod | `gympt-prod-eks` | `gympt-prod` | https://api.gympt.example.com |

---

## Local Deployment

### Prerequisites
- Docker & Docker Compose
- Java 17+ (for local development without Docker)

### Using Docker Compose

1. **Build image:**
   ```bash
   docker build -t gympt/backend-api:local .
   ```

2. **Start services:**
   ```bash
   cd ../local
   docker compose up -d backend-api
   ```

3. **Verify:**
   ```bash
   curl http://localhost:8080/actuator/health
   ```

### Standalone (without Docker)

1. **Start dependencies:**
   ```bash
   cd ../local
   ./scripts/local-up.sh
   ```

2. **Run application:**
   ```bash
   ./gradlew bootRun --args='--spring.profiles.active=local'
   ```

---

## AWS Dev Deployment

### Prerequisites
- AWS CLI configured
- kubectl configured for dev cluster
- Argo CD CLI (optional)

### Automated Deployment (Recommended)

1. **Merge to main branch:**
   ```bash
   git checkout main
   git merge feature/my-feature
   git push origin main
   ```

2. **GitHub Actions automatically:**
   - Runs tests
   - Builds Docker image
   - Pushes to ECR
   - Updates image tag in GitOps repo

3. **Argo CD automatically syncs** (if auto-sync enabled)

### Manual Deployment

1. **Build and push image:**
   ```bash
   # Authenticate to ECR
   aws ecr get-login-password --region ap-northeast-2 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com
   
   # Build
   docker build -t backend-api:v1.2.3 .
   
   # Tag
   docker tag backend-api:v1.2.3 \
     <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/gympt/backend-api:v1.2.3
   
   # Push
   docker push <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/gympt/backend-api:v1.2.3
   ```

2. **Update GitOps repository:**
   ```bash
   cd ../../gympt-gitops
   
   # Update image tag
   yq eval '.image.tag = "v1.2.3"' -i apps/backend-api/values-dev.yaml
   
   # Commit and push
   git add apps/backend-api/values-dev.yaml
   git commit -m "chore: update backend-api to v1.2.3"
   git push origin main
   ```

3. **Sync with Argo CD:**
   ```bash
   # Via CLI
   argocd app sync backend-api-dev
   
   # Via UI
   # Navigate to https://argocd.gympt.example.com
   # Click "Sync" on backend-api-dev application
   ```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n gympt-dev -l app=backend-api

# Check logs
kubectl logs -n gympt-dev -l app=backend-api --tail=100 -f

# Check service
kubectl get svc -n gympt-dev backend-api

# Test health endpoint
curl https://api.dev.gympt.example.com/actuator/health
```

---

## Production Deployment

### Production Readiness Checklist

- [ ] **Testing**
  - [ ] All unit tests passing (> 80% coverage)
  - [ ] All integration tests passing
  - [ ] Load testing completed (> 1000 req/sec, P95 < 500ms)
  - [ ] Security scanning passed (Snyk, Trivy)
  
- [ ] **Configuration**
  - [ ] Secrets rotated and stored in Secrets Manager
  - [ ] Resource limits reviewed and approved
  - [ ] HPA configured and tested
  - [ ] Pod disruption budget configured
  
- [ ] **Observability**
  - [ ] Prometheus metrics validated
  - [ ] Grafana dashboards created
  - [ ] CloudWatch alarms configured
  - [ ] PagerDuty integration tested
  
- [ ] **Documentation**
  - [ ] Runbook updated
  - [ ] API changelog updated
  - [ ] Breaking changes documented
  - [ ] Rollback plan documented
  
- [ ] **Approvals**
  - [ ] Code review completed
  - [ ] Architecture review approved
  - [ ] Security review approved
  - [ ] Change request filed and approved

### Blue-Green Deployment Strategy

1. **Deploy to green environment:**
   ```bash
   # Update image tag with prod suffix
   yq eval '.image.tag = "v1.2.3-prod"' -i apps/backend-api/values-prod.yaml
   
   # Commit
   git commit -am "chore(prod): deploy backend-api v1.2.3"
   git push
   ```

2. **Monitor green pods:**
   ```bash
   kubectl get pods -n gympt-prod -l app=backend-api,version=v1.2.3
   
   # Watch logs for errors
   kubectl logs -n gympt-prod -l app=backend-api,version=v1.2.3 -f
   ```

3. **Run smoke tests:**
   ```bash
   # Health check
   curl https://api.gympt.example.com/actuator/health
   
   # Critical endpoints
   curl -X POST https://api.gympt.example.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test"}'
   ```

4. **Switch traffic** (update Ingress/Service):
   ```bash
   kubectl patch ingress backend-api -n gympt-prod \
     --type merge -p '{"spec":{"rules":[{"http":{"paths":[{"backend":{"service":{"name":"backend-api-v1-2-3"}}}]}}]}}'
   ```

5. **Monitor metrics:**
   - Error rate < 0.1%
   - P95 latency < 500ms
   - No 5xx errors
   - Resource usage within limits

### Rollback Plan

**Automatic Rollback Triggers:**
- Error rate > 1% for 5 minutes
- P95 latency > 1000ms for 5 minutes
- Pod crash loop
- Health check failures

**Manual Rollback:**

```bash
# Via Argo CD
argocd app rollback backend-api-prod <previous-revision>

# Via kubectl
kubectl rollout undo deployment/backend-api -n gympt-prod

# Revert GitOps
cd ../../gympt-gitops
git revert HEAD
git push origin main
```

**Verify Rollback:**
```bash
# Check pods are running previous version
kubectl get pods -n gympt-prod -l app=backend-api -o jsonpath='{.items[*].spec.containers[*].image}'

# Check metrics returned to normal
# Navigate to Grafana dashboard
```

---

## Scaling

### Horizontal Pod Autoscaler (HPA)

**Dev Environment:**
```yaml
minReplicas: 2
maxReplicas: 5
targetCPUUtilizationPercentage: 70
targetMemoryUtilizationPercentage: 80
```

**Prod Environment:**
```yaml
minReplicas: 3
maxReplicas: 20
targetCPUUtilizationPercentage: 60
targetMemoryUtilizationPercentage: 70
```

**Manual Scaling:**
```bash
# Scale to 5 replicas
kubectl scale deployment backend-api -n gympt-prod --replicas=5

# Check HPA status
kubectl get hpa -n gympt-prod backend-api
```

### Vertical Scaling

Update resource requests/limits in `values-prod.yaml`:

```yaml
resources:
  requests:
    cpu: 1000m      # 1 CPU
    memory: 2Gi
  limits:
    cpu: 2000m      # 2 CPU
    memory: 4Gi
```

---

## Database Migrations

### Flyway Migrations

Migrations run automatically on application startup.

**Migration Files:** `src/main/resources/db/migration/`

**Naming Convention:** `V{version}__{description}.sql`

Example: `V1__create_users_table.sql`

### Pre-Deployment Migration Check

```bash
# Dry-run migration
./gradlew flywayInfo

# Validate migrations
./gradlew flywayValidate
```

### Rollback Migrations

Flyway doesn't support automatic rollback. Manual process:

1. Create undo script: `U{version}__{description}.sql`
2. Apply manually to database
3. Update Flyway schema history table

**Prevention:**
- Test migrations in dev first
- Use database backups
- Write reversible migrations when possible

---

## Monitoring & Alerting

### Key Metrics

**Application Metrics:**
- `http_server_requests_seconds` - Request duration
- `jvm_memory_used_bytes` - JVM memory usage
- `jdbc_connections_active` - Database connections
- `cache_gets_total` - Redis cache hits/misses

**Business Metrics:**
- `user_registrations_total` - User signups
- `workout_sessions_created_total` - Active sessions
- `api_errors_total` - Error count by endpoint

### Grafana Dashboards

- **Backend API Overview:** https://grafana.gympt.example.com/d/backend-api
- **JVM Metrics:** https://grafana.gympt.example.com/d/jvm-metrics
- **Database Performance:** https://grafana.gympt.example.com/d/db-performance

### CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| High Error Rate | > 1% for 5 min | Page on-call |
| High Latency | P95 > 1s for 5 min | Slack alert |
| Pod Restarts | > 3 in 10 min | Slack alert |
| Database Connections | > 80% pool | Slack alert |
| Memory Usage | > 90% for 5 min | Auto-scale + alert |

---

## Disaster Recovery

### Backup Strategy

**Database:**
- Automated RDS snapshots every 6 hours
- Retention: 7 days (dev), 30 days (prod)
- Cross-region replication for prod

**Configuration:**
- Secrets Manager: automatic backup
- Parameter Store: version history enabled

### Recovery Procedures

**Scenario 1: Complete Service Failure**

1. Check pod status and logs
2. Verify database connectivity
3. Check external service dependencies
4. Rollback to last known good version
5. Escalate if issue persists

**Scenario 2: Database Corruption**

1. Stop all backend-api pods
2. Restore RDS from latest snapshot
3. Apply any missing transactions from logs
4. Restart backend-api pods
5. Verify data integrity

**RTO/RPO:**
- **RTO (Recovery Time Objective):** < 1 hour
- **RPO (Recovery Point Objective):** < 15 minutes

---

## Troubleshooting

### Pod CrashLoopBackOff

```bash
# Check logs
kubectl logs -n gympt-prod backend-api-<pod-id> --previous

# Common causes:
# - Missing environment variables
# - Database connection failure
# - Port already in use
```

### High Memory Usage

```bash
# Get heap dump
kubectl exec -n gympt-prod backend-api-<pod-id> -- \
  jcmd 1 GC.heap_dump /tmp/heapdump.hprof

# Copy heap dump
kubectl cp gympt-prod/backend-api-<pod-id>:/tmp/heapdump.hprof ./heapdump.hprof

# Analyze with VisualVM or Eclipse MAT
```

### Database Connection Pool Exhausted

```bash
# Check active connections
kubectl exec -n gympt-prod backend-api-<pod-id> -- \
  curl http://localhost:8080/actuator/metrics/jdbc.connections.active

# Increase pool size in values.yaml
env:
  - name: DB_POOL_SIZE
    value: "30"
```

---

## Security

### Network Policies

Backend API can communicate with:
- PostgreSQL (port 5432)
- Redis (port 6379)
- agent-service (port 8001)
- posture-analysis-service (port 8002)
- AWS services (HTTPS)

Ingress only from:
- ALB/Ingress controller
- Other services in namespace

### TLS/SSL

- Ingress terminates TLS using ACM certificate
- Internal communication uses service mesh (mutual TLS)

### Secrets Rotation

Automated rotation via AWS Secrets Manager:
- JWT secret: 90 days
- Database password: 180 days

---

## Runbook

For on-call engineers, see detailed runbook:
- [Backend API Runbook](https://wiki.gympt.example.com/runbooks/backend-api)

Quick commands:
```bash
# Check service health
curl https://api.gympt.example.com/actuator/health

# View recent logs
kubectl logs -n gympt-prod -l app=backend-api --tail=100 --timestamps

# Check pod status
kubectl get pods -n gympt-prod -l app=backend-api

# Scale up (if needed)
kubectl scale deployment backend-api -n gympt-prod --replicas=10

# Restart pods (last resort)
kubectl rollout restart deployment/backend-api -n gympt-prod
```

---

**Last Updated:** 2026-05-18  
**On-Call:** backend-oncall@gympt.example.com  
**Slack Channel:** #gympt-backend-alerts
