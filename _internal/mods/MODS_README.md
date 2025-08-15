# Better Minesweeper Modding Guide

## Getting Started

1. Extract each mod under `mods/<mod_name>`.
2. Enable the mod loader in the game options.
3. Use **Options → Mods** to choose load order.

## Folder Layout

```
mods/
└── my_mod/
    ├── mod.json
    ├── assets/
    │   ├── tilesets/
    │   ├── fonts/
    │   └── sounds/
    └── scripts/
        └── init.py
```

## Manifest (`mod.json`)

Required fields:
- `name`
- `version`
- `api_version`
- `namespace`

Optional fields:
- `description`
- `author`
- `permissions` (`COSMETIC`, `GAMEPLAY`, `SYSTEM`)
- `dependencies` with `REQUIRED`, `OPTIONAL`, `BEFORE`, or `AFTER`
- `load_priority` (lower numbers load first)

## Writing a Mod

Each mod exposes a class named `Mod`.
You may implement it directly or inherit from `mods.mod_api.ModAPI`.
Only `initialize()` and `cleanup()` are required.

```python
class Mod:
    def __init__(self, info):
        self.info = info
        self.namespace = info.namespace

    def initialize(self):
        pass

    def cleanup(self):
        pass
```

## Events

Register handlers with `register_event_handler(event, func, priority)`.
Priorities range from `EventPriority.HIGHEST` (0) to `EventPriority.LOWEST` (1000).
Common events are:
- `game.start`
- `game.end`
- `game.win`
- `game.lose`
- `game.reset`
- `game.tile.reveal`
- `game.tile.flag`
- `ui.render`

Emit events using `self.emit_event(name, data)`.

## Assets and Registries

Use helper functions to register assets:

```python
register_tileset("mytileset", {"path": path}, self.namespace)
register_font("myfont", {"path": font_path}, self.namespace)
```

Resolve paths with `get_tileset_path`, `get_font_path`, or `get_sound_path`.
Create additional registries via `registries.create_registry("name")`.

## Settings

Define settings through `register_mod_settings`:

```python
schema = {
    "option": {"default": True, "description": "Enable feature", "type": "user"}
}
register_mod_settings(self.namespace, schema)
```

Retrieve values with `get_setting('option')` and update them with
`set_setting('option', value)`.

## Hot Reloading

Call `reload_all_mods()` to reload every loaded mod during runtime.

## Examples

### Simple Mod

```python
from mods.mod_api import ModAPI, registries
from mods.mod_settings import register_mod_settings

class Mod(ModAPI):
    def initialize(self):
        self.register_event_handler("game.start", self.on_start)

        registries.register_tileset(
            "cool", {"path": self.get_asset_path("tilesets/cool.png")}, self.namespace
        )

        register_mod_settings(self.namespace, {
            "fancy": {"default": False, "description": "Enable fancy mode"}
        })

    def on_start(self, event):
        self.log("Game started")
```

See `mods/example_theme` for a practical sample mod.
