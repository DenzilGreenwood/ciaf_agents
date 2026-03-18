#!/usr/bin/env python3
"""
Standalone Load Test Runner for CIAF-LCM Million Agent Interactions

Usage:
    python load_test_runner.py --interactions 1000000 --workers 16 --output report.json
"""

import argparse
import json
import time
import statistics
import gc
import psutil
import sys
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ciaf_agents.core import Identity, Resource, Permission, RoleDefinition, ActionRequest
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine, any_condition
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


class LoadTestRunner:
    """Run comprehensive load tests"""
    
    def __init__(self, num_interactions: int = 1_000_000, num_workers: int = 16):
        self.num_interactions = num_interactions
        self.num_workers = num_workers
        self.results = {
            "test_config": {
                "total_interactions": num_interactions,
                "num_workers": num_workers,
                "timestamp": datetime.now().isoformat(),
            },
            "tests": {}
        }
        self._setup_infrastructure()
    
    def _setup_infrastructure(self):
        """Initialize CIAF-LCM components"""
        print("Setting up CIAF-LCM infrastructure...")
        
        self.iam_store = IAMStore()
        self.pam_store = PAMStore()
        self.vault = EvidenceVault(signing_secret="load-test-vault-secret")
        
        # Create agents
        tenants = ["tenant-a", "tenant-b", "tenant-c", "tenant-d"]
        departments = ["engineering", "finance", "healthcare", "operations"]
        
        self.agents = []
        for tenant in tenants:
            for dept in departments:
                for i in range(25):
                    agent = Identity(
                        principal_id=f"agent-{tenant}-{dept}-{i:03d}",
                        principal_type="agent",
                        display_name=f"Agent {tenant}/{dept}/{i}",
                        roles={"analyst", "operator"},
                        attributes={
                            "tenant": tenant,
                            "department": dept,
                            "environment": "production" if i % 3 == 0 else "staging",
                        }
                    )
                    self.agents.append(agent)
                    self.iam_store.add_identity(agent)
        
        # Define roles
        analyst_role = RoleDefinition(
            name="analyst",
            permissions=[
                Permission("read_data", "database", any_condition),
                Permission("list_resources", "api", any_condition),
            ]
        )
        
        operator_role = RoleDefinition(
            name="operator",
            permissions=[
                Permission("execute_action", "compute", any_condition),
                Permission("modify_resource", "config", any_condition),
            ]
        )
        
        self.iam_store.add_role(analyst_role)
        self.iam_store.add_role(operator_role)
        
        # Set up privilege grants
        for agent in self.agents[::4]:
            self.pam_store.issue_grant(
                principal_id=agent.principal_id,
                allowed_actions={"approve_payment"},
                resource_types={"payment"},
                reason="Load testing",
                approved_by="manager@cognitiveinsight.ai",
                duration_minutes=60,
                ticket_id=f"LOADTEST-{agent.principal_id}"
            )
        
        # Create policy engine and executor
        self.policy_engine = PolicyEngine(self.iam_store, self.pam_store)
        self.executor = ToolExecutor(self.policy_engine, self.vault, self.pam_store)
        
        print(f"✓ Created {len(self.agents)} agents across 16 combinations")
        print(f"✓ CIAF-LCM infrastructure ready\n")
    
    def _execute_action(self, action_num: int) -> Dict[str, Any]:
        """Execute single action and return metrics"""
        agent = self.agents[action_num % len(self.agents)]
        action_type = ["read_data", "execute_action", "list_resources", "modify_resource"][action_num % 4]
        resource_type = ["database", "compute", "api", "config"][action_num % 4]
        
        resource = Resource(
            resource_id=f"resource-{action_num % 10000}",
            resource_type=resource_type,
            owner_tenant=agent.attributes.get("tenant", "default"),
            attributes={"target": f"target-{action_num % 100}"}
        )
        
        action = ActionRequest(
            action=action_type,
            resource=resource,
            params={"target": f"target-{action_num % 100}"},
            justification=f"Load test {action_num}",
            requested_by=agent,
            correlation_id=f"load-test-{action_num:08d}"
        )
        
        start = time.perf_counter()
        try:
            result = self.executor.execute(action)
            duration = time.perf_counter() - start
            success = result.get("status") == "ok"
        except Exception as e:
            duration = time.perf_counter() - start
            success = False
        
        return {
            "action_num": action_num,
            "success": success,
            "duration_ms": duration * 1000,
        }
    
    def run_sequential_test(self) -> Dict[str, Any]:
        """Run sequential interactions test"""
        print(f"Running sequential test: {self.num_interactions:,} interactions...")
        print("-" * 70)
        
        metrics = {
            "test_type": "sequential",
            "total_actions": self.num_interactions,
            "success_count": 0,
            "failure_count": 0,
            "action_times_ms": [],
        }
        
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss
        peak_memory = start_memory
        
        for i in range(self.num_interactions):
            result = self._execute_action(i)
            metrics["action_times_ms"].append(result["duration_ms"])
            
            if result["success"]:
                metrics["success_count"] += 1
            else:
                metrics["failure_count"] += 1
            
            if i % 50000 == 0 and i > 0:
                current_memory = psutil.Process().memory_info().rss
                peak_memory = max(peak_memory, current_memory)
                elapsed = time.perf_counter() - start_time
                throughput = i / elapsed
                print(f"  Progress: {i:,} actions | {throughput:.0f} actions/sec")
        
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss
        peak_memory = max(peak_memory, end_memory)
        
        # Calculate statistics
        total_duration = end_time - start_time
        metrics["total_duration_seconds"] = total_duration
        metrics["throughput_actions_per_sec"] = self.num_interactions / total_duration
        metrics["success_rate_percent"] = (metrics["success_count"] / self.num_interactions) * 100
        
        # Latency percentiles
        sorted_times = sorted(metrics["action_times_ms"])
        metrics["latency_stats"] = {
            "mean_ms": statistics.mean(metrics["action_times_ms"]),
            "median_ms": statistics.median(metrics["action_times_ms"]),
            "stdev_ms": statistics.stdev(metrics["action_times_ms"]) if len(metrics["action_times_ms"]) > 1 else 0,
            "min_ms": min(metrics["action_times_ms"]),
            "max_ms": max(metrics["action_times_ms"]),
            "p50_ms": sorted_times[int(len(sorted_times) * 0.50)],
            "p95_ms": sorted_times[int(len(sorted_times) * 0.95)],
            "p99_ms": sorted_times[int(len(sorted_times) * 0.99)],
        }
        
        # Memory metrics
        metrics["memory_stats"] = {
            "start_mb": start_memory / 1024 / 1024,
            "peak_mb": peak_memory / 1024 / 1024,
            "end_mb": end_memory / 1024 / 1024,
            "delta_mb": (end_memory - start_memory) / 1024 / 1024,
        }
        
        # Remove action_times list from results for cleaner output
        del metrics["action_times_ms"]
        
        self._print_test_summary("SEQUENTIAL TEST", metrics)
        return metrics
    
    def run_concurrent_test(self) -> Dict[str, Any]:
        """Run concurrent interactions test"""
        print(f"\nRunning concurrent test: {self.num_interactions:,} interactions with {self.num_workers} workers...")
        print("-" * 70)
        
        metrics = {
            "test_type": "concurrent",
            "total_actions": self.num_interactions,
            "num_workers": self.num_workers,
            "success_count": 0,
            "failure_count": 0,
            "action_times_ms": [],
        }
        
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss
        peak_memory = start_memory
        completed = 0
        
        actions_per_worker = self.num_interactions // self.num_workers
        
        def worker_thread(worker_id: int):
            """Worker thread"""
            worker_results = []
            start_idx = worker_id * actions_per_worker
            end_idx = start_idx + actions_per_worker
            
            for i in range(start_idx, min(end_idx, self.num_interactions)):
                result = self._execute_action(i)
                worker_results.append(result)
            
            return worker_results
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(worker_thread, i): i for i in range(self.num_workers)}
            
            for future in as_completed(futures):
                worker_results = future.result()
                for result in worker_results:
                    metrics["action_times_ms"].append(result["duration_ms"])
                    if result["success"]:
                        metrics["success_count"] += 1
                    else:
                        metrics["failure_count"] += 1
                    completed += 1
                
                current_memory = psutil.Process().memory_info().rss
                peak_memory = max(peak_memory, current_memory)
                
                elapsed = time.perf_counter() - start_time
                throughput = completed / elapsed
                print(f"  Completed: {completed:,} | {throughput:.0f} actions/sec")
        
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss
        peak_memory = max(peak_memory, end_memory)
        
        # Calculate statistics
        total_duration = end_time - start_time
        metrics["total_duration_seconds"] = total_duration
        metrics["throughput_actions_per_sec"] = self.num_interactions / total_duration
        metrics["success_rate_percent"] = (metrics["success_count"] / self.num_interactions) * 100
        
        # Latency percentiles
        sorted_times = sorted(metrics["action_times_ms"])
        metrics["latency_stats"] = {
            "mean_ms": statistics.mean(metrics["action_times_ms"]),
            "median_ms": statistics.median(metrics["action_times_ms"]),
            "stdev_ms": statistics.stdev(metrics["action_times_ms"]) if len(metrics["action_times_ms"]) > 1 else 0,
            "min_ms": min(metrics["action_times_ms"]),
            "max_ms": max(metrics["action_times_ms"]),
            "p50_ms": sorted_times[int(len(sorted_times) * 0.50)],
            "p95_ms": sorted_times[int(len(sorted_times) * 0.95)],
            "p99_ms": sorted_times[int(len(sorted_times) * 0.99)],
        }
        
        # Memory metrics
        metrics["memory_stats"] = {
            "start_mb": start_memory / 1024 / 1024,
            "peak_mb": peak_memory / 1024 / 1024,
            "end_mb": end_memory / 1024 / 1024,
            "delta_mb": (end_memory - start_memory) / 1024 / 1024,
        }
        
        # Remove action_times list
        del metrics["action_times_ms"]
        
        self._print_test_summary("CONCURRENT TEST", metrics)
        return metrics
    
    def run_evidence_vault_test(self) -> Dict[str, Any]:
        """Test evidence vault at scale"""
        print(f"\nRunning evidence vault test: {self.num_interactions:,} receipts...")
        print("-" * 70)
        
        metrics = {
            "test_type": "evidence_vault",
            "total_receipts": self.num_interactions,
            "success_count": 0,
            "failure_count": 0,
            "action_times_ms": [],
        }
        
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss
        peak_memory = start_memory
        
        for i in range(self.num_interactions):
            result = self._execute_action(i)
            metrics["action_times_ms"].append(result["duration_ms"])
            
            if result["success"]:
                metrics["success_count"] += 1
            else:
                metrics["failure_count"] += 1
            
            if i % 50000 == 0 and i > 0:
                current_memory = psutil.Process().memory_info().rss
                peak_memory = max(peak_memory, current_memory)
                print(f"  Progress: {i:,} receipts")
        
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss
        peak_memory = max(peak_memory, end_memory)
        
        # Vault stats
        metrics["vault_stats"] = {
            "total_receipts_stored": len(self.vault.receipts),
            "estimated_storage_mb": self.vault.estimate_storage_size() / 1024 / 1024,
        }
        
        # Calculate statistics
        total_duration = end_time - start_time
        metrics["total_duration_seconds"] = total_duration
        metrics["throughput_actions_per_sec"] = self.num_interactions / total_duration
        metrics["success_rate_percent"] = (metrics["success_count"] / self.num_interactions) * 100
        
        # Latency percentiles
        sorted_times = sorted(metrics["action_times_ms"])
        metrics["latency_stats"] = {
            "mean_ms": statistics.mean(metrics["action_times_ms"]),
            "median_ms": statistics.median(metrics["action_times_ms"]),
            "p95_ms": sorted_times[int(len(sorted_times) * 0.95)],
            "p99_ms": sorted_times[int(len(sorted_times) * 0.99)],
        }
        
        # Memory metrics
        metrics["memory_stats"] = {
            "start_mb": start_memory / 1024 / 1024,
            "peak_mb": peak_memory / 1024 / 1024,
            "end_mb": end_memory / 1024 / 1024,
            "delta_mb": (end_memory - start_memory) / 1024 / 1024,
        }
        
        del metrics["action_times_ms"]
        
        self._print_test_summary("EVIDENCE VAULT TEST", metrics)
        return metrics
    
    def _print_test_summary(self, test_name: str, metrics: Dict[str, Any]):
        """Print formatted test summary"""
        print("\n" + "="*70)
        print(f"{test_name} RESULTS")
        print("="*70)
        print(f"Total Actions:              {metrics.get('total_actions', metrics.get('total_receipts', 0)):,}")
        print(f"Successful:                 {metrics['success_count']:,}")
        print(f"Failed:                     {metrics['failure_count']:,}")
        print(f"Success Rate:               {metrics['success_rate_percent']:.2f}%")
        print(f"Total Duration:             {metrics['total_duration_seconds']:.2f}s")
        print(f"Throughput:                 {metrics['throughput_actions_per_sec']:.0f} actions/sec")
        
        latency = metrics.get("latency_stats", {})
        print(f"\nLatency (ms):")
        print(f"  Mean:                     {latency.get('mean_ms', 0):.2f}")
        print(f"  Median:                   {latency.get('median_ms', 0):.2f}")
        print(f"  P95:                      {latency.get('p95_ms', 0):.2f}")
        print(f"  P99:                      {latency.get('p99_ms', 0):.2f}")
        
        memory = metrics.get("memory_stats", {})
        print(f"\nMemory (MB):")
        print(f"  Start:                    {memory.get('start_mb', 0):.1f}")
        print(f"  Peak:                     {memory.get('peak_mb', 0):.1f}")
        print(f"  End:                      {memory.get('end_mb', 0):.1f}")
        print(f"  Delta:                    {memory.get('delta_mb', 0):+.1f}")
        
        if "vault_stats" in metrics:
            vault = metrics["vault_stats"]
            print(f"\nVault:")
            print(f"  Receipts Stored:          {vault['total_receipts_stored']:,}")
            print(f"  Estimated Size:           {vault['estimated_storage_mb']:.1f} MB")
        
        print("="*70)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests"""
        gc.collect()
        
        self.results["tests"]["sequential"] = self.run_sequential_test()
        gc.collect()
        
        self.results["tests"]["concurrent"] = self.run_concurrent_test()
        gc.collect()
        
        self.results["tests"]["evidence_vault"] = self.run_evidence_vault_test()
        
        return self.results
    
    def save_results(self, output_path: str):
        """Save results to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✓ Results saved to {output_file}")
    
    def print_summary(self):
        """Print overall summary"""
        print("\n" + "="*70)
        print("LOAD TEST SUMMARY")
        print("="*70)
        
        for test_name, test_results in self.results["tests"].items():
            throughput = test_results.get("throughput_actions_per_sec", 0)
            latency = test_results.get("latency_stats", {}).get("p95_ms", 0)
            success_rate = test_results.get("success_rate_percent", 0)
            memory = test_results.get("memory_stats", {}).get("peak_mb", 0)
            
            print(f"\n{test_name.upper()}:")
            print(f"  Throughput:  {throughput:>10.0f} actions/sec")
            print(f"  P95 Latency: {latency:>10.2f}ms")
            print(f"  Success:     {success_rate:>10.2f}%")
            print(f"  Peak Memory: {memory:>10.1f}MB")
        
        print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Load test CIAF-LCM with million agent interactions"
    )
    parser.add_argument(
        "--interactions", "-i",
        type=int,
        default=1_000_000,
        help="Number of interactions to test (default: 1,000,000)"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=16,
        help="Number of concurrent workers (default: 16)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="load_test_results.json",
        help="Output file for results (default: load_test_results.json)"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print("CIAF-LCM Load Test: Million Agent Interactions")
    print(f"{'='*70}")
    print(f"Interactions:  {args.interactions:,}")
    print(f"Workers:       {args.workers}")
    print(f"Output:        {args.output}")
    print(f"{'='*70}\n")
    
    runner = LoadTestRunner(
        num_interactions=args.interactions,
        num_workers=args.workers
    )
    
    try:
        runner.run_all_tests()
        runner.print_summary()
        runner.save_results(args.output)
        print("\n✓ Load test completed successfully!")
    except KeyboardInterrupt:
        print("\n\n✗ Load test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Load test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
