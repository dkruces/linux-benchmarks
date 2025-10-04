#!/usr/bin/env python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "matplotlib",
#     "numpy",
# ]
# ///

"""Generate comprehensive benchmark reports consolidating all analysis results."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"


def ensure_analysis_files(result_dir: Path, scripts_dir: Path) -> Dict[str, bool]:
    """Ensure advanced statistics and progression plot files exist."""
    json_file = result_dir / "benchmark.json"
    stats_file = result_dir / "advanced_statistics.log"
    plot_file = result_dir / "progression.png"
    
    results = {"json": json_file.exists(), "stats": False, "plot": False}
    
    if not json_file.exists():
        return results
    
    # Generate advanced statistics if missing
    if not stats_file.exists():
        stats_script = scripts_dir / "advanced_statistics.py"
        if stats_script.exists():
            success, output = run_command(
                ["uv", "run", str(stats_script.absolute()), str(json_file.absolute())], 
                cwd=result_dir
            )
            if success:
                with open(stats_file, 'w') as f:
                    f.write(output)
                results["stats"] = True
            else:
                print(f"Warning: Failed to generate statistics for {result_dir}: {output}")
    else:
        results["stats"] = True
    
    # Generate progression plot if missing
    if not plot_file.exists():
        plot_script = scripts_dir / "plot_progression.py"
        if plot_script.exists():
            success, _ = run_command([
                "uv", "run", str(plot_script.absolute()), 
                str(json_file.absolute()), 
                "--output", str(plot_file.absolute())
            ], cwd=result_dir)
            if success:
                results["plot"] = True
            else:
                print(f"Warning: Failed to generate plot for {result_dir}")
    else:
        results["plot"] = True
    
    return results


def load_json_data(json_file: Path) -> Optional[dict]:
    """Load benchmark JSON data."""
    try:
        with open(json_file) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to load {json_file}: {e}")
        return None


def load_text_file(file_path: Path) -> str:
    """Load text file content."""
    try:
        with open(file_path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def format_benchmark_summary(data: dict) -> str:
    """Format benchmark results summary table."""
    if not data or "results" not in data:
        return ""
    
    results = data["results"]
    if not results:
        return ""
    
    # Create summary table
    lines = ["| Command | Mean (s) | Std Dev (s) | Min (s) | Max (s) | Runs |",
             "|---------|----------|-------------|---------|---------|------|"]
    
    for result in results:
        cmd = result.get("command", "").replace("make LLVM=1 -j", "make -j").replace("make  -j", "make -j")
        mean = result.get("mean", 0) or 0
        stddev = result.get("stddev", 0) or 0
        min_time = result.get("min", 0) or 0
        max_time = result.get("max", 0) or 0
        runs = len(result.get("times", []))

        lines.append(f"| `{cmd}` | {mean:.3f} | {stddev:.3f} | {min_time:.3f} | {max_time:.3f} | {runs} |")
    
    return "\n".join(lines)


def format_system_info(system_info: str) -> str:
    """Format system information for markdown."""
    if not system_info:
        return ""
    
    lines = system_info.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Convert key-value pairs to more readable format
        if ':' in line and not line.startswith('='):
            key, value = line.split(':', 1)
            formatted_lines.append(f"- **{key.strip()}**: {value.strip()}")
        elif line.startswith('='):
            # Section headers
            continue
        elif line and not line.startswith('-'):
            formatted_lines.append(f"- {line}")
        else:
            formatted_lines.append(line)
    
    return "\n".join(formatted_lines)


def generate_config_report(config_dir: Path, scripts_dir: Path, machine_dir: Path) -> str:
    """Generate report section for a single configuration."""
    config_name = config_dir.name
    json_file = config_dir / "benchmark.json"
    md_file = config_dir / "benchmark.md"
    system_info_file = config_dir / "system_info.txt"
    stats_file = config_dir / "advanced_statistics.log"
    plot_file = config_dir / "progression.png"
    
    # Ensure analysis files exist
    analysis_status = ensure_analysis_files(config_dir, scripts_dir)
    
    report_sections = [f"## {config_name.title()} Configuration"]
    
    # Add system information if available
    system_info = load_text_file(system_info_file)
    if system_info:
        report_sections.extend([
            "",
            "### System Information",
            "",
            format_system_info(system_info),
            ""
        ])
    
    # Load and summarize JSON data
    json_data = load_json_data(json_file)
    if json_data:
        summary_table = format_benchmark_summary(json_data)
        if summary_table:
            report_sections.extend([
                "### Benchmark Results Summary",
                "",
                summary_table,
                ""
            ])
    
    # Add progression plot if available
    if analysis_status["plot"] and plot_file.exists():
        # Use relative path for GitHub display from report location
        plot_rel_path = plot_file.relative_to(machine_dir)
        report_sections.extend([
            "### Performance Progression",
            "",
            f"![Progression Plot]({plot_rel_path})",
            ""
        ])
    
    # Add advanced statistics if available
    if analysis_status["stats"] and stats_file.exists():
        stats_content = load_text_file(stats_file)
        if stats_content:
            report_sections.extend([
                "### Advanced Statistics",
                "",
                "```",
                stats_content,
                "```",
                ""
            ])
    
    # Add hyperfine markdown report if available
    if md_file.exists():
        md_content = load_text_file(md_file)
        if md_content and "hyperfine" in md_content.lower():
            report_sections.extend([
                "### Detailed Hyperfine Report",
                "",
                md_content,
                ""
            ])
    
    return "\n".join(report_sections)


def generate_machine_report(machine_dir: Path, scripts_dir: Path) -> str:
    """Generate report for a single machine across all architectures and kernel versions."""
    machine_name = machine_dir.name
    report_sections = [f"# {machine_name.upper()} Benchmark Report"]

    report_sections.extend([
        "",
        f"Comprehensive benchmark results for machine **{machine_name}**.",
        "",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ])

    # Get all subdirectories
    subdirs = sorted([d for d in machine_dir.iterdir() if d.is_dir()])

    # Detect if we have architecture-based structure (arm64, x86_64, etc.)
    # or legacy structure (v6.x.x directly)
    arch_dirs = [d for d in subdirs if d.name in ['arm64', 'x86_64', 'arm', 'powerpc']]

    if arch_dirs:
        # New architecture-based structure
        for arch_dir in arch_dirs:
            arch_name = arch_dir.name
            report_sections.extend([
                f"## Architecture: {arch_name}",
                ""
            ])

            # Process each kernel version under this architecture
            kernel_versions = sorted([d for d in arch_dir.iterdir() if d.is_dir() and d.name.startswith('v')])

            for version_dir in kernel_versions:
                version_name = version_dir.name
                report_sections.extend([
                    f"### Kernel Version {version_name}",
                    ""
                ])

                # Process compiler directories (llvm, gcc, etc.)
                compiler_dirs = sorted([d for d in version_dir.iterdir() if d.is_dir()])

                for compiler_dir in compiler_dirs:
                    compiler_name = compiler_dir.name
                    report_sections.extend([
                        f"#### {compiler_name.upper()} Compiler Results",
                        ""
                    ])

                    config_dirs = sorted([d for d in compiler_dir.iterdir() if d.is_dir()])
                    for config_dir in config_dirs:
                        if (config_dir / "benchmark.json").exists():
                            config_report = generate_config_report(config_dir, scripts_dir, machine_dir)
                            if config_report:
                                report_sections.extend([config_report, ""])
    else:
        # Legacy structure: directly under machine (v6.x.x)
        kernel_versions = sorted([d for d in subdirs if d.name.startswith('v')])

        for version_dir in kernel_versions:
            version_name = version_dir.name
            report_sections.extend([
                f"## Kernel Version {version_name}",
                ""
            ])

            # Process compiler directories (llvm, gcc, etc.)
            compiler_dirs = sorted([d for d in version_dir.iterdir() if d.is_dir()])

            if not compiler_dirs:
                # Direct configuration directories (very old legacy format)
                config_dirs = sorted([d for d in version_dir.iterdir() if d.is_dir()])
                for config_dir in config_dirs:
                    if (config_dir / "benchmark.json").exists() or (config_dir / "btiny.json").exists():
                        config_report = generate_config_report(config_dir, scripts_dir, machine_dir)
                        if config_report:
                            report_sections.extend([config_report, ""])
            else:
                # Format with compiler subdirectories
                for compiler_dir in compiler_dirs:
                    compiler_name = compiler_dir.name
                    report_sections.extend([
                        f"### {compiler_name.upper()} Compiler Results",
                        ""
                    ])

                    config_dirs = sorted([d for d in compiler_dir.iterdir() if d.is_dir()])
                    for config_dir in config_dirs:
                        if (config_dir / "benchmark.json").exists():
                            config_report = generate_config_report(config_dir, scripts_dir, machine_dir)
                            if config_report:
                                report_sections.extend([config_report, ""])

    return "\n".join(report_sections)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "results_dir", 
        help="Results directory to process (e.g., results/mac1611)"
    )
    parser.add_argument(
        "--scripts-dir", 
        default="scripts",
        help="Directory containing analysis scripts"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output report filename (default: REPORT.md in results directory)"
    )
    parser.add_argument(
        "--generate-missing",
        action="store_true",
        default=True,
        help="Generate missing analysis files (default: True)"
    )
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    scripts_dir = Path(args.scripts_dir)
    
    if not results_dir.exists():
        print(f"Error: Results directory {results_dir} does not exist")
        sys.exit(1)
    
    if not scripts_dir.exists():
        print(f"Error: Scripts directory {scripts_dir} does not exist")
        sys.exit(1)
    
    # Determine output filename
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = results_dir / "REPORT.md"
    
    print(f"Generating comprehensive report for {results_dir}")
    print(f"Output: {output_file}")
    print(f"")
    print(f"Analyzing benchmark results and generating artifacts...")

    # Generate the report (this will call ensure_analysis_files for each config)
    report_content = generate_machine_report(results_dir, scripts_dir)

    # Write the report
    with open(output_file, 'w') as f:
        f.write(report_content)

    print(f"")
    print(f"✅ Report generated: {output_file}")
    print(f"📊 Report contains benchmark data, system info, statistics, and plots")


if __name__ == "__main__":
    main()