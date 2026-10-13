# This file is SOOO AI generated
# i have no idea what i'm doing

# NixOS / home-manager module for steam-presence.
# flake.nix imports this with the flake itself (`self`) so the module can
# default to the flake's own package.
{ self }:
{ config, lib, pkgs, ... }:

let
  cfg = config.services.steam-presence;
  jsonFormat = pkgs.formats.json { };
in
{
  options.services.steam-presence = {
    enable = lib.mkEnableOption "steam-presence (Discord Rich Presence for Steam, Last.fm, Jellyfin, MPD and local games)";

    package = lib.mkOption {
      type = lib.types.package;
      default = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      defaultText = lib.literalExpression "steam-presence.packages.\${pkgs.stdenv.hostPlatform.system}.default";
      description = "The steam-presence package to run.";
    };

    settings = lib.mkOption {
      type = jsonFormat.type;
      default = { };
      description = ''
        Configuration for steam-presence, written to a JSON file and passed
        to the daemon via `--config`. You only need to list what you want to
        override — everything else falls back to the defaults in
        `src/steam_presence/config.py`.

        Top-level sections: `app`, `discord`, `steam_grid_db`, `steam`,
        `epic_games_store`, `jellyfin`, `local`, `mpd`, `last_fm`.

        Note: this ends up in the world-readable Nix store. If it contains
        API keys you don't want other local users to read, use `configFile`
        (e.g. via sops-nix/agenix) instead.
      '';
      example = lib.literalExpression ''
        {
          app.presedence_rules.mpd = "last_fm";
          discord.enabled = true;
          steam = {
            enabled = true;
            users = [ { api_key = "…"; user_id = 123; } ];
          };
          local = {
            enabled = true;
            processes = [ { process_name = "AppRun"; display_name = "Ship of Harkinian"; } ];
          };
          mpd = { enabled = true; catbox = true; uguu = true; };
        }
      '';
    };

    configFile = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      description = ''
        Use an existing JSON config file instead of `settings`.
        Takes precedence over `settings` when set.

        Useful for secrets (e.g. a sops-nix/agenix secret path) or for a
        mutable file — the config is re-read on every cycle, so edits take
        effect without a restart or rebuild.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    # Runs as a systemd *user* service: pypresence talks to Discord over
    # the IPC socket in $XDG_RUNTIME_DIR, so it must run in the same user
    # session as the Discord client.
    systemd.user.services.steam-presence = {
      Unit = {
        Description = "steam-presence — Discord Rich Presence daemon";
        After = [ "graphical-session.target" ];
      };

      Service = {
        ExecStart = "${lib.getExe cfg.package} --config ${
          lib.escapeShellArg (
            if cfg.configFile != null
            then toString cfg.configFile
            else jsonFormat.generate "steam-presence-config.json" cfg.settings
          )
        }";
        Environment = [ "PYTHONUNBUFFERED=1" ];
        Restart = "on-failure";
        RestartSec = 60;
      };

      Install.WantedBy = [ "default.target" ];
    };
  };
}
