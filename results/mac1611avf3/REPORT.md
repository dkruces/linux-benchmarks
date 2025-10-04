# MAC1611AVF3 Benchmark Report

Comprehensive benchmark results for machine **mac1611avf3**.

Generated on: 2025-10-04 21:20:02

## Architecture: arm64

### Kernel Version v6.16.0

#### GCC Compiler Results

## Ebpf-Ready Configuration

### System Information

- **CPU**: Virtualized Apple Silicon (8)
- **GPU**: Mesa llvmpipe (LLVM 19.1.7, 128 bits)
- **Kernel**: Linux 6.16.9+deb14-cloud-arm64
- **OS**: Debian GNU/Linux forky/sid aarch64
- **Host**: Apple Virtualization Generic Platform (1)
- **Memory**: 1.05 GiB / 15.60 GiB (7%)
- **Build Environment**: 
- **Machine Architecture**: aarch64
- **Kernel Architecture**: arm64
- **Compiler**: GCC
- **LLVM Flag**: 
- **Reproducible Builds**: Enabled
- **KBUILD_BUILD_TIMESTAMP**: 1991-08-25
- **KBUILD_BUILD_USER**: user
- **KBUILD_BUILD_HOST**: host
- **KCFLAGS**: -fdebug-prefix-map=/home/dagomez.linux/src/kernel/linux=/usr/src/linux
- **Make Threads**: 8-8 (step: 8)
- **Benchmark Runs**: 3
- **Warmup Runs**: 1
- **Kernel Source**: /home/dagomez.linux/src/kernel/linux
- **Config Fragments**: /home/dagomez.linux/src/linux-config-fragments
- **Machine ID**: mac1611avf3
- **Kernel Version**: v6.16.0
- **Build Date**: 2025-10-04 21:09:04 CEST
- **GCC Version**: gcc (Debian 15.2.0-4) 15.2.0
- **Clang Version**: Debian clang version 19.1.7 (3+b2)

### Benchmark Results Summary

| Command | Mean (s) | Std Dev (s) | Min (s) | Max (s) | Runs |
|---------|----------|-------------|---------|---------|------|
| `make -j8` | 84.375 | 0.509 | 84.031 | 84.960 | 3 |

### Advanced Statistics

```
Command 'make  -j8'
  runs:          3
  mean:     84.375 s
  stddev:    0.509 s
  median:   84.135 s
  min:      84.031 s
  max:      84.960 s

  percentiles:
     P_05 .. P_95:    84.041 s .. 84.878 s
     P_25 .. P_75:    84.083 s .. 84.547 s  (IQR = 0.465 s)
```


## Minimal Configuration

### System Information

- **CPU**: Virtualized Apple Silicon (8)
- **GPU**: Mesa llvmpipe (LLVM 19.1.7, 128 bits)
- **Kernel**: Linux 6.16.9+deb14-cloud-arm64
- **OS**: Debian GNU/Linux forky/sid aarch64
- **Host**: Apple Virtualization Generic Platform (1)
- **Memory**: 913.89 MiB / 15.60 GiB (6%)
- **Build Environment**: 
- **Machine Architecture**: aarch64
- **Kernel Architecture**: arm64
- **Compiler**: GCC
- **LLVM Flag**: 
- **Reproducible Builds**: Enabled
- **KBUILD_BUILD_TIMESTAMP**: 1991-08-25
- **KBUILD_BUILD_USER**: user
- **KBUILD_BUILD_HOST**: host
- **KCFLAGS**: -fdebug-prefix-map=/home/dagomez.linux/src/kernel/linux=/usr/src/linux
- **Make Threads**: 8-8 (step: 8)
- **Benchmark Runs**: 3
- **Warmup Runs**: 1
- **Kernel Source**: /home/dagomez.linux/src/kernel/linux
- **Config Fragments**: /home/dagomez.linux/src/linux-config-fragments
- **Machine ID**: mac1611avf3
- **Kernel Version**: v6.16.0
- **Build Date**: 2025-10-04 21:04:19 CEST
- **GCC Version**: gcc (Debian 15.2.0-4) 15.2.0
- **Clang Version**: Debian clang version 19.1.7 (3+b2)

### Benchmark Results Summary

| Command | Mean (s) | Std Dev (s) | Min (s) | Max (s) | Runs |
|---------|----------|-------------|---------|---------|------|
| `make -j8` | 63.413 | 0.929 | 62.648 | 64.447 | 3 |

### Advanced Statistics

```
Command 'make  -j8'
  runs:          3
  mean:     63.413 s
  stddev:    0.929 s
  median:   63.145 s
  min:      62.648 s
  max:      64.447 s

  percentiles:
     P_05 .. P_95:    62.697 s .. 64.317 s
     P_25 .. P_75:    62.896 s .. 63.796 s  (IQR = 0.900 s)
```

