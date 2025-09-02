# Linux Kernel Benchmarks Makefile
# Parametrized benchmark system with multiple configurations

.PHONY: help minimal ebpf-ready modules-ready debug-ready
.PHONY: kvm_guest virtio-fs systemd distro storage numa ebpf ebpf-errorinj
.PHONY: defconfig alldefconfig allyesconfig allnoconfig tinyconfig
.PHONY: analyze plot clean-results setup-scripts system-info

# Default target
all: help

# Configurable paths
KERNEL_SOURCE ?= $(HOME)/src/kernel/linux
CONFIG_FRAGMENTS ?= $(HOME)/src/linux-config-fragments

# Machine detection - works on both macOS and Linux
MACHINE_ID ?= $(shell \
	if [ "$$(uname)" = "Darwin" ]; then \
		sysctl -n hw.model | tr '[:upper:]' '[:lower:]' | tr -d ','; \
	elif [ -f /sys/class/dmi/id/product_name ] && [ -r /sys/class/dmi/id/product_name ]; then \
		cat /sys/class/dmi/id/product_name | tr ' ' '_' | tr '[:upper:]' '[:lower:]'; \
	elif [ -f /sys/class/dmi/id/board_name ] && [ -r /sys/class/dmi/id/board_name ]; then \
		cat /sys/class/dmi/id/board_name | tr ' ' '_' | tr '[:upper:]' '[:lower:]'; \
	elif command -v lscpu >/dev/null 2>&1; then \
		echo "linux_$$(lscpu | grep 'Architecture' | awk '{print $$2}' | tr '[:upper:]' '[:lower:]')"; \
	else \
		echo "linux_$$(uname -m)"; \
	fi)

# Kernel version (user can override, defaults to v6.12.0)
KERNEL_VERSION ?= v6.12.0

# Detect actual kernel version from validated source tree
DETECTED_KERNEL_VERSION := $(shell \
	if [ -f $(KERNEL_SOURCE)/COPYING ] && \
	   [ -f $(KERNEL_SOURCE)/CREDITS ] && \
	   [ -f $(KERNEL_SOURCE)/Kbuild ] && \
	   [ -f $(KERNEL_SOURCE)/MAINTAINERS ] && \
	   [ -f $(KERNEL_SOURCE)/Makefile ] && \
	   [ -f $(KERNEL_SOURCE)/README ] && \
	   [ -d $(KERNEL_SOURCE)/Documentation ] && \
	   [ -d $(KERNEL_SOURCE)/arch ] && \
	   [ -d $(KERNEL_SOURCE)/include ] && \
	   [ -d $(KERNEL_SOURCE)/drivers ] && \
	   [ -d $(KERNEL_SOURCE)/fs ] && \
	   [ -d $(KERNEL_SOURCE)/init ] && \
	   [ -d $(KERNEL_SOURCE)/ipc ] && \
	   [ -d $(KERNEL_SOURCE)/kernel ] && \
	   [ -d $(KERNEL_SOURCE)/lib ] && \
	   [ -d $(KERNEL_SOURCE)/scripts ]; then \
		echo "v$$(make -s -C $(KERNEL_SOURCE) kernelversion)"; \
	else \
		echo "invalid"; \
	fi)

# Benchmark parameters
COMPILER_DIR = $(if $(LLVM_FLAG),llvm,gcc)
RESULTS_BASE_DIR = results/$(MACHINE_ID)/$(KERNEL_VERSION)/$(COMPILER_DIR)
NPROC := $(shell nproc)
MIN_THREADS ?= $(NPROC)
MAX_THREADS ?= $(shell expr $(NPROC) \* 2)
THREAD_STEP ?= $(NPROC)
RUNS ?= 10
WARMUP ?= 1

# Reproducible builds support (see Documentation/kbuild/reproducible-builds.rst)
# Always enabled for consistent benchmark results

# Reproducible build variables (Documentation/kbuild/reproducible-builds.rst)
export KBUILD_BUILD_TIMESTAMP = 1991-08-25
export KBUILD_BUILD_USER = user
export KBUILD_BUILD_HOST = host
export KCFLAGS = -fdebug-prefix-map=$(KERNEL_SOURCE)=/usr/src/linux

# Always use reproducible builds
RESULTS_BASE_DIR = results/$(MACHINE_ID)/$(KERNEL_VERSION)/$(COMPILER_DIR)

# Base config files
BASE_CONFIGS = $(CONFIG_FRAGMENTS)/kernel/configs/64bit.config

# Configuration definitions
MINIMAL_CONFIGS = $(BASE_CONFIGS) \
	$(KERNEL_SOURCE)/kernel/configs/kvm_guest.config \
	$(CONFIG_FRAGMENTS)/kernel/configs/virtio-fs.config \
	$(CONFIG_FRAGMENTS)/kernel/configs/systemd.config \
	$(CONFIG_FRAGMENTS)/kernel/configs/distro.config \
	$(CONFIG_FRAGMENTS)/kernel/configs/storage.config

EBPF_READY_CONFIGS = $(MINIMAL_CONFIGS) \
	$(CONFIG_FRAGMENTS)/kernel/configs/numa.config \
	$(CONFIG_FRAGMENTS)/kernel/configs/ebpf.config \
	$(CONFIG_FRAGMENTS)/kernel/configs/ebpf-errorinj.config

MODULES_READY_CONFIGS = $(MINIMAL_CONFIGS) \
	$(CONFIG_FRAGMENTS)/kernel/configs/modules.config

DEBUG_READY_CONFIGS = $(MINIMAL_CONFIGS) \
	$(CONFIG_FRAGMENTS)/kernel/configs/vm_debug.config \
	$(CONFIG_FRAGMENTS)/kernel/configs/gdb.config

# Determine if we need bee-init (macOS only) and LLVM flag
BEE_INIT_CMD = $(shell \
	if [ "$$(uname)" = "Darwin" ]; then \
		echo "source bee-init &&"; \
	else \
		echo ""; \
	fi)

# LLVM compiler selection
# On macOS: Always use LLVM (required for kernel builds)
# On Linux: Default to GCC, but allow LLVM=1 override
LLVM_FLAG = $(shell \
	if [ "$$(uname)" = "Darwin" ]; then \
		echo "LLVM=1"; \
	elif [ "$(LLVM)" = "1" ]; then \
		echo "LLVM=1"; \
	else \
		echo ""; \
	fi)

help:
	@echo "Linux Kernel Benchmarks - Parametrized Benchmark System"
	@echo ""
	@echo "Configuration targets:"
	@echo "  minimal         - Basic functional kernel with KVM/systemd support"
	@echo "  ebpf-ready      - Minimal + eBPF support with error injection"
	@echo "  modules-ready   - Minimal + module support"
	@echo "  debug-ready     - Minimal + VM debugging and GDB support"
	@echo ""
	@echo "Individual config targets:"
	@echo "  kvm_guest       - KVM guest optimizations"
	@echo "  virtio-fs       - VirtIO filesystem support"
	@echo "  systemd         - Systemd requirements"
	@echo "  distro          - Distribution compatibility"
	@echo "  storage         - Storage drivers"
	@echo "  numa            - NUMA support"
	@echo "  ebpf            - eBPF support"
	@echo "  ebpf-errorinj   - eBPF error injection"
	@echo ""
	@echo "Kernel-native config targets:"
	@echo "  defconfig       - Default config from ARCH supplied defconfig"
	@echo "  alldefconfig    - All symbols set to default values"
	@echo "  allyesconfig    - New config where all options are accepted with yes"
	@echo "  allnoconfig     - New config where all options are answered with no"
	@echo "  tinyconfig      - Configure the tiniest possible kernel"
	@echo ""
	@echo "System targets:"
	@echo "  analyze         - Generate advanced statistics from existing results"
	@echo "  plot            - Generate progression plots from existing results"
	@echo "  report          - Generate comprehensive markdown report with all analysis"
	@echo "  setup-scripts   - Download hyperfine analysis scripts"
	@echo "  system-info     - Display current system information"
	@echo "  clean-results   - Remove all benchmark results"
	@echo "  help            - Show this help message"
	@echo ""
	@echo "Configuration variables:"
	@echo "  KERNEL_SOURCE   = $(KERNEL_SOURCE)"
	@echo "  CONFIG_FRAGMENTS= $(CONFIG_FRAGMENTS)"
	@echo "  MACHINE_ID      = $(MACHINE_ID)"
	@echo "  KERNEL_VERSION  = $(KERNEL_VERSION)"
	@echo "  MIN_THREADS     = $(MIN_THREADS)"
	@echo "  MAX_THREADS     = $(MAX_THREADS)"
	@echo "  THREAD_STEP     = $(THREAD_STEP)"
	@echo "  RUNS            = $(RUNS)"
	@echo "  WARMUP          = $(WARMUP)"
	@echo "  LLVM            = $(LLVM) (1 for LLVM/Clang, unset for GCC on Linux)"
	@echo ""
	@echo "Compiler selection:"
	@echo "  macOS: Always uses LLVM/Clang (required for kernel builds)"
	@echo "  Linux: Uses GCC by default, set LLVM=1 for LLVM/Clang"
	@echo ""
	@echo "Example usage:"
	@echo "  make minimal                    # Use default compiler (GCC on Linux, LLVM on macOS)"
	@echo "  make minimal LLVM=1             # Force LLVM/Clang on Linux"
	@echo "  make ebpf-ready RUNS=5 LLVM=1   # Custom runs with LLVM"
	@echo "  make debug-ready KERNEL_SOURCE=/path/to/kernel CONFIG_FRAGMENTS=/path/to/fragments"

# Validate kernel version matches user expectation
validate-kernel:
	@if [ "$(DETECTED_KERNEL_VERSION)" = "invalid" ]; then \
		echo "❌ ERROR: $(KERNEL_SOURCE) is not a valid Linux kernel source tree"; \
		echo "   Missing required files/directories for kernel source validation"; \
		exit 1; \
	fi
	@if [ "$(KERNEL_VERSION)" != "$(DETECTED_KERNEL_VERSION)" ]; then \
		echo "❌ ERROR: Kernel version mismatch!"; \
		echo "   Expected: $(KERNEL_VERSION)"; \
		echo "   Detected: $(DETECTED_KERNEL_VERSION)"; \
		echo "   Source:   $(KERNEL_SOURCE)"; \
		echo ""; \
		echo "   Either:"; \
		echo "   1. Use correct version: make target KERNEL_VERSION=$(DETECTED_KERNEL_VERSION)"; \
		echo "   2. Or change KERNEL_SOURCE to point to $(KERNEL_VERSION) source"; \
		exit 1; \
	fi
	@echo "✅ Kernel version validated: $(KERNEL_VERSION)"

# Create base results directory
$(RESULTS_BASE_DIR): validate-kernel
	@mkdir -p $(RESULTS_BASE_DIR)

# Common system information collection function
define collect_system_info
	@if command -v fastfetch >/dev/null 2>&1; then \
		fastfetch --logo none -s CPU:CPUCache:GPU:Kernel:OS:Host:Memory:PhysicalMemory > $(1) 2>/dev/null; \
	fi
	@echo "" >> $(1)
	@echo "Build Environment:" >> $(1)
	@echo "=================" >> $(1)
	@echo "Compiler: $(if $(LLVM_FLAG),LLVM/Clang,GCC)" >> $(1)
	@echo "LLVM Flag: $(LLVM_FLAG)" >> $(1)
	@echo "Reproducible Builds: Enabled" >> $(1)
	@echo "KBUILD_BUILD_TIMESTAMP: $(KBUILD_BUILD_TIMESTAMP)" >> $(1)
	@echo "KBUILD_BUILD_USER: $(KBUILD_BUILD_USER)" >> $(1)
	@echo "KBUILD_BUILD_HOST: $(KBUILD_BUILD_HOST)" >> $(1)
	@echo "KCFLAGS: $(KCFLAGS)" >> $(1)
	@echo "Make Threads: $(MIN_THREADS)-$(MAX_THREADS) (step: $(THREAD_STEP))" >> $(1)
	@echo "Benchmark Runs: $(RUNS)" >> $(1)
	@echo "Warmup Runs: $(WARMUP)" >> $(1)
	@echo "Kernel Source: $(KERNEL_SOURCE)" >> $(1)
	@echo "Config Fragments: $(CONFIG_FRAGMENTS)" >> $(1)
	@echo "Machine ID: $(MACHINE_ID)" >> $(1)
	@echo "Kernel Version: $(KERNEL_VERSION)" >> $(1)
	@date +'Build Date: %Y-%m-%d %H:%M:%S %Z' >> $(1)
	@if command -v gcc >/dev/null 2>&1; then \
		echo "GCC Version: $$(gcc --version | head -1)" >> $(1); \
	fi
	@if command -v clang >/dev/null 2>&1; then \
		echo "Clang Version: $$(clang --version | head -1)" >> $(1); \
	fi
endef

# Generic benchmark function for fragment-based configs
define run_benchmark
	@echo "🚀 Starting $(1) benchmark with $(MIN_THREADS)-$(MAX_THREADS) threads ($(RUNS) runs)"
	@echo "📍 Working in: $(KERNEL_SOURCE)"
	@echo "💾 Results to: $(RESULTS_BASE_DIR)/$(1)/"
	@echo "🔧 Compiler: $(if $(LLVM_FLAG),LLVM/Clang,GCC)"
	@mkdir -p $(RESULTS_BASE_DIR)/$(1)
	@echo "📋 Collecting system information..."
	$(call collect_system_info,$(RESULTS_BASE_DIR)/$(1)/system_info.txt)
	@echo "📝 Copying configuration fragments..."
	@echo "# Configuration fragments used for $(1)" > $(RESULTS_BASE_DIR)/$(1)/fragments.txt
	@for fragment in $(2); do \
		echo "$$fragment" >> $(RESULTS_BASE_DIR)/$(1)/fragments.txt; \
		if [ -f "$$fragment" ]; then \
			cp "$$fragment" "$(RESULTS_BASE_DIR)/$(1)/" 2>/dev/null || true; \
		fi; \
	done
	cd $(KERNEL_SOURCE) && $(BEE_INIT_CMD) \
	hyperfine \
		--parameter-scan nproc $(MIN_THREADS) $(MAX_THREADS) \
		--parameter-step-size $(THREAD_STEP) \
		--warmup $(WARMUP) \
		--prepare '$(KERNEL_SOURCE)/scripts/kconfig/merge_config.sh -n .config $(2)' \
		--runs $(RUNS) 'make $(LLVM_FLAG) -j{nproc}' \
		--conclude 'make $(LLVM_FLAG) mrproper' \
		--export-markdown $(PWD)/$(RESULTS_BASE_DIR)/$(1)/benchmark.md \
		--export-json $(PWD)/$(RESULTS_BASE_DIR)/$(1)/benchmark.json
	@echo "📄 Copying final configuration..."
	@cd $(KERNEL_SOURCE) && $(KERNEL_SOURCE)/scripts/kconfig/merge_config.sh -n .config $(2) >/dev/null 2>&1 && cp .config $(PWD)/$(RESULTS_BASE_DIR)/$(1)/ && make $(LLVM_FLAG) mrproper >/dev/null 2>&1
endef

# Simple benchmark function for kernel-native configs (defconfig, alldefconfig, etc.)
define run_kernel_config_benchmark
	@echo "🚀 Starting $(1) benchmark with $(MIN_THREADS)-$(MAX_THREADS) threads ($(RUNS) runs)"
	@echo "📍 Working in: $(KERNEL_SOURCE)"
	@echo "💾 Results to: $(RESULTS_BASE_DIR)/$(1)/"
	@echo "🔧 Compiler: $(if $(LLVM_FLAG),LLVM/Clang,GCC)"
	@mkdir -p $(RESULTS_BASE_DIR)/$(1)
	@echo "📋 Collecting system information..."
	$(call collect_system_info,$(RESULTS_BASE_DIR)/$(1)/system_info.txt)
	@echo "📝 Recording kernel-native configuration..."
	@echo "# Kernel-native configuration: $(1)" > $(RESULTS_BASE_DIR)/$(1)/fragments.txt
	@echo "Using built-in kernel configuration target: $(1)" >> $(RESULTS_BASE_DIR)/$(1)/fragments.txt
	cd $(KERNEL_SOURCE) && $(BEE_INIT_CMD) \
	hyperfine \
		--parameter-scan nproc $(MIN_THREADS) $(MAX_THREADS) \
		--parameter-step-size $(THREAD_STEP) \
		--warmup $(WARMUP) \
		--prepare 'make $(LLVM_FLAG) $(1)' \
		--runs $(RUNS) 'make $(LLVM_FLAG) -j{nproc}' \
		--conclude 'make $(LLVM_FLAG) mrproper' \
		--export-markdown $(PWD)/$(RESULTS_BASE_DIR)/$(1)/benchmark.md \
		--export-json $(PWD)/$(RESULTS_BASE_DIR)/$(1)/benchmark.json
	@echo "📄 Copying final configuration..."
	@cd $(KERNEL_SOURCE) && make $(LLVM_FLAG) $(1) >/dev/null 2>&1 && cp .config $(PWD)/$(RESULTS_BASE_DIR)/$(1)/ && make $(LLVM_FLAG) mrproper >/dev/null 2>&1
endef

# Configuration targets
minimal: $(RESULTS_BASE_DIR)
	$(call run_benchmark,minimal,$(MINIMAL_CONFIGS))

ebpf-ready: $(RESULTS_BASE_DIR)
	$(call run_benchmark,ebpf-ready,$(EBPF_READY_CONFIGS))

modules-ready: $(RESULTS_BASE_DIR)
	$(call run_benchmark,modules-ready,$(MODULES_READY_CONFIGS))

debug-ready: $(RESULTS_BASE_DIR)
	$(call run_benchmark,debug-ready,$(DEBUG_READY_CONFIGS))

# Individual config benchmarks
kvm_guest: $(RESULTS_BASE_DIR)
	$(call run_benchmark,kvm_guest,$(BASE_CONFIGS) $(KERNEL_SOURCE)/kernel/configs/kvm_guest.config)

virtio-fs: $(RESULTS_BASE_DIR)
	$(call run_benchmark,virtio-fs,$(BASE_CONFIGS) $(CONFIG_FRAGMENTS)/kernel/configs/virtio-fs.config)

systemd: $(RESULTS_BASE_DIR)
	$(call run_benchmark,systemd,$(BASE_CONFIGS) $(CONFIG_FRAGMENTS)/kernel/configs/systemd.config)

distro: $(RESULTS_BASE_DIR)
	$(call run_benchmark,distro,$(BASE_CONFIGS) $(CONFIG_FRAGMENTS)/kernel/configs/distro.config)

storage: $(RESULTS_BASE_DIR)
	$(call run_benchmark,storage,$(BASE_CONFIGS) $(CONFIG_FRAGMENTS)/kernel/configs/storage.config)

numa: $(RESULTS_BASE_DIR)
	$(call run_benchmark,numa,$(BASE_CONFIGS) $(CONFIG_FRAGMENTS)/kernel/configs/numa.config)

ebpf: $(RESULTS_BASE_DIR)
	$(call run_benchmark,ebpf,$(BASE_CONFIGS) $(CONFIG_FRAGMENTS)/kernel/configs/ebpf.config)

ebpf-errorinj: $(RESULTS_BASE_DIR)
	$(call run_benchmark,ebpf-errorinj,$(BASE_CONFIGS) $(CONFIG_FRAGMENTS)/kernel/configs/ebpf-errorinj.config)

# Kernel-native configuration targets
defconfig: $(RESULTS_BASE_DIR)
	$(call run_kernel_config_benchmark,defconfig)

alldefconfig: $(RESULTS_BASE_DIR)
	$(call run_kernel_config_benchmark,alldefconfig)

allyesconfig: $(RESULTS_BASE_DIR)
	$(call run_kernel_config_benchmark,allyesconfig)

allnoconfig: $(RESULTS_BASE_DIR)
	$(call run_kernel_config_benchmark,allnoconfig)

tinyconfig: $(RESULTS_BASE_DIR)
	$(call run_kernel_config_benchmark,tinyconfig)

# Download hyperfine analysis scripts
setup-scripts:
	@echo "📥 Setting up hyperfine analysis scripts..."
	@if [ ! -d "scripts" ]; then \
		mkdir scripts; \
		echo "  Created scripts directory"; \
	fi
	@if [ ! -f "scripts/advanced_statistics.py" ] || [ ! -f "scripts/plot_progression.py" ]; then \
		echo "  Downloading hyperfine analysis scripts..."; \
		curl -fsSL https://raw.githubusercontent.com/sharkdp/hyperfine/master/scripts/advanced_statistics.py -o scripts/advanced_statistics.py; \
		curl -fsSL https://raw.githubusercontent.com/sharkdp/hyperfine/master/scripts/plot_progression.py -o scripts/plot_progression.py; \
		chmod +x scripts/*.py; \
		echo "✅ Scripts downloaded successfully"; \
	else \
		echo "✅ Scripts already exist"; \
	fi

# Generate advanced statistics for all JSON files in results directory
analyze: $(RESULTS_BASE_DIR) setup-scripts
	@echo "📈 Generating advanced statistics for all benchmark results..."
	@if [ -f "scripts/advanced_statistics.py" ]; then \
		for config_dir in $(RESULTS_BASE_DIR)/*/; do \
			if [ -d "$$config_dir" ]; then \
				config_name=$$(basename "$$config_dir"); \
				json_file="$$config_dir/benchmark.json"; \
				if [ -f "$$json_file" ]; then \
					echo "  Processing $$config_name..."; \
					cd "$$config_dir" && uv run ../../../../../scripts/advanced_statistics.py benchmark.json > advanced_statistics.log; \
					cd - > /dev/null; \
				fi \
			fi \
		done; \
	else \
		echo "⚠️  scripts/advanced_statistics.py not found - skipping statistics"; \
	fi

# Generate progression plots for all JSON files in results directory
plot: $(RESULTS_BASE_DIR) setup-scripts
	@echo "📊 Generating progression plots for all benchmark results..."
	@if [ -f "scripts/plot_progression.py" ]; then \
		for config_dir in $(RESULTS_BASE_DIR)/*/; do \
			if [ -d "$$config_dir" ]; then \
				config_name=$$(basename "$$config_dir"); \
				json_file="$$config_dir/benchmark.json"; \
				if [ -f "$$json_file" ]; then \
					echo "  Processing $$config_name..."; \
					cd "$$config_dir" && uv run ../../../../../scripts/plot_progression.py benchmark.json --output progression.png; \
					cd - > /dev/null; \
				fi \
			fi \
		done; \
	else \
		echo "⚠️  scripts/plot_progression.py not found - skipping plots"; \
	fi

# Generate comprehensive markdown report for current machine
report: setup-scripts
	@echo "📄 Generating comprehensive benchmark report..."
	@machine_results_dir="results/$(MACHINE_ID)"; \
	if [ -d "$$machine_results_dir" ]; then \
		echo "  Processing results for machine: $(MACHINE_ID)"; \
		if [ -f "scripts/generate_report.py" ]; then \
			uv run scripts/generate_report.py "$$machine_results_dir" --scripts-dir scripts; \
			echo "✅ Report generated: $$machine_results_dir/REPORT.md"; \
			echo "📋 Report includes: benchmark data, system info, statistics, and plots"; \
		else \
			echo "⚠️  scripts/generate_report.py not found"; \
		fi \
	else \
		echo "⚠️  No results found for machine: $(MACHINE_ID)"; \
		echo "     Expected directory: $$machine_results_dir"; \
	fi

# Display current system information
system-info:
	@echo "🖥️  System Information:"
	@echo "======================"
	@if command -v fastfetch >/dev/null 2>&1; then \
		fastfetch --logo none -s CPU:CPUCache:GPU:Kernel:OS:Host:Memory:PhysicalMemory 2>/dev/null; \
	else \
		echo "⚠️  fastfetch not found - please install fastfetch"; \
	fi

# Clean all results
clean-results:
	@echo "🧹 Cleaning benchmark results..."
	@if [ -d "results" ]; then \
		read -p "Are you sure you want to delete all results? [y/N] " -n 1 -r; \
		echo; \
		if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
			rm -rf results/; \
			echo "✅ All results cleaned"; \
		else \
			echo "❌ Cleaning cancelled"; \
		fi \
	else \
		echo "ℹ️  No results directory found"; \
	fi
