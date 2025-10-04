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
import base64
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


def encode_image_base64(image_path: Path) -> Optional[str]:
    """Encode image file to base64 for embedding in HTML."""
    try:
        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
    except (FileNotFoundError, IOError):
        return None


def parse_system_info_html(system_info: str) -> Dict[str, str]:
    """Parse system info into key-value pairs for HTML display."""
    info = {}
    if not system_info:
        return info

    lines = system_info.split('\n')
    for line in lines:
        line = line.strip()
        if ':' in line and not line.startswith('='):
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()

    return info


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


def generate_html_report(machine_dir: Path, scripts_dir: Path) -> str:
    """Generate HTML report for a single machine across all architectures and kernel versions."""
    machine_name = machine_dir.name

    # Collect all configurations
    all_configs = []
    subdirs = sorted([d for d in machine_dir.iterdir() if d.is_dir()])
    arch_dirs = [d for d in subdirs if d.name in ['arm64', 'x86_64', 'arm', 'powerpc']]

    if arch_dirs:
        # New architecture-based structure
        for arch_dir in arch_dirs:
            arch_name = arch_dir.name
            kernel_versions = sorted([d for d in arch_dir.iterdir() if d.is_dir() and d.name.startswith('v')])

            for version_dir in kernel_versions:
                version_name = version_dir.name
                compiler_dirs = sorted([d for d in version_dir.iterdir() if d.is_dir()])

                for compiler_dir in compiler_dirs:
                    compiler_name = compiler_dir.name
                    config_dirs = sorted([d for d in compiler_dir.iterdir() if d.is_dir()])

                    for config_dir in config_dirs:
                        json_file = config_dir / "benchmark.json"
                        if json_file.exists():
                            all_configs.append({
                                'arch': arch_name,
                                'version': version_name,
                                'compiler': compiler_name,
                                'config': config_dir.name,
                                'dir': config_dir
                            })
    else:
        # Legacy structure
        kernel_versions = sorted([d for d in subdirs if d.name.startswith('v')])
        for version_dir in kernel_versions:
            compiler_dirs = sorted([d for d in version_dir.iterdir() if d.is_dir()])

            for compiler_dir in compiler_dirs:
                config_dirs = sorted([d for d in compiler_dir.iterdir() if d.is_dir()])
                for config_dir in config_dirs:
                    json_file = config_dir / "benchmark.json"
                    if json_file.exists():
                        all_configs.append({
                            'arch': 'N/A',
                            'version': version_dir.name,
                            'compiler': compiler_dir.name,
                            'config': config_dir.name,
                            'dir': config_dir
                        })

    # Generate summary statistics from first available config
    summary_stats = {}
    if all_configs:
        first_config = all_configs[0]
        system_info_file = first_config['dir'] / "system_info.txt"
        system_info = load_text_file(system_info_file)
        info_dict = parse_system_info_html(system_info)

        json_file = first_config['dir'] / "benchmark.json"
        json_data = load_json_data(json_file)

        if json_data and "results" in json_data and json_data["results"]:
            result = json_data["results"][0]
            summary_stats['mean_time'] = f"{result.get('mean', 0) or 0:.1f}s"
            summary_stats['threads'] = info_dict.get('Make Threads', 'N/A')

        summary_stats['compiler'] = info_dict.get('Compiler', 'N/A')
        summary_stats['kernel'] = first_config['version']
        summary_stats['arch'] = first_config['arch']
        summary_stats['cpu'] = info_dict.get('CPU', 'N/A')

    # Generate config sections HTML
    configs_html = ""
    for cfg in all_configs:
        ensure_analysis_files(cfg['dir'], scripts_dir)

        config_header = f"{cfg['arch']} / {cfg['version']} / {cfg['compiler']} / {cfg['config']}"

        json_file = cfg['dir'] / "benchmark.json"
        system_info_file = cfg['dir'] / "system_info.txt"
        stats_file = cfg['dir'] / "advanced_statistics.log"
        plot_file = cfg['dir'] / "progression.png"

        configs_html += f"""
        <div class="section">
            <h2 class="section-title">{config_header}</h2>
"""

        # System information
        system_info = load_text_file(system_info_file)
        if system_info:
            info_dict = parse_system_info_html(system_info)
            info_items = "".join([f"<li><strong>{k}:</strong> {v}</li>\n" for k, v in info_dict.items()])
            configs_html += f"""
            <div class="info-box">
                <h3 style="margin-top: 0; color: #2d3748;">System Information</h3>
                <ul>
{info_items}                </ul>
            </div>
"""

        # Benchmark results table
        json_data = load_json_data(json_file)
        if json_data and "results" in json_data:
            configs_html += """
            <h3 style="color: #4a5568; margin-top: 30px;">Benchmark Results</h3>
            <table>
                <tr>
                    <th>Command</th>
                    <th>Mean (s)</th>
                    <th>Std Dev (s)</th>
                    <th>Min (s)</th>
                    <th>Max (s)</th>
                    <th>Runs</th>
                </tr>
"""

            for result in json_data["results"]:
                cmd = result.get("command", "").replace("make LLVM=1 -j", "make -j").replace("make  -j", "make -j")
                mean = result.get("mean", 0) or 0
                stddev = result.get("stddev", 0) or 0
                min_time = result.get("min", 0) or 0
                max_time = result.get("max", 0) or 0
                runs = len(result.get("times", []))

                configs_html += f"""                <tr>
                    <td><code>{cmd}</code></td>
                    <td>{mean:.3f}</td>
                    <td>{stddev:.3f}</td>
                    <td>{min_time:.3f}</td>
                    <td>{max_time:.3f}</td>
                    <td>{runs}</td>
                </tr>
"""

            configs_html += "            </table>\n"

        # Progression plot
        if plot_file.exists():
            plot_base64 = encode_image_base64(plot_file)
            if plot_base64:
                configs_html += f"""
            <div class="chart-container">
                <h3 style="color: #4a5568; margin-top: 30px;">Performance Progression</h3>
                <img src="{plot_base64}" alt="Progression Plot" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            </div>
"""

        # Advanced statistics
        if stats_file.exists():
            stats_content = load_text_file(stats_file)
            if stats_content:
                configs_html += f"""
            <h3 style="color: #4a5568; margin-top: 30px;">Advanced Statistics</h3>
            <pre style="background: #f7fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; overflow-x: auto;">{stats_content}</pre>
"""

        configs_html += "        </div>\n"

    # Build HTML document
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{machine_name.upper()} - Linux Kernel Build Benchmarks</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #2d3748;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .timestamp {{
            text-align: center;
            color: #718096;
            margin-bottom: 30px;
            font-size: 0.9em;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.2);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .info-box {{
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 30px 0;
            border-radius: 5px;
        }}
        .info-box ul {{
            margin: 10px 0;
            padding-left: 20px;
            list-style: none;
        }}
        .info-box li {{
            margin: 8px 0;
            color: #4a5568;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:hover {{
            background: #f7fafc;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section-title {{
            font-size: 1.8em;
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .chart-container {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: #f7fafc;
            border-radius: 10px;
        }}
        code {{
            background: #edf2f7;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{machine_name.upper()} Build Benchmarks</h1>
        <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

        <div class="summary-grid">
            <div class="stat-card">
                <div class="stat-label">Architecture</div>
                <div class="stat-value">{summary_stats.get('arch', 'N/A')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Kernel Version</div>
                <div class="stat-value">{summary_stats.get('kernel', 'N/A')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Build Time</div>
                <div class="stat-value">{summary_stats.get('mean_time', 'N/A')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Compiler</div>
                <div class="stat-value">{summary_stats.get('compiler', 'N/A')}</div>
            </div>
        </div>

        <div class="info-box">
            <h3 style="margin-top: 0; color: #2d3748;">About This Report</h3>
            <ul>
                <li><strong>Machine:</strong> {machine_name}</li>
                <li><strong>CPU:</strong> {summary_stats.get('cpu', 'N/A')}</li>
                <li><strong>Configurations:</strong> {len(all_configs)} benchmark(s)</li>
                <li><strong>Reproducible Builds:</strong> Enabled</li>
            </ul>
        </div>

{configs_html}

        <div style="text-align: center; padding: 30px 0; color: #718096; font-size: 0.9em; border-top: 1px solid #e2e8f0; margin-top: 40px;">
            <p>Linux Kernel Build Benchmarks</p>
            <p>Generated with hyperfine • Reproducible builds enabled</p>
        </div>
    </div>
</body>
</html>
"""

    return html_content


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
    
    # Determine output filenames
    if args.output:
        md_output = Path(args.output)
        html_output = md_output.with_suffix('.html')
    else:
        md_output = results_dir / "REPORT.md"
        html_output = results_dir / "index.html"

    print(f"Generating comprehensive reports for {results_dir}")
    print(f"")
    print(f"Analyzing benchmark results and generating artifacts...")

    # Generate the markdown report (this will call ensure_analysis_files for each config)
    md_content = generate_machine_report(results_dir, scripts_dir)

    # Write the markdown report
    with open(md_output, 'w') as f:
        f.write(md_content)

    # Generate and write the HTML report
    html_content = generate_html_report(results_dir, scripts_dir)
    with open(html_output, 'w') as f:
        f.write(html_content)

    print(f"")
    print(f"✅ Reports generated:")
    print(f"   📄 Markdown: {md_output}")
    print(f"   🌐 HTML: {html_output}")
    print(f"📊 Reports contain benchmark data, system info, statistics, and plots")


if __name__ == "__main__":
    main()