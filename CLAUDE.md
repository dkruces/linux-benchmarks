# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains Linux kernel build benchmarks using hyperfine. The project focuses on performance analysis of different kernel configurations and compilation parameters.

## Repository Structure

- `results/` - Archived benchmark results organized by machine and kernel version
  - Each machine has subdirectories for specific kernel versions (e.g., `v6.12-rc6/`)
  - Results include JSON data files, markdown reports, progression plots, and advanced statistics
  - **Benchmark artifacts per configuration**:
    - `benchmark.json` - Hyperfine performance data
    - `benchmark.md` - Human-readable benchmark report
    - `system_info.txt` - Complete system and build environment info
    - `.config` - Final kernel configuration used for the build
    - `fragments.txt` - List of configuration fragments used
    - Individual fragment files (for fragment-based configs)
    - `progression.png` - Performance progression plot (when generated)
    - `advanced_statistics.log` - Detailed statistical analysis (when generated)

## Benchmark Workflow

The primary benchmarking approach uses hyperfine with the following pattern:

```sh
hyperfine \
  --parameter-scan nproc 8 16 \
  --parameter-step-size 8 \
  --prepare 'make LLVM=1 btiny_defconfig' \
  --runs 10 'make LLVM=1 -j{nproc}' \
  --conclude 'make LLVM=1 mrproper' \
  --export-markdown btiny.md \
  --export-json btiny.json
```

## Analysis Tools

The project relies on hyperfine's analysis scripts:

1. **Advanced Statistics**: `scripts/advanced_statistics.py btiny.json`
   - Provides detailed statistical analysis of benchmark runs
   - Shows mean, stddev, median, min/max, and percentiles

2. **Progression Plots**: `scripts/plot_progression.py btiny.json --output progression.png`
   - Creates visual progression charts of benchmark performance

## Typical Build Configurations

- Uses LLVM=1 flag for Clang-based compilation
- Common configs: `btiny_defconfig`, minimal configurations
- Thread counts typically tested: 8, 16 (varies by machine)
- Architecture typically x86_64

## Reproducible Builds

This project always uses reproducible builds following the Linux kernel's `Documentation/kbuild/reproducible-builds.rst` guidelines. Reproducible builds ensure identical output from the same source code and build environment, providing consistent benchmark results.

### Reproducible Build Features

All builds automatically include:

1. **Build Environment**:
   - `KBUILD_BUILD_TIMESTAMP`: Fixed to `1991-08-25` (Linux announcement date)
   - `KBUILD_BUILD_USER`: Fixed to `user`
   - `KBUILD_BUILD_HOST`: Fixed to `host`

2. **Debug Information**:
   - `KCFLAGS`: Includes `-fdebug-prefix-map` for consistent debug paths
   - Maps absolute kernel source paths to `/usr/src/linux` (ready for out-of-tree builds)

### Benefits

- **Verification**: Ensures build infrastructure hasn't been compromised
- **Comparison**: True performance differences vs. build artifacts
- **Consistency**: Same source + tools = identical binaries

## Benchmark Traceability

Each benchmark run captures complete build environment and configuration details:

### Configuration Preservation
- **`.config`**: Final merged kernel configuration used for the build
- **`fragments.txt`**: List of configuration fragments that were merged
- **Fragment files**: Copies of individual configuration fragment files (when using fragment-based configs)

### Environment Capture
- **Build environment variables**: All reproducible build settings (KBUILD_*, KCFLAGS)
- **System information**: Hardware specs, compiler versions, build parameters
- **Timestamp information**: When the benchmark was run and build environment state

This ensures every benchmark result can be exactly reproduced with the same configuration and environment.

### Backfilling Missing Configuration Files

For existing benchmark results that lack configuration files, use:

```sh
make backfill-configs
```

This will automatically:
- Find all existing benchmark results (directories with `benchmark.json`)
- Generate missing `.config` files for each configuration
- Create `fragments.txt` with the list of fragments used
- Copy individual fragment files to each result directory
- Skip directories that already have complete configuration files

Supported configurations: `minimal`, `ebpf-ready`, `modules-ready`, `debug-ready`, and kernel-native configs (`defconfig`, `allyesconfig`, etc.).

## Machine-Specific Results

Results are organized by machine identifier (e.g., `mac142`, `x1gen7`) to track performance characteristics across different hardware configurations.

## Commit Guidelines

### One Commit Per Change

As with the Linux kernel, this project prefers commits to be atomic and to the point. We don't want spell fixes to be blended in with code changes. Spell fixes should go into separate commits. When in doubt, just don't do any spell fixes unless asked explicitly to do that.

### Use the Signed-off-by Tag

We want to use the Signed-off-by tag which embodies the application of the Developer Certificate of Origin.

### Use Generated-by: Claude AI

Use this tag for code generated by Claude Code AI. Put this before the Signed-off-by tag.

**CRITICAL FORMATTING RULE**: When using "Generated-by: Claude AI", it MUST be immediately followed by the "Signed-off-by:" tag with NO empty lines between them. These two lines must be consecutive.

**Correct format:**
```
Subject line

Detailed description of changes...

Generated-by: Claude AI
Signed-off-by: Your Name <email@example.com>
```

**WRONG** - Do NOT add empty lines between Generated-by and Signed-off-by:
```
Generated-by: Claude AI

Signed-off-by: Your Name <email@example.com>
```