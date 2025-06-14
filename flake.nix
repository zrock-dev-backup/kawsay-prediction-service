{
  description = "Kawsay Prediction Service: Development Shell and Runnable App";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # Create poetry2nix instance
        p2nix = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };
        inherit (p2nix) mkPoetryApplication mkPoetryEnv defaultPoetryOverrides;
        
        # Use python311 but make it easier to change if needed
        python = pkgs.python311;
        
        # Build the application package from poetry.lock
        kawsay-predictor-pkg = mkPoetryApplication {
          projectDir = self;
          inherit python;
          
          # Add common overrides for Python packages that often have build issues
          overrides = defaultPoetryOverrides.extend (final: prev: {
            # Fix fastapi-cli build issue with uvicorn optional dependencies
            fastapi-cli = prev.fastapi-cli.overridePythonAttrs (old: {
              buildInputs = (old.buildInputs or []) ++ [ pkgs.python311Packages.setuptools ];
              # Remove the problematic uvicorn optional-dependencies reference
              postPatch = (old.postPatch or "") + ''
                substituteInPlace setup.py --replace 'uvicorn[standard]' 'uvicorn' || true
              '';
            });
            
            # Ensure uvicorn has the attributes that might be expected
            uvicorn = prev.uvicorn.overridePythonAttrs (old: {
              # Add optional-dependencies as an empty set if it doesn't exist
              passthru = (old.passthru or {}) // {
                optional-dependencies = {
                  standard = [];
                };
              };
            });
          });
          
          # Ensure we can find the src directory
          postInstall = ''
            # Make sure the application can find its modules
            export PYTHONPATH=$out/lib/python*/site-packages:$PYTHONPATH
          '';
        };

        # Create a development environment with poetry
        devEnv = mkPoetryEnv {
          projectDir = self;
          inherit python;
        };

      in {
        # Package output - the built application
        packages = {
          default = kawsay-predictor-pkg;
          kawsay-predictor = kawsay-predictor-pkg;
        };

        # Runnable application
        apps = {
          default = {
            type = "app";
            # Use python -m uvicorn to avoid fastapi-cli issues
            program = "${pkgs.writeShellScript "kawsay-run" ''
              export PYTHONPATH=${kawsay-predictor-pkg}/lib/python*/site-packages
              cd ${kawsay-predictor-pkg}
              exec ${kawsay-predictor-pkg}/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
            ''}";
          };
          
          # Alternative: try to use uvicorn binary directly if available
          uvicorn = {
            type = "app";
            program = "${pkgs.writeShellScript "kawsay-uvicorn" ''
              export PYTHONPATH=${kawsay-predictor-pkg}/lib/python*/site-packages
              if [ -f "${kawsay-predictor-pkg}/bin/uvicorn" ]; then
                exec ${kawsay-predictor-pkg}/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
              else
                cd ${kawsay-predictor-pkg}
                exec ${kawsay-predictor-pkg}/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
              fi
            ''}";
          };
        };

        # Development shell
        devShells.default = pkgs.mkShell {
          name = "kawsay-prediction-service-dev";
          
          buildInputs = [
            python
            pkgs.poetry
            # Add any additional development tools here
            pkgs.curl  # for testing the API
          ];
          
          # Include the poetry environment
          inputsFrom = [ devEnv ];
          
          shellHook = ''
            echo "🚀 Welcome to the Kawsay Prediction Service dev environment!"
            echo ""
            echo "Available commands:"
            echo "  poetry install    - Install/update dependencies"
            echo "  poetry run ...    - Run commands in the poetry environment"
            echo "  nix run          - Run the production build"
            echo "  nix run .#serve  - Alternative run method"
            echo ""
            
            # Set up Python path for development
            export PYTHONPATH=$PWD/src:$PYTHONPATH
            
            # Show current Python and Poetry versions
            echo "Python: $(python --version)"
            echo "Poetry: $(poetry --version)"
          '';
        };

        # Optional: Add additional development shells
        devShells.minimal = pkgs.mkShell {
          name = "kawsay-minimal-dev";
          buildInputs = [ python ];
          shellHook = ''
            echo "Minimal Python environment loaded"
            export PYTHONPATH=$PWD/src:$PYTHONPATH
          '';
        };
      });
}
