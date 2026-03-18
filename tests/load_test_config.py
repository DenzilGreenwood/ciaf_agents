"""
Load Test Configuration - Allows flexible scaling without code changes

Environment Variables:
  CIAF_LOAD_TEST_SCALE: "1M", "10M", "100M", "1B" (default: uses code value)
  CIAF_LOAD_TEST_DURATION_HOURS: Max duration before stopping (default: unlimited)
  CIAF_LOAD_TEST_WORKERS: Number of concurrent workers (default: 16)
  CIAF_LOAD_TEST_SAMPLE_RATE: Latency sampling rate 0.0-1.0 (default: 0.001)
"""

import os
from typing import Dict, Any

def parse_scale(scale_str: str) -> int:
    """Parse scale string to action count
    
    Examples:
        "1M" -> 1_000_000
        "100M" -> 100_000_000
        "1B" -> 1_000_000_000
    """
    scale_str = scale_str.upper().strip()
    multipliers = {
        'K': 1_000,
        'M': 1_000_000,
        'B': 1_000_000_000,
        'T': 1_000_000_000_000,
    }
    
    for suffix, multiplier in multipliers.items():
        if scale_str.endswith(suffix):
            try:
                number = float(scale_str[:-1])
                return int(number * multiplier)
            except ValueError:
                raise ValueError(f"Invalid scale format: {scale_str}")
    
    # Try direct integer
    try:
        return int(scale_str)
    except ValueError:
        raise ValueError(f"Invalid scale format: {scale_str}")


class LoadTestConfig:
    """Load test configuration with environment variable overrides"""
    
    # Defaults
    SCALE_ACTIONS = 1_000_000_000  # 1 billion
    NUM_WORKERS = 16
    CHECKPOINT_INTERVAL = 100_000_000  # 100M
    SAMPLE_INTERVAL = 100_000  # 100K
    SAMPLE_RATE = 0.001  # 0.1% of actions
    MAX_DURATION_HOURS = None  # Unlimited
    ENABLE_GC_TRACKING = True
    ENABLE_MEMORY_PROFILING = True
    
    @classmethod
    def from_environment(cls) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {
            'scale_actions': cls.SCALE_ACTIONS,
            'num_workers': cls.NUM_WORKERS,
            'checkpoint_interval': cls.CHECKPOINT_INTERVAL,
            'sample_interval': cls.SAMPLE_INTERVAL,
            'sample_rate': cls.SAMPLE_RATE,
            'max_duration_hours': cls.MAX_DURATION_HOURS,
            'enable_gc_tracking': cls.ENABLE_GC_TRACKING,
            'enable_memory_profiling': cls.ENABLE_MEMORY_PROFILING,
        }
        
        # Override from environment
        if 'CIAF_LOAD_TEST_SCALE' in os.environ:
            scale_str = os.environ['CIAF_LOAD_TEST_SCALE']
            config['scale_actions'] = parse_scale(scale_str)
            print(f"📊 Load test scale: {scale_str} ({config['scale_actions']:,} actions)")
        
        if 'CIAF_LOAD_TEST_WORKERS' in os.environ:
            config['num_workers'] = int(os.environ['CIAF_LOAD_TEST_WORKERS'])
            print(f"👥 Load test workers: {config['num_workers']}")
        
        if 'CIAF_LOAD_TEST_CHECKPOINT' in os.environ:
            checkpoint_str = os.environ['CIAF_LOAD_TEST_CHECKPOINT']
            config['checkpoint_interval'] = parse_scale(checkpoint_str)
            print(f"🏁 Checkpoint interval: {checkpoint_str}")
        
        if 'CIAF_LOAD_TEST_SAMPLE' in os.environ:
            sample_str = os.environ['CIAF_LOAD_TEST_SAMPLE']
            config['sample_interval'] = parse_scale(sample_str)
            print(f"🎯 Sample interval: {sample_str}")
        
        if 'CIAF_LOAD_TEST_DURATION_HOURS' in os.environ:
            config['max_duration_hours'] = float(os.environ['CIAF_LOAD_TEST_DURATION_HOURS'])
            print(f"⏱️  Max duration: {config['max_duration_hours']} hours")
        
        if 'CIAF_LOAD_TEST_SAMPLE_RATE' in os.environ:
            config['sample_rate'] = float(os.environ['CIAF_LOAD_TEST_SAMPLE_RATE'])
            print(f"📈 Latency sample rate: {config['sample_rate']*100:.2f}%")
        
        return config
    
    @classmethod
    def for_quick_test(cls) -> Dict[str, Any]:
        """Quick test configuration (10M actions, 2 workers)"""
        return {
            'scale_actions': 10_000_000,
            'num_workers': 2,
            'checkpoint_interval': 5_000_000,
            'sample_interval': 100_000,
            'sample_rate': 0.01,
            'max_duration_hours': 0.5,
            'enable_gc_tracking': True,
            'enable_memory_profiling': True,
        }
    
    @classmethod
    def for_medium_test(cls) -> Dict[str, Any]:
        """Medium test configuration (100M actions, 8 workers)"""
        return {
            'scale_actions': 100_000_000,
            'num_workers': 8,
            'checkpoint_interval': 25_000_000,
            'sample_interval': 100_000,
            'sample_rate': 0.001,
            'max_duration_hours': 2.0,
            'enable_gc_tracking': True,
            'enable_memory_profiling': True,
        }
    
    @classmethod
    def for_full_scale(cls) -> Dict[str, Any]:
        """Full scale test configuration (1B actions, 16 workers)"""
        return {
            'scale_actions': 1_000_000_000,
            'num_workers': 16,
            'checkpoint_interval': 100_000_000,
            'sample_interval': 100_000,
            'sample_rate': 0.001,
            'max_duration_hours': None,
            'enable_gc_tracking': True,
            'enable_memory_profiling': True,
        }


# Pre-defined test scenarios
TEST_SCENARIOS = {
    'quick': {
        'name': '⚡ Quick Test',
        'description': 'Fast validation (10M actions, ~1-5 minutes)',
        'actions': 10_000_000,
        'workers': 2,
    },
    'medium': {
        'name': '📊 Medium Test',
        'description': 'Good scalability validation (100M actions, ~30 minutes)',
        'actions': 100_000_000,
        'workers': 8,
    },
    'large': {
        'name': '🔥 Large Test',
        'description': 'Production-scale validation (500M actions, ~2 hours)',
        'actions': 500_000_000,
        'workers': 16,
    },
    'billion': {
        'name': '🌍 Billion Scale',
        'description': 'Ultimate scale test (1B actions, 10-50 hours)',
        'actions': 1_000_000_000,
        'workers': 16,
    },
}


def print_test_scenarios():
    """Print available test scenarios"""
    print("\n" + "="*70)
    print("CIAF-LCM Load Test Scenarios")
    print("="*70)
    for key, scenario in TEST_SCENARIOS.items():
        print(f"\n{scenario['name']}")
        print(f"  Key: {key}")
        print(f"  {scenario['description']}")
    print("\n" + "="*70)


def get_test_scenario(key: str) -> Dict[str, Any]:
    """Get test scenario configuration
    
    Args:
        key: 'quick', 'medium', 'large', or 'billion'
    
    Returns:
        Configuration dictionary
    """
    if key not in TEST_SCENARIOS:
        print(f"⚠️  Unknown scenario: {key}")
        print_test_scenarios()
        raise ValueError(f"Unknown test scenario: {key}")
    
    scenario = TEST_SCENARIOS[key]
    return {
        'scale_actions': scenario['actions'],
        'num_workers': scenario['workers'],
        'checkpoint_interval': min(100_000_000, scenario['actions'] // 10),
        'sample_interval': 100_000,
        'sample_rate': 0.001,
        'max_duration_hours': None,
        'enable_gc_tracking': True,
        'enable_memory_profiling': True,
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'scenarios':
            print_test_scenarios()
        elif sys.argv[1] == 'quick':
            config = LoadTestConfig.for_quick_test()
            print(f"\n✅ Quick test config: {config['scale_actions']:,} actions")
        elif sys.argv[1] == 'medium':
            config = LoadTestConfig.for_medium_test()
            print(f"\n✅ Medium test config: {config['scale_actions']:,} actions")
        elif sys.argv[1] == 'full':
            config = LoadTestConfig.for_full_scale()
            print(f"\n✅ Full scale config: {config['scale_actions']:,} actions")
        else:
            config = LoadTestConfig.from_environment()
            print(f"\n✅ Environment config loaded")
    else:
        print("Usage: python load_test_config.py [scenarios|quick|medium|full]")
        print("Or set environment variables: CIAF_LOAD_TEST_SCALE, CIAF_LOAD_TEST_WORKERS, etc.")
