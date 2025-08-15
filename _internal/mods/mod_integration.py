# mod_integration.py - Integration layer between mod manager and game
"""
This module provides integration between the mod manager and the core game.
It handles initialization, event routing, and provides a clean interface
for the game to interact with mods.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

class ModSystemIntegration:
    """Main integration class for the mod manager."""
    
    def __init__(self):
        self.mod_manager = None
        self.event_system = None
        self.asset_manager = None
        self.mod_settings = None
        self.registries = None
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize the mod manager."""
        try:
            # Import mod manager components
            from mods.mod_manager import mod_manager
            from mods.event_system import event_system
            from mods.asset_manager import asset_manager
            from mods.mod_settings import mod_settings
            from mods.mod_api import registries
            
            self.mod_manager = mod_manager
            self.event_system = event_system
            self.asset_manager = asset_manager
            self.mod_settings = mod_settings
            self.registries = registries
            
            # Connect systems
            mod_manager.event_system = event_system
            mod_manager.asset_manager = asset_manager
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize mod manager: {e}")
            return False
    
    def discover_and_load_mods(self) -> Dict[str, bool]:
        """Discover mods and load only enabled ones."""
        if not self.initialized:
            return {}
        
        try:
            # Discover mods
            discovered = self.mod_manager.discover_mods()
            print(f"Discovered {len(discovered)} mods")
            
            # Load only enabled mods respecting saved order
            results = self.mod_manager.load_all_mods()

            loaded_count = sum(1 for success in results.values() if success)
            print(f"Loaded {loaded_count}/{len(results)} mods")

            return results
            
        except Exception as e:
            print(f"Error during mod loading: {e}")
            return {}
    
    def reload_mods_with_new_config(self) -> Dict[str, bool]:
        """Reload mods with current configuration (hot-reload)."""
        if not self.initialized:
            return {}
        
        try:
            # Unload all current mods
            self.mod_manager.unload_all_mods()
            
            # Re-discover mods in case new ones were added
            self.mod_manager.discover_mods(force_refresh=True)
            
            # Load mods with current enabled list
            results = self.mod_manager.load_all_mods()
            
            loaded_count = sum(1 for success in results.values() if success)
            print(f"Hot-reload complete: {loaded_count}/{len(results)} mods loaded")
            
            return results
            
        except Exception as e:
            print(f"Error during hot-reload: {e}")
            return {}
    
    def emit_game_event(self, event_name: str, data: Dict[str, Any] = None):
        """Emit a game event for mods to handle."""
        if self.initialized and self.event_system:
            try:
                self.event_system.emit_event(event_name, data or {})
            except Exception as e:
                print(f"Error emitting event {event_name}: {e}")
    
    def get_asset_path(self, asset_name: str) -> Optional[Path]:
        """Get path to an asset, considering mod overrides."""
        if self.initialized and self.asset_manager:
            try:
                return self.asset_manager.get_asset_path(asset_name)
            except Exception as e:
                print(f"Error getting asset {asset_name}: {e}")
        return None
    
    def get_tileset_path(self, tileset_name: str = "default") -> Optional[Path]:
        """Get path to a tileset."""
        if self.initialized and self.asset_manager:
            try:
                return self.asset_manager.get_tileset_path(tileset_name)
            except Exception as e:
                print(f"Error getting tileset {tileset_name}: {e}")
        return None
    
    def get_font_path(self, font_name: str = "default") -> Optional[Path]:
        """Get path to a font."""
        if self.initialized and self.asset_manager:
            try:
                return self.asset_manager.get_font_path(font_name)
            except Exception as e:
                print(f"Error getting font {font_name}: {e}")
        return None
    
    def cleanup(self):
        """Clean up the mod manager."""
        if self.initialized:
            try:
                # Save settings
                if self.mod_settings:
                    self.mod_settings.save_settings()
                
                # Unload all mods
                if self.mod_manager:
                    self.mod_manager.unload_all_mods()
                
                print("Mod manager cleaned up successfully")
                
            except Exception as e:
                print(f"Error during mod manager cleanup: {e}")
    
    def is_available(self) -> bool:
        """Check if the mod manager is available and initialized."""
        return self.initialized
    
    def get_mod_count(self) -> Dict[str, int]:
        """Get mod count statistics."""
        if not self.initialized or not self.mod_manager:
            return {'discovered': 0, 'loaded': 0}
        
        return {
            'discovered': len(self.mod_manager.discovered_mods),
            'loaded': len(self.mod_manager.loaded_mods)
        }

# Global integration instance
mod_integration = ModSystemIntegration()

# Global reference to main window for mod access
_main_window = None

def set_main_window(main_window):
    """Set the main window reference for mod access."""
    global _main_window
    _main_window = main_window

def get_main_window():
    """Get the main window reference for mods to use."""
    return _main_window

# Convenience functions for game code
def initialize_mod_system() -> bool:
    """Initialize the mod manager."""
    if mod_integration.initialize():
        return mod_integration.discover_and_load_mods()
    return False

def cleanup_mod_system():
    """Clean up the mod manager."""
    mod_integration.cleanup()

def reload_all_mods() -> Dict[str, bool]:
    """Reload all currently loaded mods."""
    if mod_integration.is_available() and mod_integration.mod_manager:
        return mod_integration.mod_manager.reload_all_mods()
    return {}

def emit_game_event(event_name: str, data: Dict[str, Any] = None):
    """Emit a game event."""
    mod_integration.emit_game_event(event_name, data)

def get_modded_asset_path(asset_name: str, fallback_path: str = None) -> str:
    """Get asset path with mod support and fallback."""
    if mod_integration.is_available():
        modded_path = mod_integration.get_asset_path(asset_name)
        if modded_path and modded_path.exists():
            return str(modded_path)
    
    return fallback_path or asset_name

def get_modded_tileset_path(tileset_name: str = "default", fallback_path: str = None) -> str:
    """Get tileset path with mod support and fallback."""
    if mod_integration.is_available():
        modded_path = mod_integration.get_tileset_path(tileset_name)
        if modded_path and modded_path.exists():
            return str(modded_path)
    
    return fallback_path or f"assets/{tileset_name}_tileset.png"

def get_modded_font_path(font_name: str = "default", fallback_path: str = None) -> str:
    """Get font path with mod support and fallback."""
    if mod_integration.is_available():
        modded_path = mod_integration.get_font_path(font_name)
        if modded_path and modded_path.exists():
            return str(modded_path)
    
    return fallback_path or f"assets/{font_name}_font.ttf"

def is_mod_system_available() -> bool:
    """Check if mod manager is available."""
    return mod_integration.is_available()
