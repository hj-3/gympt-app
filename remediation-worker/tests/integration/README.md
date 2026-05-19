# Remediation Worker - Integration Tests

## Structure

```
integration/
├── kubernetes_test.go       # K8s API integration
├── prometheus_test.go       # Prometheus query tests
└── slack_test.go            # Slack notification tests
```

## Requirements

- Kubernetes cluster (kind/minikube for local)
- Prometheus instance
- Slack webhook (test channel)

## Running

```bash
go test ./tests/integration/... -v -tags=integration
```
