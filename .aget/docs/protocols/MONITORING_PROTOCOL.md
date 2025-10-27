# Monitoring Protocol

**Version**: 1.0
**Based on**: L208 lines 301-329 (Observability & Monitoring)
**Last Updated**: 2025-10-26

## Overview

This protocol defines monitoring and observability procedures for document processing pipelines.

## Metrics Collection

### Initialize Metrics Collector

```python
from pipeline.metrics_collector import MetricsCollector

# Initialize collector
collector = MetricsCollector(
    enable_pipeline_metrics=True,
    enable_llm_metrics=True,
    enable_resource_metrics=True
)

print(f"✅ Metrics collector initialized")
```

### Record Pipeline Metrics

```python
# Record document processing
collector.increment_counter(
    "documents_processed_total",
    labels={"status": "success", "task_type": "extraction"}
)

# Record timing
with collector.time_operation("document_processing"):
    # ... process document ...
    pass

# Record LLM usage
collector.observe_histogram(
    "tokens_per_request",
    value=1234,
    labels={"provider": "openai", "model": "gpt-4o"}
)

# Record cost
collector.increment_counter(
    "llm_cost_usd_total",
    value=0.023,
    labels={"provider": "openai"}
)
```

### Get Current Metrics

```python
# Get all metrics
metrics = collector.get_metrics()

print(f"Pipeline Metrics:")
print(f"  Documents processed: {metrics.get('documents_processed_total', 0)}")
print(f"  Processing duration (avg): {metrics.get('processing_duration_avg', 0):.2f}s")
print(f"  Cache hit rate: {metrics.get('cache_hit_rate', 0):.2%}")
print(f"  Total cost: ${metrics.get('llm_cost_usd_total', 0):.2f}")
```

**Bash metrics check**:

```bash
python3 -c "
from pipeline.metrics_collector import MetricsCollector
collector = MetricsCollector()
metrics = collector.get_metrics()
print(f\"Docs processed: {metrics.get('documents_processed_total', 0)}\")
print(f\"Total cost: \${metrics.get('llm_cost_usd_total', 0):.2f}\")
"
```

## Status Tracking

### Track Processing Status

```python
from pipeline.status_tracker import StatusTracker

# Initialize tracker
tracker = StatusTracker()

# Update status
tracker.update_status(
    task_id="task_001",
    status="IN_PROGRESS",
    progress=0.5,
    message="Processing page 5/10"
)

# Get status
status = tracker.get_status("task_001")
print(f"Status: {status.status}")
print(f"Progress: {status.progress:.1%}")
print(f"Message: {status.message}")
```

## Export Metrics

### Export Prometheus Format

```python
# Export metrics for Prometheus
prometheus_metrics = collector.export_prometheus()

# Save to file
with open("metrics.txt", "w") as f:
    f.write(prometheus_metrics)

print(f"✅ Metrics exported to metrics.txt")
```

## Monitoring Dashboard

### Create Status Dashboard

```bash
# Create monitoring script
cat > dashboard.py << 'EOF'
#!/usr/bin/env python3
from pipeline.metrics_collector import MetricsCollector
from pipeline.status_tracker import StatusTracker
import time

def display_dashboard():
    collector = MetricsCollector()
    tracker = StatusTracker()

    while True:
        metrics = collector.get_metrics()

        print("\n" + "="*50)
        print("Document Processing Dashboard")
        print("="*50)

        print(f"\n📊 Pipeline Metrics:")
        print(f"  Documents processed: {metrics.get('documents_processed_total', 0)}")
        print(f"  Success rate: {metrics.get('success_rate', 1.0):.1%}")
        print(f"  Avg duration: {metrics.get('processing_duration_avg', 0):.2f}s")

        print(f"\n💰 Cost Metrics:")
        print(f"  Total cost: ${metrics.get('llm_cost_usd_total', 0):.2f}")
        print(f"  Cache savings: ${metrics.get('cache_savings_usd', 0):.2f}")
        print(f"  Cache hit rate: {metrics.get('cache_hit_rate', 0):.2%}")

        print(f"\n🔧 Resource Metrics:")
        print(f"  Memory usage: {metrics.get('memory_usage_mb', 0):.0f} MB")
        print(f"  CPU usage: {metrics.get('cpu_usage_percent', 0):.1f}%")

        time.sleep(10)

if __name__ == "__main__":
    display_dashboard()
EOF

chmod +x dashboard.py
python3 dashboard.py
```

## Related Protocols

- **PROCESSING_PROTOCOL.md** - Integrate monitoring with processing
- **QUEUE_MANAGEMENT_PROTOCOL.md** - Queue monitoring

## Configuration References

- `configs/metrics.yaml` - Metrics configuration

## Module References

- `src/pipeline/metrics_collector.py` - Metrics collection
- `src/pipeline/status_tracker.py` - Status tracking
