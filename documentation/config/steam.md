|Variable|Type|Default|Comment|
|-|-|-|-|
|enabled|bool|False|Weather or not to enable steam|
|users|list[SteamUser]|[]|List of users to check|
|discord_fallback_app_id|int|1400020030565122139|this is _NOT_ your user ID, see [discord's dev portal](https://discord.com/developers/applications)|

### example of a steam entry

```json
"steam": {
    "enabled": true,
    "users": [
        {
            "api_key": "REDACTED",
            "user_id": 123456789
        }
    ]
},
```

### api key

visit https://steamcommunity.com/dev/apikey to obtain an api key


### steam user

```py
class SteamUser:
    api_key: str = ""
    user_id: int = 0
```
