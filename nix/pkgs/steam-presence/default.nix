{
  lib,
  stdenv,
  makeWrapper,
  src,
  python3,
  python3Packages,
  fetchPypi,
  bash,
  coreutils,
}: let
  python-steamgriddb = python3Packages.buildPythonPackage rec {
    pname = "python-steamgriddb";
    version = "1.0.5";
    src = fetchPypi {
      inherit pname version;
      hash = "sha256-A223uwmGXac7QLaM8E+5Z1zRi0kIJ1CS2R83vxYkUGk=";
    };
    pyproject = true;
    build-system = [python3Packages.setuptools];
    propagatedBuildInputs = [
      python3Packages.requests
    ];
    doCheck = false;
  };

  pythonEnv = python3.withPackages (ps: [
    ps.requests
    ps.beautifulsoup4
    ps.pypresence
    ps.psutil
    python-steamgriddb
  ]);
in
  stdenv.mkDerivation {
    pname = "steam-presence";
    version = "1.12.2";

    inherit src;
    nativeBuildInputs = [
      makeWrapper
    ];
    installPhase = ''
      runHook preInstall
      mkdir -p $out/share/steam-presence
      cp -r ./* $out/share/steam-presence

      mkdir -p $out/bin
      cat > $out/bin/steam-presence <<'EOF'
      #!${bash}/bin/bash
      set -eo pipefail

      # Determine runtime directory (env overrides default)
      RUNTIME_DIR="''${STEAM_PRESENCE_RUNTIME_DIR:-$HOME/.local/state/steam-presence}"

      # Store app dir (where upstream sources live)
      STORE_APP_DIR="$out/share/steam-presence"

      # Ensure runtime dir exists and seed it if main.py is missing
      if [ ! -f "$RUNTIME_DIR/main.py" ]; then
        ${coreutils}/bin/mkdir -p "$RUNTIME_DIR"
        ${coreutils}/bin/cp -r "$STORE_APP_DIR/." "$RUNTIME_DIR/"
      fi

      cd "$RUNTIME_DIR"
      exec ${pythonEnv}/bin/python "main.py"
      EOF
      chmod +x $out/bin/steam-presence

      runHook postInstall
    '';
    meta = with lib; {
      description = "A simple script to fetch a Steam user's current game and related info, and display it as a Discord rich presence";
      homepage = "https://github.com/JustTemmie/steam-presence";
      license = licenses.mit;
      maintainers = with maintainers; [];
      mainProgram = "steam-presence";
      platforms = platforms.linux;
    };
  }
