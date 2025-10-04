# MAC1611AVF2 Benchmark Report

Comprehensive benchmark results for machine **mac1611avf2**.

Generated on: 2025-10-04 21:04:06

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
- **Memory**: 959.59 MiB / 15.60 GiB (6%)
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
- **Benchmark Runs**: 1
- **Warmup Runs**: 1
- **Kernel Source**: /home/dagomez.linux/src/kernel/linux
- **Config Fragments**: /home/dagomez.linux/src/linux-config-fragments
- **Machine ID**: mac1611avf2
- **Kernel Version**: v6.16.0
- **Build Date**: 2025-10-04 20:54:35 CEST
- **GCC Version**: gcc (Debian 15.2.0-4) 15.2.0
- **Clang Version**: Debian clang version 19.1.7 (3+b2)

### Benchmark Results Summary

| Command | Mean (s) | Std Dev (s) | Min (s) | Max (s) | Runs |
|---------|----------|-------------|---------|---------|------|
| `make -j8` | 86.270 | 0.000 | 86.270 | 86.270 | 1 |

### Advanced Statistics

```
Command 'make  -j8'
  runs:          1
  mean:     86.270 s
  stddev:      nan s
  median:   86.270 s
  min:      86.270 s
  max:      86.270 s

  percentiles:
     P_05 .. P_95:    86.270 s .. 86.270 s
     P_25 .. P_75:    86.270 s .. 86.270 s  (IQR = 0.000 s)
```


## Minimal Configuration

### System Information

- **CPU**: Virtualized Apple Silicon (8)
- **GPU**: Mesa llvmpipe (LLVM 19.1.7, 128 bits)
- **Kernel**: Linux 6.16.9+deb14-cloud-arm64
- **OS**: Debian GNU/Linux forky/sid aarch64
- **Host**: Apple Virtualization Generic Platform (1)
- **Memory**: 881.92 MiB / 15.60 GiB (6%)
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
- **Benchmark Runs**: 1
- **Warmup Runs**: 1
- **Kernel Source**: /home/dagomez.linux/src/kernel/linux
- **Config Fragments**: /home/dagomez.linux/src/linux-config-fragments
- **Machine ID**: mac1611avf2
- **Kernel Version**: v6.16.0
- **Build Date**: 2025-10-04 20:33:36 CEST
- **GCC Version**: gcc (Debian 15.2.0-4) 15.2.0
- **Clang Version**: Debian clang version 19.1.7 (3+b2)

### Benchmark Results Summary

| Command | Mean (s) | Std Dev (s) | Min (s) | Max (s) | Runs |
|---------|----------|-------------|---------|---------|------|
| `make -j8` | 63.925 | 0.000 | 63.925 | 63.925 | 1 |

