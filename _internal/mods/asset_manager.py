# asset_manager.py - Multi-mod asset management system
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

from config.constants import MOD_FILE_TYPES, MOD_CONFLICT_RESOLUTION

@dataclass
class AssetInfo:
    """Information about an asset."""
    name: str
    path: Path
    mod_name: str
    priority: int
    asset_type: str
    
class AssetManager:
    """Manages assets from multiple mods with conflict resolution."""
    
    def __init__(self):
        self.assets: Dict[str, AssetInfo] = {}
        self.conflicts: Dict[str, List[AssetInfo]] = {}
        self.asset_cache: Dict[str, Any] = {}
        
    def register_mod_assets(self, mod_name: str, mod_path: Path, priority: int = 500):
        """Register all assets from a mod."""
        assets_dir = mod_path / 'assets'
        if not assets_dir.exists():
            return
        
        for asset_file in assets_dir.rglob('*'):
            if asset_file.is_file():
                # Determine asset type
                asset_type = self._determine_asset_type(asset_file)
                if asset_type:
                    # Create relative name for asset
                    rel_path = asset_file.relative_to(assets_dir)
                    asset_name = str(rel_path)
                    
                    asset_info = AssetInfo(
                        name=asset_name,
                        path=asset_file,
                        mod_name=mod_name,
                        priority=priority,
                        asset_type=asset_type
                    )
                    
                    self._register_asset(asset_info)
    
    def _determine_asset_type(self, asset_path: Path) -> Optional[str]:
        """Determine asset type based on file extension and location."""
        suffix = asset_path.suffix.lower()
        
        if suffix in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            if 'tileset' in asset_path.name.lower():
                return 'tileset'
            return 'image'
        elif suffix in ['.wav', '.mp3', '.ogg']:
            return 'sound'
        elif suffix in ['.json']:
            return 'config'
        elif suffix in ['.ttf', '.otf']:
            return 'font'
        
        return None
    
    def _register_asset(self, asset_info: AssetInfo):
        """Register an asset with conflict detection."""
        asset_name = asset_info.name
        
        if asset_name in self.assets:
            # Conflict detected
            existing = self.assets[asset_name]
            
            # Track conflicts
            if asset_name not in self.conflicts:
                self.conflicts[asset_name] = [existing]
            self.conflicts[asset_name].append(asset_info)
            
            # Resolve conflict based on priority
            if asset_info.priority < existing.priority:
                # Higher priority (lower number) wins
                self.assets[asset_name] = asset_info
                print(f"Asset conflict: {asset_name} - {asset_info.mod_name} overrides {existing.mod_name}")
            else:
                print(f"Asset conflict: {asset_name} - {existing.mod_name} keeps priority over {asset_info.mod_name}")
        else:
            self.assets[asset_name] = asset_info
    
    def get_asset_path(self, asset_name: str) -> Optional[Path]:
        """Get the path to an asset."""
        if asset_name in self.assets:
            return self.assets[asset_name].path
        
        # Try with common asset directories
        for common_dir in ['tilesets', 'sounds', 'fonts']:
            full_name = f"{common_dir}/{asset_name}"
            if full_name in self.assets:
                return self.assets[full_name].path
        
        return None
    
    def get_tileset_path(self, tileset_name: str = "default") -> Optional[Path]:
        """Get path to a tileset."""
        # Try exact match first
        tileset_path = self.get_asset_path(f"tilesets/{tileset_name}.png")
        if tileset_path:
            return tileset_path
        
        # Try without extension
        tileset_path = self.get_asset_path(f"tilesets/{tileset_name}")
        if tileset_path:
            return tileset_path
        
        # Fall back to default
        if tileset_name != "default":
            return self.get_tileset_path("default")
        
        return None
    
    def get_font_path(self, font_name: str = "default") -> Optional[Path]:
        """Get path to a font."""
        # Try common font extensions
        for ext in ['.ttf', '.otf']:
            font_path = self.get_asset_path(f"fonts/{font_name}{ext}")
            if font_path:
                return font_path
        
        # Try without extension
        font_path = self.get_asset_path(f"fonts/{font_name}")
        if font_path:
            return font_path
        
        # Fall back to default
        if font_name != "default":
            return self.get_font_path("default")
        
        return None
    
    def get_sound_path(self, sound_name: str) -> Optional[Path]:
        """Get path to a sound file."""
        # Try common sound extensions
        for ext in ['.wav', '.mp3', '.ogg']:
            sound_path = self.get_asset_path(f"sounds/{sound_name}{ext}")
            if sound_path:
                return sound_path
        
        # Try without extension
        return self.get_asset_path(f"sounds/{sound_name}")
    
    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Load and cache a JSON configuration file."""
        cache_key = f"config:{config_name}"
        
        if cache_key in self.asset_cache:
            return self.asset_cache[cache_key]
        
        config_path = self.get_asset_path(f"config/{config_name}.json")
        if not config_path or not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.asset_cache[cache_key] = config
            return config
            
        except Exception as e:
            print(f"Error loading config {config_name}: {e}")
            return None
    
    def merge_configs(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Merge configuration files from all mods."""
        merged_config = {}
        
        # Find all matching config files
        pattern = f"config/{config_name}.json"
        matching_assets = [
            asset for asset in self.assets.values()
            if asset.name == pattern and asset.asset_type == 'config'
        ]
        
        # Sort by priority (higher priority = lower number)
        matching_assets.sort(key=lambda x: x.priority)
        
        for asset in matching_assets:
            try:
                with open(asset.path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Deep merge the configurations
                merged_config = self._deep_merge(merged_config, config)
                
            except Exception as e:
                print(f"Error merging config {asset.path}: {e}")
        
        return merged_config if merged_config else None
    
    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_conflicts(self) -> Dict[str, List[AssetInfo]]:
        """Get all asset conflicts."""
        return self.conflicts.copy()
    
    def resolve_conflict(self, asset_name: str, preferred_mod: str) -> bool:
        """Manually resolve an asset conflict."""
        if asset_name not in self.conflicts:
            return False
        
        conflicts = self.conflicts[asset_name]
        for asset_info in conflicts:
            if asset_info.mod_name == preferred_mod:
                self.assets[asset_name] = asset_info
                return True
        
        return False
    
    def clear_cache(self):
        """Clear the asset cache."""
        self.asset_cache.clear()
    
    def unregister_mod_assets(self, mod_name: str):
        """Remove all assets from a specific mod."""
        # Remove from main assets
        to_remove = [name for name, asset in self.assets.items() if asset.mod_name == mod_name]
        for name in to_remove:
            del self.assets[name]
        
        # Remove from conflicts
        for asset_name, conflict_list in self.conflicts.items():
            self.conflicts[asset_name] = [
                asset for asset in conflict_list if asset.mod_name != mod_name
            ]
        
        # Remove empty conflict lists
        self.conflicts = {k: v for k, v in self.conflicts.items() if v}
        
        # Clear cache
        self.clear_cache()
    
    def get_asset_info(self, asset_name: str) -> Optional[AssetInfo]:
        """Get detailed information about an asset."""
        return self.assets.get(asset_name)
    
    def list_assets(self, asset_type: str = None, mod_name: str = None) -> List[AssetInfo]:
        """List assets with optional filtering."""
        assets = list(self.assets.values())
        
        if asset_type:
            assets = [asset for asset in assets if asset.asset_type == asset_type]
        
        if mod_name:
            assets = [asset for asset in assets if asset.mod_name == mod_name]
        
        return assets

# Global asset manager instance
asset_manager = AssetManager()

# Register base game assets
def register_base_assets():
    """Register the base game assets."""
    base_assets_dir = Path("assets")
    if base_assets_dir.exists():
        asset_manager.register_mod_assets("core", Path("."), priority=0)  # Highest priority

# Initialize base assets
register_base_assets()
