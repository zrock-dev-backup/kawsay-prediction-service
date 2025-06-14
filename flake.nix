# flake.nix
{
  description = "Development environment for the Kawsay Prediction Service";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        pythonVersion = pkgs.python311;
      in
      {
        devShells.default = pkgs.mkShell {
          name = "kawsay-prediction-service";
          buildInputs = [
            pythonVersion
            pkgs.poetry
          ];

          shellHook = ''
            echo "Welcome to the Kawsay Prediction Service environment!"
            echo "Run 'poetry install' to set up your Python dependencies."
            export PYTHONPATH=$PYTHONPATH:$(pwd)/src
          '';
        };
      });
}
