# mod_api.py - Base API for mod development
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
from pathlib import Path

from .event_system import event_system, EventPriority, Event, event_handler
from .asset_manager import asset_manager
from .mod_manager import ModInfo

class ModAPI(ABC):
    """Base class for all mods."""
    
    def __init__(self, mod_info: ModInfo):
        self.mod_info = mod_info
        self.namespace = mod_info.namespace
        self.settings = {}
        self.event_handlers = []
        
    @abstractmethod
    def initialize(self):
        """Initialize the mod. Called when the mod is loaded."""
        pass
    
    def cleanup(self):
        """Clean up the mod. Called when the mod is unloaded."""
        # Unregister all event handlers
        for handler_info in self.event_handlers:
            event_system.unregister_handler(
                handler_info['event_name'], 
                handler_info['callback'], 
                self.namespace
            )
        self.event_handlers.clear()
    
    def register_event_handler(self, event_name: str, callback: Callable[[Event], None], 
                             priority: int = EventPriority.NORMAL):
        """Register an event handler."""
        success = event_system.register_handler(event_name, callback, priority, self.namespace)
        if success:
            self.event_handlers.append({
                'event_name': event_name,
                'callback': callback,
                'priority': priority
            })
        return success
    
    def emit_event(self, event_name: str, data: Dict[str, Any] = None) -> Event:
        """Emit an event."""
        return event_system.emit_event(event_name, data)
    
    def get_asset_path(self, asset_name: str) -> Optional[Path]:
        """Get path to an asset."""
        return asset_manager.get_asset_path(asset_name)
    
    def get_tileset_path(self, tileset_name: str = "default") -> Optional[Path]:
        """Get path to a tileset."""
        return asset_manager.get_tileset_path(tileset_name)
    
    def get_font_path(self, font_name: str = "default") -> Optional[Path]:
        """Get path to a font."""
        return asset_manager.get_font_path(font_name)
    
    def get_sound_path(self, sound_name: str) -> Optional[Path]:
        """Get path to a sound file."""
        return asset_manager.get_sound_path(sound_name)
    
    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Load a configuration file."""
        return asset_manager.load_config(config_name)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a mod setting."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a mod setting."""
        self.settings[key] = value
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        print(f"[{level}] {self.namespace}: {message}")
    
    def get_mod_path(self) -> Path:
        """Get the path to this mod's directory."""
        return self.mod_info.mod_path

class Registry:
    """Generic registry for mod content."""
    
    def __init__(self, name: str):
        self.name = name
        self.entries: Dict[str, Any] = {}
        self.mod_entries: Dict[str, List[str]] = {}  # mod_name -> [entry_keys]
    
    def register(self, key: str, value: Any, mod_name: str = "core") -> bool:
        """Register an entry."""
        if key in self.entries:
            print(f"Registry {self.name}: Key '{key}' already exists, overriding")
        
        self.entries[key] = value
        
        if mod_name not in self.mod_entries:
            self.mod_entries[mod_name] = []
        self.mod_entries[mod_name].append(key)
        
        return True
    
    def get(self, key: str) -> Any:
        """Get an entry."""
        return self.entries.get(key)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all entries."""
        return self.entries.copy()
    
    def unregister(self, key: str) -> bool:
        """Unregister an entry."""
        if key in self.entries:
            del self.entries[key]
            return True
        return False
    
    def unregister_mod_entries(self, mod_name: str):
        """Unregister all entries from a mod."""
        if mod_name in self.mod_entries:
            for key in self.mod_entries[mod_name]:
                if key in self.entries:
                    del self.entries[key]
            del self.mod_entries[mod_name]
    
    def list_keys(self) -> List[str]:
        """List all registered keys."""
        return list(self.entries.keys())

class ModRegistries:
    """Container for all mod registries."""
    
    def __init__(self):
        self.registries: Dict[str, Registry] = {}
        self._initialize_default_registries()
    
    def _initialize_default_registries(self):
        """Initialize default registries."""
        registry_names = [
            'tilesets', 'game_modes', 'themes', 'fonts', 'sounds',
            'difficulty_presets', 'tile_types', 'render_effects'
        ]
        
        for name in registry_names:
            self.registries[name] = Registry(name)
    
    def get_registry(self, name: str) -> Optional[Registry]:
        """Get a registry by name."""
        return self.registries.get(name)
    
    def create_registry(self, name: str) -> Registry:
        """Create a new registry."""
        if name in self.registries:
            return self.registries[name]
        
        registry = Registry(name)
        self.registries[name] = registry
        return registry
    
    def register_tileset(self, key: str, tileset_info: Dict[str, Any], mod_name: str = "core"):
        """Register a tileset."""
        return self.registries['tilesets'].register(key, tileset_info, mod_name)
    
    def register_game_mode(self, key: str, mode_info: Dict[str, Any], mod_name: str = "core"):
        """Register a game mode."""
        return self.registries['game_modes'].register(key, mode_info, mod_name)
    
    def register_theme(self, key: str, theme_info: Dict[str, Any], mod_name: str = "core"):
        """Register a theme."""
        return self.registries['themes'].register(key, theme_info, mod_name)

    def register_font(self, key: str, font_info: Dict[str, Any], mod_name: str = "core"):
        """Register a font."""
        return self.registries['fonts'].register(key, font_info, mod_name)
    
    def get_tileset(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a tileset."""
        return self.registries['tilesets'].get(key)
    
    def get_game_mode(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a game mode."""
        return self.registries['game_modes'].get(key)
    
    def get_theme(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a theme."""
        return self.registries['themes'].get(key)

    def get_font(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a font."""
        return self.registries['fonts'].get(key)
    
    def unregister_mod_content(self, mod_name: str):
        """Unregister all content from a mod."""
        for registry in self.registries.values():
            registry.unregister_mod_entries(mod_name)

# Global registries instance
registries = ModRegistries()

# Convenience functions for mod developers
def register_tileset(key: str, tileset_info: Dict[str, Any], mod_name: str = "core"):
    """Register a tileset."""
    return registries.register_tileset(key, tileset_info, mod_name)

def register_game_mode(key: str, mode_info: Dict[str, Any], mod_name: str = "core"):
    """Register a game mode."""
    return registries.register_game_mode(key, mode_info, mod_name)

def register_theme(key: str, theme_info: Dict[str, Any], mod_name: str = "core"):
    """Register a theme."""
    return registries.register_theme(key, theme_info, mod_name)

def register_font(key: str, font_info: Dict[str, Any], mod_name: str = "core"):
    """Register a font."""
    return registries.register_font(key, font_info, mod_name)

def get_tileset(key: str) -> Optional[Dict[str, Any]]:
    """Get a tileset."""
    return registries.get_tileset(key)

def get_game_mode(key: str) -> Optional[Dict[str, Any]]:
    """Get a game mode."""
    return registries.get_game_mode(key)

def get_theme(key: str) -> Optional[Dict[str, Any]]:
    """Get a theme."""
    return registries.get_theme(key)

def get_font(key: str) -> Optional[Dict[str, Any]]:
    """Get a font."""
    return registries.get_font(key)
