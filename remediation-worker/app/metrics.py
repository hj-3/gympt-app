from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


# Metrics
remediation_actions_total = Counter(
    "remediation_actions_total",
    "Total number of remediation actions attempted",
    ["action_type", "namespace", "status"]
)

remediation_action_duration_seconds = Histogram(
    "remediation_action_duration_seconds",
    "Duration of remediation actions",
    ["action_type", "namespace"]
)

remediation_cooldown_blocks = Counter(
    "remediation_cooldown_blocks_total",
    "Number of actions blocked by cooldown",
    ["action_type", "namespace"]
)

remediation_rate_limit_blocks = Counter(
    "remediation_rate_limit_blocks_total",
    "Number of actions blocked by rate limits",
    ["action_type"]
)

remediation_dry_run_actions = Counter(
    "remediation_dry_run_actions_total",
    "Number of actions executed in dry-run mode",
    ["action_type", "namespace"]
)

webhook_requests_total = Counter(
    "webhook_requests_total",
    "Total webhook requests received",
    ["source", "status"]
)

active_remediations = Gauge(
    "active_remediations",
    "Number of currently active remediations"
)


def get_metrics():
    """Return Prometheus metrics in text format"""
    return generate_latest(), CONTENT_TYPE_LATEST
