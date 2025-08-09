|Variable|Type|Default|Comment|
|-|-|-|-|
|enabled|bool|True|Whether or not to enable discord integration, disabling this kinda kills the purpose of the program|
|fallback_app_id|int|1400019956321620069|this is _NOT_ your user ID, see [discord's dev portal](https://discord.com/developers/applications) 
|custom_app_ids|dict[str, int]|{"App name here": 141471589572411256163}|List of custom app IDs, see [discord's dev portal](https://discord.com/developers/applications). Case insensitive check
|playing|DiscordData|See below|
|per_app|dict[str, DiscordData]|See below|

```py
class DiscordData:
  status_lines: list[]
  small_images: dict[str, str]
  large_images: dict[str, str]
```

### the defaults of the "playing" field
```json
{
  "status_lines": [
    "{default.details}",
    "{default.state}",
    "{steam.rich_presence}",
    "{steam.review_description} reviews ({steam.review_percent}%)",
  ],
  "small_images": {

  },
  "large_images": {
    "{discord.image_url}": null,
    "{steam_grid_db.icon}": null,
    "{steam.capsule_header_image}": null,
    "{steam.capsule_vertical_image}": null,
  }
}
```

### the defaults of the "per-app" field
```json
{
  "Trackmania": {
    "large_images": {
      "https://img.icons8.com/?size=256&id=LJEz2yMtDm2f": null,
    },
  },
}
```