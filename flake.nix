{
  description = "steam-presence — Discord Rich Presence for Steam, Last.fm, Jellyfin, MPD and local games";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      lib = nixpkgs.lib;

      # (nixpkgs currently ships 4.6.1 change to nix when
      #  that updates and just use ps.pypresence)
      mkPypresence = pkgs: pkgs.python3Packages.buildPythonPackage rec {
        pname = "pypresence";
        version = "4.6.2";
        pyproject = true;

        src = pkgs.fetchPypi {
          inherit pname version;
          sha256 = "7e7e93de0e94a42314300ef6d15dd2c44c64ef74b7c749243bc226be2ab90687";
        };

        build-system = [ pkgs.python3Packages.setuptools ];

        doCheck = false; # upstream tests need network access
        pythonImportsCheck = [ "pypresence" ];

        meta = {
          description = "Discord RPC client written in Python";
          homepage = "https://github.com/qwertyquerty/pypresence";
          license = lib.licenses.mit;
        };
      };

      # make sure this matches requirements.txt
      mkPythonEnv = pkgs: pkgs.python3.withPackages (ps: [
        ps.beautifulsoup4
        ps.requests
        ps.pillow
        ps.mutagen
        ps.psutil
        (mkPypresence pkgs)
      ]);

      mkSteamPresence = pkgs:
        let
          pythonEnv = mkPythonEnv pkgs;
        in
        pkgs.stdenvNoCC.mkDerivation {
          pname = "steam-presence";
          version = "0.1.0";

          src = lib.cleanSource ./.;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          dontConfigure = true;
          dontBuild = true;

          installPhase = ''
            runHook preInstall

            mkdir -p $out/share/steam-presence
            cp -r main.py src $out/share/steam-presence/

            makeWrapper ${pythonEnv}/bin/python3 $out/bin/steam-presence \
              --add-flags "$out/share/steam-presence/main.py" \
              --prefix PYTHONPATH : "$out/share/steam-presence:${pythonEnv}/${pkgs.python3.sitePackages}"

            runHook postInstall
          '';

          meta = {
            description = "Discord Rich Presence for Steam, Last.fm, Jellyfin, MPD and local games";
            mainProgram = "steam-presence";
            license = lib.licenses.gpl3;
          };
        };
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        steam-presence = mkSteamPresence pkgs;
      in
      {
        packages = {
          inherit steam-presence;
          default = steam-presence;
        };

        apps.default = flake-utils.lib.mkApp { drv = steam-presence; };

        devShells.default = pkgs.mkShell {
          packages = [ (mkPythonEnv pkgs) ];
          shellHook = ''
            echo "run: python main.py --config ./config.json"
          '';
        };
      })
    // {
      nixosModules.default = import ./nix/steam-presence.nix { inherit self; };
      nixosModules.steam-presence = import ./nix/steam-presence.nix { inherit self; };
      homeManagerModules.default = import ./nix/steam-presence.nix { inherit self; };
      homeManagerModules.steam-presence = import ./nix/steam-presence.nix { inherit self; };
    };
}
