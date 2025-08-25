{
  description = "Linux kernel benchmarking environment with hyperfine and analysis tools";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python environment for analysis scripts
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          matplotlib
          numpy
          scipy
        ]);

        # Kernel build essentials
        kernelBuildInputs = with pkgs; [
          # Core build tools
          gnumake
          gcc
          binutils
          flex
          bison
          
          # Kernel-specific tools
          bc
          elfutils
          openssl
          perl
          python3
          rsync
          
          # Additional utilities that may be needed
          gmp
          libmpc
          mpfr
          zlib
          ncurses
          
          # For LLVM builds (LLVM=1 flag support)
          llvm
          clang
          lld
        ];

      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Core benchmarking tools
            hyperfine
            
            # System information
            fastfetch
            
            # Download tools
            curl
            wget
            
            # Python environment manager and environment
            uv
            pythonEnv
            
            # Standard shell tools
            gnumake
            coreutils
            findutils
            
            # Optional: Git for version control
            git
            
            # Text editors
            helix
            vim
            
          ] ++ kernelBuildInputs;

          shellHook = ''
            echo "🚀 Linux Kernel Benchmarking Environment"
            echo "========================================"
            echo ""
            echo "Available tools:"
            echo "  hyperfine      - $(hyperfine --version | head -1)"
            echo "  fastfetch      - $(fastfetch --version 2>/dev/null | head -1 || echo 'available')"
            echo "  python3        - $(python3 --version)"
            echo "  uv             - $(uv --version)"
            echo "  make           - $(make --version | head -1)"
            echo "  gcc            - $(gcc --version | head -1)"
            echo "  clang          - $(clang --version | head -1)"
            echo "  helix          - $(hx --version | head -1)"
            echo "  vim            - $(vim --version | head -1)"
            echo ""
            echo "Quick start:"
            echo "  make help           # Show available benchmark targets"
            echo "  make system-info    # Display system information"  
            echo "  make setup-scripts  # Download analysis scripts"
            echo "  make minimal        # Run minimal kernel benchmark"
            echo ""
            echo "Configuration:"
            echo "  KERNEL_SOURCE=\$HOME/src/kernel/linux"
            echo "  CONFIG_FRAGMENTS=\$HOME/src/linux-config-fragments"
            echo ""
          '';

          # Environment variables
          KERNEL_SOURCE = "/home/dagomez/src/kernel/linux";
          CONFIG_FRAGMENTS = "/home/dagomez/src/linux-config-fragments";
          
          # Ensure Python scripts can find matplotlib
          PYTHONPATH = "${pythonEnv}/${pythonEnv.sitePackages}";
        };

        # Alternative shells for different use cases
        devShells.minimal = pkgs.mkShell {
          buildInputs = with pkgs; [
            hyperfine
            fastfetch  
            curl
            gnumake
            pythonEnv
            uv
          ];
          
          shellHook = ''
            echo "📦 Minimal Linux Benchmarking Environment"
            echo "Basic tools for running benchmarks without kernel build dependencies"
          '';
        };

        devShells.analysis = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            uv
            curl
          ];
          
          shellHook = ''
            echo "📊 Analysis Environment"
            echo "Tools for analyzing existing benchmark results"
          '';
        };
      });
}