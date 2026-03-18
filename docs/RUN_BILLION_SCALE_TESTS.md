# Running Billion-Scale Load Tests for CIAF-LCM

## Quick Start

### 1. Small-Scale Test (Quick Validation - 5 minutes)
```bash
cd d:\Github\ciaf_agents\ciaf_agents
python -m pytest tests/test_load_million_interactions.py::TestMillionAgentInteractions::test_sequential_million_interactions -v
```
✅ **Result**: Validates load test infrastructure works

### 2. Medium-Scale Test (Scalability Validation - 30 minutes)
```bash
cd d:\Github\ciaf_agents\ciaf_agents
# Edit test to use 100_000_000 instead of 1_000_000
# OR use environment variable approach (see below)
python -m pytest tests/test_load_million_interactions.py -v -k "concurrent"
```

### 3. Full-Scale Test (Billion Scale - 10-50 hours)
```bash
cd d:\Github\ciaf_agents\ciaf_agents

# Duration estimate:
# - Current throughput: ~1,000-2,000 actions/sec (1M test)
# - 1 billion actions = 1,000,000,000 / 1,500 = 666,666 seconds
# - 666,666 seconds / 3600 = ~185 hours (~8 days!)

# For practical testing, scale appropriately:
CIAF_LOAD_TEST_SCALE=100M python -m pytest tests/test_load_million_interactions.py -v
```

## Environment Variable Configuration

### CIAF_LOAD_TEST_SCALE
Controls the number of actions executed.

**Supported Values:**
- `1M`, `10M`, `100M`, `1B` (examples)
- Or any number: `50M`, `500M`, `2B`
- Format: `<number><K|M|B>` (case-insensitive)

**Example:**
```bash
# Test with 500 million actions
set CIAF_LOAD_TEST_SCALE=500M
python -m pytest tests/test_load_million_interactions.py::TestMillionAgentInteractions::test_concurrent_agent_interactions -v

# On Linux/macOS:
export CIAF_LOAD_TEST_SCALE=500M
pytest tests/test_load_million_interactions.py -v
```

### CIAF_LOAD_TEST_WORKERS  
Number of concurrent worker threads.

**Example:**
```bash
# Use 8 workers instead of default 16
set CIAF_LOAD_TEST_WORKERS=8
python -m pytest tests/test_load_million_interactions.py -v
```

### CIAF_LOAD_TEST_CHECKPOINT
Checkpoint interval for progress reporting.

**Example:**
```bash
# Report progress every 50M actions
set CIAF_LOAD_TEST_CHECKPOINT=50M
python -m pytest tests/test_load_million_interactions.py -v
```

## Expected Runtimes

Based on ~1,500-2,000 actions/second throughput:

| Scale | Throughput | Duration |
|-------|-----------|----------|
| 1M | 1,500-2,000/sec | ~10 seconds |
| 10M | 1,500-2,000/sec | ~2 minutes |
| 100M | 1,500-2,000/sec | ~20 minutes |
| 500M | 1,500-2,000/sec | ~80 minutes |
| 1B | 1,500-2,000/sec | ~160 minutes (2.5 hours) |

*Note: Actual times will vary based on hardware, policy complexity, and concurrent load.*

## Interpreting Results

### Success Metrics
- ✅ All actions completed
- ✅ Success rate ≥ 80% (some policy blocks expected)
- ✅ Throughput ≥ 1,000 actions/sec
- ✅ P95 latency < 50ms
- ✅ Memory growth is linear

### Memory Analysis
```
Memory Cost = (Peak Memory - Start Memory) / Total Actions

Good Performance: < 1.0 KB per action
Acceptable: < 5.0 KB per action
Needs Optimization: > 5.0 KB per action
```

### Latency Analysis
```
Latency Percentiles (milliseconds):
- Mean: X.X ms
- P50 (Median): X.X ms  
- P95: < 50ms (↓ good)
- P99: < 100ms (↓ good)
```

## Troubleshooting

### Test Hangs or Takes Too Long
1. **Reduce Scale**: Start with 10M instead of 1B
   ```bash
   set CIAF_LOAD_TEST_SCALE=10M
   ```
2. **Reduce Workers**: Less contention may improve throughput
   ```bash
   set CIAF_LOAD_TEST_WORKERS=4
   ```

### Memory Usage Exceeds Available RAM
Evidence vault stores all receipts. For billion-scale:
- 1B actions × 650 bytes = ~650 GB storage
- Peak memory might hit limits

**Solution**: Run on a machine with sufficient RAM or test smaller scale:
```bash
set CIAF_LOAD_TEST_SCALE=100M  # ~65 GB vault
```

### Throughput Degradation Over Time
If you see latency increasing:
1. **Check System**: Disk I/O, CPU, network congestion
2. **Enable Memory Profiling**: GC pauses may degrade latency
3. **Profile with**: `python -m cProfile -s cumtime test_runner.py`

### Out of Memory Errors
1. Increase available memory
2. Reduce scale or worker count
3. Implement vault rotation (save/archive receipts)

## Advanced: Custom Test Scales

For precise testing at specific scales:

### Edit Test File
```python
# tests/test_load_million_interactions.py, line ~345
num_actions = 250_000_000  # Custom: 250M actions
```

### Run with Custom Configuration
```python
import os
os.environ['CIAF_LOAD_TEST_SCALE'] = '250M'

# Then run:
python -m pytest tests/test_load_million_interactions.py -v
```

## Generating Reports

After running tests, metrics are printed to console:

```
================================================================================
LOAD TEST RESULTS
================================================================================
Total Actions:           100,000,000
Successful:              95,000,000 (95.00%)
Failed:                  5,000,000
Total Duration:          55234.12s (15.34h)

Throughput Analysis:
  Average Throughput:      1,809 actions/sec

Latency Analysis (milliseconds):
  Mean:                    5.123ms
  P50 (Median):            3.456ms
  P95:                     18.234ms
  P99:                     45.678ms
  P99.9:                   89.012ms

Memory Analysis:
  Start:                   156.2MB
  Peak:                    4523.1MB
  End:                     4123.5MB
  Memory Cost per Action:  0.0422KB
  Memory Growth:           3966.9MB
================================================================================
```

### Export to File
```bash
python -m pytest tests/test_load_million_interactions.py -v -s > results.txt 2>&1
```

### Parse Results with Python
```python
# TODO: Add JSON export format for automated parsing
```

## Continuous Monitoring

For production deployments, monitor at scale:

```python
from ciaf_agents.execution import ToolExecutor

executor = ToolExecutor(...)

# After 1M actions - check metrics
if executor.action_count % 1_000_000 == 0:
    print(f"Progress: {executor.action_count:,} actions")
    print(f"Throughput: {executor.get_throughput():.0f} actions/sec")
    print(f"Memory: {executor.get_memory_usage_mb():.1f} MB")
```

## Related Documentation

- [SCALABILITY_ASSESSMENT.md](SCALABILITY_ASSESSMENT.md) - Full assessment methodology
- [LOAD_TESTING_GUIDE.md](LOAD_TESTING_GUIDE.md) - Detailed testing procedures
- [API_REFERENCE.md](API_REFERENCE.md) - CIAF-LCM API documentation

## Questions or Issues?

1. Check test output for detailed error messages
2. Reduce scale and re-run to isolate issues
3. Review framework logs: `ciaf_agents/*.log`
4. Check memory/disk availability: `systeminfo` (Windows) or `free -h` (Linux)

---

**Test Infrastructure**: CIAF-LCM Load Test Framework v1.0
**Framework**: CIAF-LCM v1.0
**Supported Scales**: 1K to 1B+ actions
**Minimum RAM for 1B Scale**: 700GB (vault storage)
