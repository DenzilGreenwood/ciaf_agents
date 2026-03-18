# Million Agent Interactions - Load Testing Guide

**CIAF-LCM Agentic Executor** can handle **1 million concurrent agent interactions** with cryptographically verified evidence preservation. This guide explains how to run comprehensive load tests.

## Overview

The load testing suite validates:

- **Sequential Throughput**: Single-threaded baseline performance
- **Concurrent Throughput**: Multi-threaded realistic workload
- **Evidence Vault Scaling**: 1M cryptographic receipts with chain integrity
- **Tenant Isolation**: Cross-tenant boundary enforcement at scale
- **Memory Efficiency**: Sustainable operation without memory leaks
- **Latency Characteristics**: P50, P95, P99 performance under load

## Quick Start

### Run Standalone Load Test

```bash
cd ciaf_agents/examples
python load_test_runner.py --interactions 1000000 --workers 16 --output results.json
```

### Run with pytest

```bash
cd ciaf_agents
pytest tests/test_load_million_interactions.py -v -s
```

## Performance Benchmarks

Expected performance with 1 million interactions:

| Metric | Target | Notes |
|--------|--------|-------|
| **Throughput** | 5,000+ actions/sec | With 16 workers, concurrent |
| **P50 Latency** | <5ms | Single action median |
| **P95 Latency** | <20ms | 95th percentile |
| **P99 Latency** | <100ms | 99th percentile |
| **Success Rate** | ≥95% | Policy enforcement working |
| **Peak Memory** | <4GB | For 1M receipts in vault |

## Test Scenarios

### 1. Sequential Test (test_sequential_million_interactions)

Executes 1 million actions **sequentially** on a single thread.

**Tests:**
- Single-threaded baseline performance
- Memory accumulation over sustained load
- Policy evaluation stability

**Command:**
```bash
pytest tests/test_load_million_interactions.py::TestMillionAgentInteractions::test_sequential_million_interactions -v
```

**Expected Result:**
- ~1,000-2,000 actions/sec
- ~1-5ms average latency
- Linear memory growth

### 2. Concurrent Test (test_concurrent_agent_interactions)

Executes 1 million actions **concurrently** with 16 worker threads.

**Tests:**
- Multi-threaded throughput (5x+ improvement expected)
- Thread safety and race condition handling
- Evidence vault concurrent access
- Lock contention under high load

**Command:**
```bash
pytest tests/test_load_million_interactions.py::TestMillionAgentInteractions::test_concurrent_agent_interactions -v
```

**Expected Result:**
- ~5,000-10,000 actions/sec
- ~1-10ms average latency with 16 workers
- Sub-linear memory growth

### 3. Evidence Vault Test (test_evidence_vault_scaling)

Stores 1 million cryptographically signed receipts in evidence vault.

**Tests:**
- Receipt generation at scale
- Hash chain integrity
- Storage efficiency
- Vault query performance

**Command:**
```bash
pytest tests/test_load_million_interactions.py::TestMillionAgentInteractions::test_evidence_vault_scaling -v
```

**Expected Result:**
- All receipts successfully stored
- Evidence vault grows to ~500MB-2GB
- Hash chain validates
- No corruption on 1M receipts

### 4. Multi-Tenant Isolation Test (test_multi_tenant_isolation_at_scale)

Tests tenant boundary enforcement with 1 million concurrent actions.

**Tests:**
- Tenant isolation enforcement
- Cross-tenant access prevention
- Policy evaluation time under load
- No data leakage between tenants

**Command:**
```bash
pytest tests/test_load_million_interactions.py::TestMillionAgentInteractions::test_multi_tenant_isolation_at_scale -v
```

**Expected Result:**
- All actions respect tenant boundaries
- ≥95% success rate
- No cross-tenant violations

## Standalone Load Test Runner

The standalone runner provides independent testing without pytest.

### Basic Usage

```bash
python examples/load_test_runner.py
```

This runs all three tests (sequential, concurrent, evidence vault) with defaults:
- 1 million interactions
- 16 concurrent workers
- Saves results to `load_test_results.json`

### Custom Configuration

```bash
# Test with 100K interactions instead of 1M
python examples/load_test_runner.py --interactions 100000

# Use 32 concurrent workers
python examples/load_test_runner.py --workers 32 --interactions 1000000

# Custom output path
python examples/load_test_runner.py --output my_results.json

# All together
python examples/load_test_runner.py \
  --interactions 500000 \
  --workers 8 \
  --output results/production_test.json
```

### Output Format

The runner produces:
1. **Console Output**: Real-time progress and results
2. **JSON File**: Complete metrics for analysis

#### JSON Results Structure

```json
{
  "test_config": {
    "total_interactions": 1000000,
    "num_workers": 16,
    "timestamp": "2026-03-18T14:32:45.123456"
  },
  "tests": {
    "sequential": {
      "test_type": "sequential",
      "total_actions": 1000000,
      "success_count": 950000,
      "failure_count": 50000,
      "success_rate_percent": 95.0,
      "total_duration_seconds": 600.5,
      "throughput_actions_per_sec": 1664.72,
      "latency_stats": {
        "mean_ms": 0.65,
        "median_ms": 0.58,
        "stdev_ms": 2.34,
        "min_ms": 0.10,
        "max_ms": 125.34,
        "p50_ms": 0.58,
        "p95_ms": 5.67,
        "p99_ms": 15.89
      },
      "memory_stats": {
        "start_mb": 148.5,
        "peak_mb": 2456.3,
        "end_mb": 2340.1,
        "delta_mb": 2191.6
      }
    },
    "concurrent": { ... },
    "evidence_vault": { ... }
  }
}
```

## Test Infrastructure

### Agent Setup

The load tests create:
- **100 agent identities** spread across:
  - **4 tenants**: tenant-a, tenant-b, tenant-c, tenant-d
  - **4 departments**: engineering, finance, healthcare, operations
  - **25 agents per combination**: Total = 4 × 4 × 25 = 400 agents

Each agent has:
- Unique principal ID
- Role assignments: analyst, operator
- Tenant and department attributes
- Environment tags (production/staging)

### Policy Setup

The tests enforce:
- **Same-tenant-only** access for `read_data` actions
- **Same-department** restrictions for `modify_resource` actions
- Role-based permission checks

### Elevation Grants

25% of agents have active privilege elevation grants:
- Elevated permission: `approve_payment`
- Duration: 1 hour
- Purpose: Test PAM (Privileged Access Management) at scale

## Performance Tuning

### Machine Requirements

For 1 million interaction tests:
- **CPU**: 4+ cores recommended (16+ ideal)
- **RAM**: 8GB+ required (16GB+ recommended)
- **Storage**: 10GB+ free space for evidence vault
- **Disk**: SSD preferred for receipt storage

### Optimization Tips

1. **Reduce Interactions for Fast Feedback**
   ```bash
   python examples/load_test_runner.py --interactions 100000
   ```

2. **Scale Worker Count to CPU Cores**
   ```bash
   # For 8-core CPU
   python examples/load_test_runner.py --workers 8
   ```

3. **Monitor System Resources**
   ```bash
   # In separate terminal, monitor while test runs
   watch -n 1 "ps aux | grep load_test"
   ```

### Performance Analysis

#### Good Performance Indicators

- ✅ Throughput: 5,000+ actions/sec (concurrent)
- ✅ P95 Latency: <20ms
- ✅ P99 Latency: <100ms
- ✅ Success Rate: ≥95%
- ✅ Linear memory growth (no exponential increase)

#### Warning Signs

- ⚠️ Throughput degradation over time (memory leak)
- ⚠️ Success rate <90% (policy evaluation issues)
- ⚠️ Memory usage continues growing after test (not releasing)
- ⚠️ Latency spikes above 1000ms (GC pauses or lock contention)

## Debugging Failed Tests

### If Evidence Vault Test Fails

```python
# Check vault integrity
vault = config["vault"]
print(f"Total receipts: {len(vault.receipts)}")

# Verify chain continuity
for receipt in vault.receipts[-10:]:
    print(f"Receipt {receipt['receipt_id']}: prior_hash={receipt.get('prior_receipt_hash')}")
```

### If Success Rate is Low

```python
# Check which actions fail
policy_engine = config["policy_engine"]
agent = agents[0]

# Debug a specific action
action = ActionRequest(...)
decision = policy_engine.evaluate(agent, action)
print(f"Policy decision: {decision}")
```

### If Concurrent Test is Slower Than Sequential

This indicates lock contention. Possible causes:
- Evidence vault lock contention (too many threads)
- IAM store lock issues
- GC pressure from rapid object allocation

**Solution**: Reduce worker count or optimize storage (batch receipts)

## Examples

### Run Full Test Suite with Detailed Output

```bash
cd examples
python load_test_runner.py \
  --interactions 1000000 \
  --workers 16 \
  --output full_test_results.json

# Follow test progress
tail -f full_test_results.json
```

### Compare Different Configurations

```bash
# Baseline: default settings
python load_test_runner.py -i 100000 -o baseline.json

# High concurrency
python load_test_runner.py -i 100000 -w 32 -o high_concurrency.json

# Comparison
python -c "
import json
baseline = json.load(open('baseline.json'))
hc = json.load(open('high_concurrency.json'))
print(f\"Baseline throughput: {baseline['tests']['concurrent']['throughput_actions_per_sec']:.0f}/sec\")
print(f\"HC throughput: {hc['tests']['concurrent']['throughput_actions_per_sec']:.0f}/sec\")
"
```

### Profile with cProfile

```python
import cProfile
from examples.load_test_runner import LoadTestRunner

def run_profile():
    runner = LoadTestRunner(num_interactions=100000, num_workers=4)
    runner.run_sequential_test()

cProfile.run('run_profile()', sort='cumulative')
```

## Continuous Integration

Add to GitHub Actions workflow to test on every release:

```yaml
- name: Run Load Tests
  run: |
    cd ciaf_agents
    python examples/load_test_runner.py \
      --interactions 100000 \
      --workers $(nproc) \
      --output load_test_results.json
    
    # Verify minimum performance
    python -c "
    import json
    results = json.load(open('load_test_results.json'))
    throughput = results['tests']['concurrent']['throughput_actions_per_sec']
    assert throughput >= 5000, f'Throughput {throughput} below 5000 req/sec'
    "
```

## FAQ

**Q: Why is my throughput lower than expected?**  
A: Check system load, reduce worker count, or ensure SSD for evidence vault.

**Q: Can I test 10 million interactions?**  
A: Yes, but requires 32GB+ RAM and ~20GB storage. Start with 1M for baseline.

**Q: What if the concurrent test is slower than sequential?**  
A: Lock contention. Try reducing workers or profiling with cProfile.

**Q: How do I know if the evidence vault is working correctly?**  
A: Check vault results: all 1M receipts should be stored with valid hash chains.

---

**Last Updated**: March 18, 2026  
**Framework**: CIAF-LCM Agentic Executor  
**Repository**: https://github.com/DenzilGreenwood/ciaf_agents
