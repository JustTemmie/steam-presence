{
  description = "A Nix flake for steam-presence";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {inherit system;};

      steam-presence-src = pkgs.lib.cleanSource ./.;

      steam-presence-pkg = pkgs.callPackage ./nix/pkgs/steam-presence {
        src = steam-presence-src;
      };
    in {
      packages = {
        steam-presence = steam-presence-pkg;
        default = steam-presence-pkg;
      };

      apps = {
        steam-presence = {
          type = "app";
          program = "${steam-presence-pkg}/bin/steam-presence";
        };
        default = {
          type = "app";
          program = "${steam-presence-pkg}/bin/steam-presence";
        };
      };
    })
    // {
      nixosModules = {
        steam-presence = import ./nix/nixos-modules/steam-presence.nix;
      };
    };
}
