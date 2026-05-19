# Remediation Worker

Automated remediation service for Kubernetes that receives alerts from Prometheus Alertmanager and CloudWatch Events, then executes predefined remediation actions.

## Features

- **Alertmanager Integration**: Receives webhook calls from Prometheus Alertmanager
- **CloudWatch Events**: Processes AWS CloudWatch Events for infrastructure issues
- **Kubernetes Actions**: Restart deployments, scale services, patch resources
- **Argo CD Integration**: Rollback applications to previous revisions
- **Slack Notifications**: Real-time notifications for all remediation actions
- **Safety Mechanisms**:
  - Rate limiting (max actions per hour)
  - Cooldown periods between actions
  - Excluded namespaces and deployments
  - Dry-run mode for testing
- **Observability**: Prometheus metrics and structured JSON logging

## Architecture

```
┌─────────────────┐
│  Alertmanager   │
└────────┬────────┘
         │ webhook
         ▼
┌─────────────────────┐
│ Remediation Worker  │
│                     │
│ - Rate Limiting     │
│ - Cooldown          │
│ - Action Engine     │
└──┬──────────────┬───┘
   │              │
   │              └─────► Slack Notifications
   │
   ├─────► Kubernetes API
   │       - Restart pods
   │       - Scale deployments
   │       - Patch resources
   │
   └─────► Argo CD API
           - Rollback applications
```

## Alert-to-Action Flow

1. **Alert fires** in Prometheus
2. **Alertmanager** routes to remediation-worker webhook
3. **Remediation worker**:
   - Looks up alert in `alert-rules.yaml`
   - Checks rate limits and cooldowns
   - Executes action (restart, scale, rollback, etc.)
   - Records metrics
   - Sends Slack notification
4. **Result** logged and exposed via `/metrics`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DRY_RUN` | Enable dry-run mode | `false` |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | - |
| `ARGOCD_SERVER` | Argo CD server address | `argocd-server.argocd.svc.cluster.local:443` |
| `ARGOCD_AUTH_TOKEN` | Argo CD API token | - |
| `AWS_REGION` | AWS region | `ap-northeast-2` |
| `EKS_CLUSTER_NAME` | EKS cluster name | `gympt-dev-eks` |

### Alert Rules

Alert rules are defined in `/etc/remediation/alert-rules.yaml` (mounted from ConfigMap).

Example rule:

```yaml
- alertName: BackendHighErrorRate
  severity: critical
  action: restart_deployment
  params:
    namespace: backend-api
    deployment: backend-api
    gracePeriod: 30
  dryRun: false
  notifySlack: true
  cooldown: 600
  description: "Restart backend-api deployment due to high 5xx error rate"
```

## Available Actions

### 1. restart_deployment

Performs rolling restart of a deployment.

**Params:**
- `namespace`: Target namespace
- `deployment`: Deployment name
- `gracePeriod`: Grace period in seconds (default: 30)

### 2. scale_deployment

Scales deployment up or down.

**Params:**
- `namespace`: Target namespace
- `deployment`: Deployment name
- `scaleDirection`: `up` or `down`
- `targetReplicas`: Target replica count (can use `+1`, `-1` for relative scaling)
- `maxReplicas`: Maximum replicas (default: 10)
- `minReplicas`: Minimum replicas (default: 1)

### 3. rollback_argocd

Triggers Argo CD rollback to previous revision.

**Params:**
- `application`: Argo CD application name
- `namespace`: `argocd`
- `revisionHistory`: Number of revisions to rollback (default: 1)

### 4. notify_only

Sends notification without taking action.

**Params:**
- `message`: Notification message

### 5. patch_deployment

Applies JSON patch to deployment spec.

**Params:**
- `namespace`: Target namespace
- `deployment`: Deployment name
- `patch`: JSON patch object

## Safety Features

### Rate Limiting

Prevents excessive actions:
- Max restarts per hour: 3
- Max scale-ups per hour: 5
- Max rollbacks per hour: 2

### Cooldown Period

Default 5-minute cooldown between actions on the same deployment.

### Excluded Resources

The following namespaces and deployments are never auto-remediated:
- `kube-system`, `kube-public`, `kube-node-lease`
- `argocd`, `monitoring`
- `kube-prometheus-stack`, `argocd-server`, `remediation-worker`

### Dry-Run Mode

Enable globally via `DRY_RUN=true` to log actions without executing them.

## API Endpoints

### `GET /health`

Health check endpoint.

### `GET /ready`

Readiness check endpoint.

### `GET /metrics`

Prometheus metrics:
- `remediation_actions_total{action_type, namespace, status}`
- `remediation_action_duration_seconds{action_type, namespace}`
- `remediation_cooldown_blocks_total{action_type, namespace}`
- `remediation_rate_limit_blocks_total{action_type}`
- `remediation_dry_run_actions_total{action_type, namespace}`
- `webhook_requests_total{source, status}`
- `active_remediations`

### `POST /webhook/alert`

Alertmanager webhook receiver.

**Payload:** Alertmanager webhook JSON

### `POST /webhook/cloudwatch`

CloudWatch Events webhook receiver.

**Payload:** CloudWatch Event JSON

## Local Development

### Prerequisites

- Python 3.11+
- kubectl configured for target cluster
- Argo CD CLI (optional)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DRY_RUN=true
export LOG_LEVEL=DEBUG
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Run locally
uvicorn app.main:app --reload --port 8080
```

### Test Webhook

```bash
# Send test alert
curl -X POST http://localhost:8080/webhook/alert \
  -H "Content-Type: application/json" \
  -d '{
    "version": "4",
    "groupKey": "test",
    "status": "firing",
    "receiver": "remediation-worker",
    "groupLabels": {},
    "commonLabels": {},
    "commonAnnotations": {},
    "externalURL": "http://localhost",
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "BackendHighErrorRate",
          "namespace": "backend-api",
          "deployment": "backend-api"
        },
        "annotations": {
          "summary": "High error rate detected"
        },
        "startsAt": "2026-05-19T10:00:00Z"
      }
    ]
  }'
```

## Deployment

### Build Docker Image

```bash
docker build -t <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/gympt/remediation-worker:dev-latest .
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/gympt/remediation-worker:dev-latest
```

### Deploy via Helm

```bash
cd gympt-gitops/platform/remediation

# Create secret
kubectl create secret generic remediation-secrets \
  -n workers \
  --from-literal=slack-webhook-url=<SLACK_WEBHOOK_URL> \
  --from-literal=argocd-auth-token=<ARGOCD_TOKEN>

# Install chart
helm install remediation-worker ./chart \
  -n workers \
  -f values-dev.yaml
```

### Configure Alertmanager

Update `platform/monitoring/values-dev.yaml`:

```yaml
alertmanager:
  config:
    receivers:
    - name: 'critical'
      webhook_configs:
      - url: 'http://remediation-worker.workers.svc.cluster.local:8080/webhook/alert'
        send_resolved: true
```

## Monitoring

### View Logs

```bash
kubectl logs -n workers deployment/remediation-worker --follow
```

### Check Metrics

```bash
kubectl port-forward -n workers deployment/remediation-worker 8080:8080

# In another terminal
curl http://localhost:8080/metrics | grep remediation
```

### Slack Notifications

All actions are posted to configured Slack channels with:
- Action type and status
- Target namespace and deployment
- Success/failure indication
- Error details (if failed)
- Dry-run indicator

## Troubleshooting

### Actions Not Executing

1. Check dry-run mode: `kubectl get deployment remediation-worker -n workers -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="DRY_RUN")].value}'`
2. Verify alert-rules ConfigMap is mounted
3. Check rate limits in metrics
4. Review cooldown cache

### Argo CD Rollback Fails

1. Verify `ARGOCD_AUTH_TOKEN` is set correctly
2. Check Argo CD server connectivity
3. Ensure application exists and has history

### Kubernetes API Errors

1. Check ServiceAccount has correct RBAC permissions
2. Verify IRSA role attached to ServiceAccount
3. Review excluded namespaces/deployments

## Security

- Runs as non-root user (UID 1000)
- Read-only root filesystem
- Minimal capabilities (drops ALL)
- IRSA for AWS permissions
- ServiceAccount with least-privilege RBAC

## References

- [Alertmanager Webhook Configuration](https://prometheus.io/docs/alerting/latest/configuration/#webhook_config)
- [Argo CD API](https://argo-cd.readthedocs.io/en/stable/developer-guide/api-docs/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [Alert Rules](../../../gympt-gitops/platform/remediation/alert-rules.yaml)
- [Runbooks](../../../gympt-gitops/platform/remediation/runbooks.md)
