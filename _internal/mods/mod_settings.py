# mod_settings.py - Hierarchical settings system for mods
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field

from config.constants import MOD_SETTINGS_SCHEMA

@dataclass
class SettingInfo:
    """Information about a setting."""
    key: str
    value: Any
    default: Any
    setting_type: str = "user"  # core, framework, user
    description: str = ""
    mod_name: str = "core"
    
class ModSettings:
    """Hierarchical settings system supporting multiple mods."""
    
    def __init__(self):
        self.settings: Dict[str, SettingInfo] = {}
        self.namespaces: Dict[str, str] = {}  # namespace -> mod_name
        self.settings_file = Path("config/mod_settings.json")
        self._load_settings()
    
    def register_mod_settings(self, mod_name: str, settings_schema: Dict[str, Any]):
        """Register settings for a mod."""
        namespace = mod_name.lower()
        
        # Check for reserved namespaces
        if namespace in MOD_SETTINGS_SCHEMA['RESERVED_NAMESPACES']:
            namespace = f"mod_{namespace}"
        
        self.namespaces[namespace] = mod_name
        
        for key, info in settings_schema.items():
            full_key = f"{namespace}{MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR']}{key}"
            
            setting_info = SettingInfo(
                key=full_key,
                value=info.get('default'),
                default=info.get('default'),
                setting_type=info.get('type', 'user'),
                description=info.get('description', ''),
                mod_name=mod_name
            )
            
            self.settings[full_key] = setting_info
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        if key in self.settings:
            return self.settings[key].value
        return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a setting value."""
        if key not in self.settings:
            # Create new user setting
            self.settings[key] = SettingInfo(
                key=key,
                value=value,
                default=value,
                setting_type="user",
                description="",
                mod_name=self._get_mod_name_from_key(key)
            )
            return True
        
        setting_info = self.settings[key]
        
        # Check if setting can be modified
        if setting_info.setting_type == "core":
            print(f"Warning: Cannot modify core setting '{key}'")
            return False
        
        if setting_info.setting_type == "framework":
            print(f"Warning: Modifying framework setting '{key}'")
        
        setting_info.value = value
        return True
    
    def get_mod_settings(self, mod_name: str) -> Dict[str, Any]:
        """Get all settings for a specific mod."""
        namespace = mod_name.lower()
        prefix = f"{namespace}{MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR']}"
        
        mod_settings = {}
        for key, setting_info in self.settings.items():
            if key.startswith(prefix):
                short_key = key[len(prefix):]
                mod_settings[short_key] = setting_info.value
        
        return mod_settings
    
    def set_mod_settings(self, mod_name: str, settings: Dict[str, Any]) -> bool:
        """Set multiple settings for a mod."""
        namespace = mod_name.lower()
        prefix = f"{namespace}{MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR']}"
        
        success = True
        for key, value in settings.items():
            full_key = f"{prefix}{key}"
            if not self.set_setting(full_key, value):
                success = False
        
        return success
    
    def reset_setting(self, key: str) -> bool:
        """Reset a setting to its default value."""
        if key in self.settings:
            setting_info = self.settings[key]
            setting_info.value = setting_info.default
            return True
        return False
    
    def reset_mod_settings(self, mod_name: str):
        """Reset all settings for a mod to defaults."""
        namespace = mod_name.lower()
        prefix = f"{namespace}{MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR']}"
        
        for key, setting_info in self.settings.items():
            if key.startswith(prefix):
                setting_info.value = setting_info.default
    
    def delete_mod_settings(self, mod_name: str):
        """Delete all settings for a mod."""
        namespace = mod_name.lower()
        prefix = f"{namespace}{MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR']}"
        
        keys_to_delete = [key for key in self.settings.keys() if key.startswith(prefix)]
        for key in keys_to_delete:
            del self.settings[key]
        
        if namespace in self.namespaces:
            del self.namespaces[namespace]
    
    def _get_mod_name_from_key(self, key: str) -> str:
        """Extract mod name from a setting key."""
        if MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR'] in key:
            namespace = key.split(MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR'])[0]
            return self.namespaces.get(namespace, "unknown")
        return "core"
    
    def _load_settings(self):
        """Load settings from file."""
        if not self.settings_file.exists():
            return
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for key, value in data.items():
                if isinstance(value, dict) and 'value' in value:
                    # Full setting info
                    setting_info = SettingInfo(
                        key=key,
                        value=value['value'],
                        default=value.get('default', value['value']),
                        setting_type=value.get('type', 'user'),
                        description=value.get('description', ''),
                        mod_name=value.get('mod_name', 'core')
                    )
                    self.settings[key] = setting_info
                else:
                    # Simple key-value pair
                    self.settings[key] = SettingInfo(
                        key=key,
                        value=value,
                        default=value,
                        setting_type="user",
                        description="",
                        mod_name=self._get_mod_name_from_key(key)
                    )
        
        except Exception as e:
            print(f"Error loading mod settings: {e}")
    
    def save_settings(self):
        """Save settings to file."""
        try:
            # Create config directory if it doesn't exist
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert settings to JSON-serializable format
            data = {}
            for key, setting_info in self.settings.items():
                # Only save non-default values
                if setting_info.value != setting_info.default:
                    data[key] = {
                        'value': setting_info.value,
                        'default': setting_info.default,
                        'type': setting_info.setting_type,
                        'description': setting_info.description,
                        'mod_name': setting_info.mod_name
                    }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Error saving mod settings: {e}")
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get all settings organized by mod."""
        organized_settings = {}
        
        for key, setting_info in self.settings.items():
            mod_name = setting_info.mod_name
            if mod_name not in organized_settings:
                organized_settings[mod_name] = {}
            
            # Get short key name
            if MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR'] in key:
                short_key = key.split(MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR'], 1)[1]
            else:
                short_key = key
            
            organized_settings[mod_name][short_key] = {
                'value': setting_info.value,
                'default': setting_info.default,
                'type': setting_info.setting_type,
                'description': setting_info.description
            }
        
        return organized_settings
    
    def validate_settings(self) -> List[str]:
        """Validate all settings and return list of issues."""
        issues = []
        
        for key, setting_info in self.settings.items():
            # Check for conflicts with reserved namespaces
            if MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR'] in key:
                namespace = key.split(MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR'])[0]
                if namespace in MOD_SETTINGS_SCHEMA['RESERVED_NAMESPACES']:
                    issues.append(f"Setting '{key}' uses reserved namespace '{namespace}'")
        
        return issues

# Global mod settings instance
mod_settings = ModSettings()

# Convenience functions
def get_mod_setting(mod_name: str, key: str, default: Any = None) -> Any:
    """Get a mod setting."""
    namespace = mod_name.lower()
    full_key = f"{namespace}{MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR']}{key}"
    return mod_settings.get_setting(full_key, default)

def set_mod_setting(mod_name: str, key: str, value: Any) -> bool:
    """Set a mod setting."""
    namespace = mod_name.lower()
    full_key = f"{namespace}{MOD_SETTINGS_SCHEMA['NAMESPACE_SEPARATOR']}{key}"
    return mod_settings.set_setting(full_key, value)

def register_mod_settings(mod_name: str, settings_schema: Dict[str, Any]):
    """Register settings for a mod."""
    return mod_settings.register_mod_settings(mod_name, settings_schema)
