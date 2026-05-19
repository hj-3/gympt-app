# Remediation Worker - Unit Tests

## Structure

```
unit/
├── pod_test.go              # Pod remediation tests
├── job_test.go              # Job cleanup tests
├── dlq_test.go              # DLQ processing tests
└── aggregator_test.go       # Alert aggregation tests
```

## Mocking Kubernetes Client

```go
func TestPodRemediation(t *testing.T) {
    clientset := fake.NewSimpleClientset()
    // Create test pods
    // Test remediation logic
}
```

## Running

```bash
go test ./internal/... -v
```
