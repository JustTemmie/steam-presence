requires python 3.11+

# Steam Presence

A program used to display what you're playing on discord.

![GitHub last commit](https://img.shields.io/github/last-commit/justtemmie/steam-presence)
![visitors](https://visitor-badge.laobi.icu/badge?page_id=justtemmie.steam-presence)
[![License](https://shields.io/github/license/justtemmie/steam-presence?color=purple)](https://www.gnu.org/licenses/gpl-3.0-standalone.html)



<details open>
<summary><h2>Preview and Preamble</h2></summary>

### Preview

![discord profile playing BTD6](https://github.com/user-attachments/assets/79e44ebe-ebd8-4b13-9a22-d902104aa2c9)

Profile whilst playing "BTD6" 

### Features

...

### Why??

...

### Requirements

 - Python 3.11 or higher
 - Python pip installed
 - a verified steam account (requires your account to have spent 5 USD on games)
 - your steam account must be online in order to detect your current game

</details>



<details open>
<summary><h2>Installation</h2></summary>

<details>
<summary><h3>NixOS</h3></summary>

Add `steam-presence.url = "github:JustTemmie/steam-presence/steam-presence-v2";` to your flake inputs.

Add EITHER of the modules `inputs.steam-presence.steam-presence.default` or `inputs.steam-presence.homeManagerModules.default`

Enable `services.steam-presence` with the corresponding settings

Reference implementation (mine):

- [flake.nix](https://codeberg.org/Twig/NixOS-Dotfiles/src/branch/main/flake.nix)
- [home manager configuration](https://codeberg.org/Twig/NixOS-Dotfiles/src/branch/main/home/users/twig/steam-presence.nix)

</details>

<details>
<summary><h3>Other Linux</h3></summary>

can someone help

</details>

<details>
<summary><h3>MacOS</h3></summary>

i have no idea

</details>

<details>
<summary><h3>Windows</h3></summary>

could theoretically be done

</details>

</details>



<details open>
<summary><h2>Configuration</h2></summary>

Steam Presence will by default look for a file named config.json in the current path. Path can be overwritten with the --config argument.

Below is each entries default config data

<details open>
<summary><h3>Steam Config (Recommended)</h3></summary>

<h4>Required values</h4>

```jsonc
// set this to true
"enabled": false
// see SteamUser for more info
"users": [] 
```

<h4>Optional settings</h4>

```jsonc
// I don't recommend changing
"cooldown": 25
// power users only, see code for implementation details 
"inject_discord_status_data": true

// see DiscordData for more info
"discord_status_data": {
    "status_lines": [
        "{steam.rich_presence}",
        "{steam.app_playtime} hours on record",
        "{steam.review_description} ({steam.review_percent}%)",
    ],
    "buttons": [
        {
            "url": "https://store.steampowered.com/app/{steam.app_id}",
            "label": "on steam! – {steam.price_formatted}"
        }
    ]
}
```
</details>

<details>
<summary><h3>Steam Grid DB Config</h3></summary>

...

</details>

<details>
<summary><h3>App Config</h3></summary>

...

</details>

<details>
<summary><h3>Local Config</h3></summary>

...

</details>

<details>
<summary><h3>MPD Config</h3></summary>

...

</details>

</details>

