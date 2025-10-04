#!/bin/bash
# migrate_arch.sh - Add architecture level to existing results directory structure
#
# Transforms:
#   results/{machine}/{version}/{compiler}/{config}/
# Into:
#   results/{machine}/{arch}/{version}/{compiler}/{config}/

set -eo pipefail

# Detect architecture from system
MACHINE_ARCH=$(uname -m)

# Map uname -m to kernel architecture names
case "$MACHINE_ARCH" in
    x86_64)  KERNEL_ARCH="x86_64" ;;
    aarch64) KERNEL_ARCH="arm64" ;;
    armv7l)  KERNEL_ARCH="arm" ;;
    ppc64le) KERNEL_ARCH="powerpc" ;;
    *)       KERNEL_ARCH="$MACHINE_ARCH" ;;
esac

# Allow override via argument
if [ $# -eq 1 ]; then
    KERNEL_ARCH="$1"
fi

echo "🔄 Migrating results to include architecture layer"
echo "   Architecture: $KERNEL_ARCH (detected from: $MACHINE_ARCH)"
echo ""

# Check if results directory exists
if [ ! -d "results" ]; then
    echo "❌ Error: results/ directory not found"
    exit 1
fi

# Track statistics
MIGRATED=0
SKIPPED=0
ERRORS=0

# Process each machine directory
for machine_dir in results/*/; do
    [ -d "$machine_dir" ] || continue

    machine_name=$(basename "$machine_dir")

    # Skip if already has architecture directories
    if [ -d "$machine_dir/$KERNEL_ARCH" ] || [ -d "$machine_dir/x86_64" ] || [ -d "$machine_dir/arm64" ]; then
        echo "⏭️  Skipping $machine_name - already has architecture directories"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Check if there are kernel version directories (start with 'v')
    # Disable errexit temporarily for this check
    set +e
    ls -d "$machine_dir"/v* >/dev/null 2>&1
    has_kernel_dirs=$?
    set -e

    if [ $has_kernel_dirs -ne 0 ]; then
        echo "⏭️  Skipping $machine_name - no kernel version directories found"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "📦 Migrating $machine_name..."

    # Create architecture directory
    mkdir -p "$machine_dir/$KERNEL_ARCH"

    # Move each kernel version directory
    for kernel_dir in "$machine_dir"/v*; do
        [ -d "$kernel_dir" ] || continue
        kernel_version=$(basename "$kernel_dir")

        echo "   → Moving $kernel_version to $KERNEL_ARCH/"

        if mv "$kernel_dir" "$machine_dir/$KERNEL_ARCH/"; then
            MIGRATED=$((MIGRATED + 1))
        else
            echo "   ❌ Failed to move $kernel_version"
            ERRORS=$((ERRORS + 1))
        fi
    done

    # Archive old REPORT.md if exists
    if [ -f "$machine_dir/REPORT.md" ]; then
        echo "   📄 Archiving old REPORT.md"
        mv "$machine_dir/REPORT.md" "$machine_dir/REPORT.md.pre-arch-migration"
    fi

    echo "   ✅ Completed $machine_name"
    echo ""
done

echo ""
echo "📊 Migration Summary:"
echo "   Machines migrated: $MIGRATED"
echo "   Machines skipped:  $SKIPPED"
echo "   Errors:            $ERRORS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ Migration completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify structure: ls -la results/*/"
    echo "  2. Regenerate reports: make report"
    echo "  3. Test new benchmarks: make minimal"
else
    echo "⚠️  Migration completed with errors"
    exit 1
fi
