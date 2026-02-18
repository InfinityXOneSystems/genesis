"""Command-line interface for Genesis"""

import asyncio
import argparse
from pathlib import Path
from genesis.core import Orchestrator, AutonomousLoop
from genesis.analysis import RepositoryScanner
from genesis.benchmarking import BenchmarkSystem
from genesis.utils import setup_logging


def main() -> None:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Genesis - Autonomous AI Engineering System"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a full autonomous cycle")
    run_parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to repository (default: current directory)",
    )
    run_parser.add_argument(
        "--output-dir",
        default="./output",
        help="Output directory for reports",
    )
    
    # Loop command
    loop_parser = subparsers.add_parser("loop", help="Run the autonomous improvement loop")
    loop_parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to repository",
    )
    loop_parser.add_argument(
        "--threshold",
        type=float,
        default=1.2,
        help="Target threshold (default: 1.2 = 20%% improvement)",
    )
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan repository")
    scan_parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to repository",
    )
    scan_parser.add_argument(
        "--output",
        default="./analysis/global_analysis.json",
        help="Output file path",
    )
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmarks")
    benchmark_parser.add_argument(
        "--output",
        default="./benchmarks/results.json",
        help="Output file path",
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "loop":
        asyncio.run(cmd_loop(args))
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    else:
        parser.print_help()


async def cmd_run(args: argparse.Namespace) -> None:
    """Run a full autonomous cycle"""
    logger = setup_logging()
    logger.info("Starting Genesis autonomous cycle")
    
    orchestrator = Orchestrator(
        repository_path=args.repo_path,
        output_dir=Path(args.output_dir),
    )
    
    results = await orchestrator.run_full_cycle()
    
    print("\n=== Cycle Complete ===")
    for phase, result in results.items():
        status = result.get("status", "unknown")
        print(f"{phase}: {status}")
    
    print(f"\nResults saved to {args.output_dir}")


async def cmd_loop(args: argparse.Namespace) -> None:
    """Run the autonomous improvement loop"""
    logger = setup_logging()
    logger.info("Starting Genesis autonomous loop")
    
    loop = AutonomousLoop(
        repository_path=args.repo_path,
        target_threshold=args.threshold,
    )
    
    result = await loop.run()
    
    print("\n=== Loop Complete ===")
    print(f"Iterations: {result['iterations']}")
    print(f"Final Score: {result['final_score']:.2f}")
    print(f"Target: {result['target_threshold']}")
    print(f"Threshold Met: {result['threshold_met']}")


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan repository"""
    logger = setup_logging()
    logger.info("Scanning repository")
    
    scanner = RepositoryScanner()
    repo_info = scanner.scan_repository(args.repo_path)
    
    analysis = scanner.generate_global_analysis(
        [repo_info],
        output_path=Path(args.output),
    )
    
    print("\n=== Repository Analysis ===")
    print(f"Repository: {repo_info.name}")
    print(f"Language: {repo_info.language}")
    print(f"Files: {repo_info.files_count}")
    print(f"Lines of Code: {repo_info.lines_of_code}")
    print(f"Has Tests: {repo_info.has_tests}")
    print(f"Has CI/CD: {repo_info.has_ci}")
    print(f"Has Docs: {repo_info.has_docs}")
    print(f"\nFull analysis saved to {args.output}")


def cmd_benchmark(args: argparse.Namespace) -> None:
    """Run benchmarks"""
    logger = setup_logging()
    logger.info("Running benchmarks")
    
    benchmark_system = BenchmarkSystem()
    results = benchmark_system.run_benchmarks(output_path=Path(args.output))
    
    # Generate and print report
    report = benchmark_system.generate_report(results)
    print(report)
    
    print(f"\nFull results saved to {args.output}")


if __name__ == "__main__":
    main()
