# mod_manager.py - Core mod management system
import json
import os
import sys
import importlib.util
import traceback
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import config.settings as settings

from config.constants import (
    MOD_DISCOVERY, MOD_FRAMEWORK, MOD_DEPENDENCY_TYPES, 
    MOD_SAFETY_LIMITS, MOD_NAMESPACE_RULES, MOD_API_LEVELS
)

class ModInfo:
    """Represents metadata about a mod."""
    def __init__(self, data: Dict[str, Any], mod_path: Path):
        self.name = data['name']
        self.version = data['version']
        self.api_version = data['api_version']
        self.description = data.get('description', '')
        self.author = data.get('author', 'Unknown')
        self.dependencies = data.get('dependencies', {})
        self.permissions = data.get('permissions', 'COSMETIC')
        self.load_priority = data.get('load_priority', 500)
        self.mod_path = mod_path
        self.namespace = self._validate_namespace(self.name)
        self.loaded = False
        self.mod_instance = None
        
    def _validate_namespace(self, name: str) -> str:
        """Validate and normalize mod namespace."""
        # Convert to lowercase and replace invalid chars
        namespace = ''.join(c if c in MOD_NAMESPACE_RULES['VALID_CHARS'] else '_' 
                          for c in name.lower())
        
        # Check reserved names
        if namespace in MOD_NAMESPACE_RULES['RESERVED_NAMES']:
            namespace = f"mod_{namespace}"
            
        # Truncate if too long
        if len(namespace) > MOD_NAMESPACE_RULES['MAX_LENGTH']:
            namespace = namespace[:MOD_NAMESPACE_RULES['MAX_LENGTH']]
            
        return namespace

class ModManager:
    """Manages mod discovery, loading, and lifecycle."""
    
    def __init__(self):
        self.discovered_mods: Dict[str, ModInfo] = {}
        self.loaded_mods: Dict[str, ModInfo] = {}
        self.mod_load_order: List[str] = []
        self.event_system = None  # Will be set by EventSystem
        self.asset_manager = None  # Will be set by AssetManager
        self._discovery_cache = None
        self._cache_valid = False
        self._cache_timestamp = 0
        self._dir_snapshot = {}
        self._discovery_errors = []  # Track discovery errors
    
    def discover_mods(self, force_refresh: bool = False) -> List[ModInfo]:
        """Discover all available mods with caching."""
        import time
        import os

        # Check if we need to refresh the cache
        current_time = time.time()
        cache_age = current_time - self._cache_timestamp

        search_dirs = [Path(p) for p in MOD_DISCOVERY['SEARCH_PATHS']]
        existing_dirs = [d for d in search_dirs if d.exists()]

        dirs_snapshot = {str(d): d.stat().st_mtime for d in existing_dirs}

        # Use cache if it's valid, directories unchanged, and not forced to refresh
        if (not force_refresh and
            self._cache_valid and
            self._discovery_cache is not None and
            cache_age < 600 and  # Cache valid for 10 minutes
            dirs_snapshot == self._dir_snapshot):
            return self._discovery_cache
        
        # Perform discovery with improved performance
        self.discovered_mods.clear()
        
        # Clear previous discovery errors
        if hasattr(self, '_discovery_errors'):
            self._discovery_errors.clear()
        
        # Quick check: if no mod directories exist, return empty list
        if not existing_dirs:
            self._discovery_cache = []
            self._cache_valid = True
            self._cache_timestamp = current_time
            return self._discovery_cache
        
        # Pre-compile manifest file patterns for faster lookup
        manifest_files = MOD_DISCOVERY['MANIFEST_FILES']
        
        for search_dir in existing_dirs:
            try:
                # Use faster os.scandir instead of pathlib for initial scan
                with os.scandir(search_dir) as entries:
                    mod_dirs = [entry.path for entry in entries if entry.is_dir()]
                
                for mod_dir_path in mod_dirs:
                    mod_dir = Path(mod_dir_path)
                    
                    # Look for manifest file - optimized with early exit
                    manifest_path = None
                    for manifest_file in manifest_files:
                        potential_path = mod_dir / manifest_file
                        if potential_path.is_file():  # is_file() is faster than exists()
                            manifest_path = potential_path
                            break
                    
                    if manifest_path:
                        try:
                            mod_info = self._load_mod_info(manifest_path, mod_dir)
                            if mod_info:
                                self.discovered_mods[mod_info.namespace] = mod_info
                        except Exception as e:
                            # Silently skip problematic mods to avoid console spam
                            self._add_discovery_error(f"Error loading mod {mod_dir.name}: {e}")
                            
            except (OSError, PermissionError):
                # Skip directories that can't be read
                continue
        
        # Update cache and snapshot
        self._discovery_cache = list(self.discovered_mods.values())
        self._cache_valid = True
        self._cache_timestamp = current_time
        self._dir_snapshot = dirs_snapshot
        
        return self._discovery_cache
    
    def _load_mod_info(self, manifest_path: Path, mod_dir: Path) -> Optional[ModInfo]:
        """Load mod information from manifest file."""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                if manifest_path.suffix == '.json':
                    data = json.load(f)
                elif manifest_path.suffix == '.toml':
                    try:
                        # Prefer the standard library tomllib if available
                        try:
                            import tomllib as toml_module
                        except ModuleNotFoundError:
                            import toml as toml_module  # type: ignore
                        data = toml_module.load(f)
                    except Exception:
                        self._add_discovery_error(
                            f"TOML support not available, skipping {manifest_path}"
                        )
                        return None
                else:
                    return None
            
            # Validate required fields
            for field in MOD_DISCOVERY['REQUIRED_FIELDS']:
                if field not in data:
                    self._add_discovery_error(f"Mod {mod_dir.name} missing required field: {field}")
                    return None
            
            # Check API version compatibility
            if data['api_version'] != MOD_FRAMEWORK['API_VERSION']:
                self._add_discovery_error(f"Mod {data['name']} API version {data['api_version']} incompatible with {MOD_FRAMEWORK['API_VERSION']}")
                return None
            
            return ModInfo(data, mod_dir)
            
        except Exception as e:
            self._add_discovery_error(f"Error parsing mod manifest {manifest_path}: {e}")
            return None
    
    def resolve_dependencies(self, preferred_order: Optional[List[str]] = None) -> List[str]:
        """Resolve mod dependencies and return load order.

        Supports ``REQUIRED`` dependencies as well as ``BEFORE`` and ``AFTER``
        ordering hints. If ``preferred_order`` is supplied, mods are ordered
        according to that list when it does not conflict with dependency rules.
        """

        # Build dependency edges (A -> B means A must load before B)
        edges: Dict[str, List[str]] = {name: [] for name in self.discovered_mods}
        for mod_name, info in self.discovered_mods.items():
            for dep_name, dep_type in info.dependencies.items():
                if dep_type == MOD_DEPENDENCY_TYPES['REQUIRED']:
                    if dep_name not in self.discovered_mods:
                        raise ValueError(
                            f"Required dependency {dep_name} not found for mod {mod_name}")
                    edges.setdefault(dep_name, []).append(mod_name)
                elif dep_type == MOD_DEPENDENCY_TYPES['AFTER']:
                    edges.setdefault(dep_name, []).append(mod_name)
                elif dep_type == MOD_DEPENDENCY_TYPES['BEFORE']:
                    edges.setdefault(mod_name, []).append(dep_name)

        load_order: List[str] = []
        visited = set()
        temp = set()

        def visit(node: str):
            if node in temp:
                raise ValueError(f"Circular dependency detected involving {node}")
            if node in visited:
                return
            temp.add(node)
            for nxt in edges.get(node, []):
                visit(nxt)
            temp.remove(node)
            visited.add(node)
            load_order.append(node)

        for mod in self.discovered_mods:
            if mod not in visited:
                visit(mod)

        if preferred_order:
            order_index = {name: i for i, name in enumerate(preferred_order)}
            candidate = sorted(load_order, key=lambda n: order_index.get(n, len(order_index)))
            pos = {m: i for i, m in enumerate(candidate)}
            for mod in candidate:
                for dep in edges.get(mod, []):
                    if pos.get(dep, -1) > pos[mod]:
                        candidate = load_order
                        break
                else:
                    continue
                break
            load_order = candidate

        self.mod_load_order = load_order
        return load_order
    
    def load_mod(self, mod_name: str) -> bool:
        """Load a specific mod."""
        if mod_name not in self.discovered_mods:
            print(f"Mod {mod_name} not found")
            return False
        
        if mod_name in self.loaded_mods:
            print(f"Mod {mod_name} already loaded")
            return True
        
        mod_info = self.discovered_mods[mod_name]
        
        try:
            # Check if we're at the mod limit
            if len(self.loaded_mods) >= MOD_SAFETY_LIMITS['MAX_MODS_LOADED']:
                print(f"Cannot load {mod_name}: mod limit reached")
                return False
            
            # Load the mod's main script with faster path checking
            init_script = mod_info.mod_path / 'scripts' / 'init.py'
            if not init_script.is_file():  # is_file() is faster than exists()
                print(f"Mod {mod_name} missing init.py script")
                return False
            
            # Create module spec with optimized namespace
            module_name = f"mods.{mod_info.namespace}"
            
            # Check if module already exists in sys.modules (avoid reload)
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                # Load the module
                spec = importlib.util.spec_from_file_location(module_name, init_script)
                if spec is None or spec.loader is None:
                    print(f"Mod {mod_name} failed to create module spec")
                    return False
                    
                module = importlib.util.module_from_spec(spec)
                
                # Add to sys.modules before execution for circular imports
                sys.modules[module_name] = module
                
                # Execute the module
                spec.loader.exec_module(module)
            
            # Look for main mod class with faster attribute access
            mod_class = getattr(module, 'Mod', None)
            if mod_class:
                mod_instance = mod_class(mod_info)
                mod_info.mod_instance = mod_instance

                # Initialize the mod
                if hasattr(mod_instance, 'initialize'):
                    mod_instance.initialize()

            if self.asset_manager:
                try:
                    self.asset_manager.register_mod_assets(
                        mod_name,
                        mod_info.mod_path,
                        priority=mod_info.load_priority,
                    )
                except Exception as e:
                    print(f"Error registering assets for {mod_name}: {e}")

            mod_info.loaded = True
            self.loaded_mods[mod_name] = mod_info
            print(f"Successfully loaded mod: {mod_name}")
            if self.event_system:
                try:
                    from .event_system import GameEvents
                    self.event_system.emit_event(GameEvents.MOD_LOAD, {
                        'mod_name': mod_name,
                        'mod_info': mod_info,
                    })
                except Exception as e:
                    print(f"Error emitting mod.load event for {mod_name}: {e}")
            return True
            
        except Exception as e:
            print(f"Error loading mod {mod_name}: {e}")
            # Remove from sys.modules if it was added during failed load
            module_name = f"mods.{mod_info.namespace}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            print(traceback.format_exc())
            return False
    
    def load_all_mods(self) -> Dict[str, bool]:
        """Load all discovered mods in dependency order, honoring user load order when possible."""
        results = {}

        try:
            preferred = get_enabled_mods()
            
            # Only auto-enable all mods if no enabled mods are specified AND this is the first run
            if not preferred and not hasattr(settings.settings, '_mods_initialized'):
                preferred = list(self.discovered_mods.keys())
                # Mark that we've initialized mods and save the initial enabled list
                settings.settings.enabled_mods = preferred
                settings.settings._mods_initialized = True
                settings.settings.save()
                print(f"First run: auto-enabling all discovered mods: {preferred}")
            elif not preferred:
                print("No mods enabled by user")
                return {}
            
            load_order = self.resolve_dependencies(preferred_order=preferred)

            # Determine which mods actually need to be loaded
            mods_to_load = set()

            def include_mod(mod_name: str):
                if mod_name not in self.discovered_mods or mod_name in mods_to_load:
                    return
                mods_to_load.add(mod_name)
                info = self.discovered_mods[mod_name]
                for dep, dep_type in info.dependencies.items():
                    if dep_type == MOD_DEPENDENCY_TYPES['REQUIRED']:
                        include_mod(dep)

            for name in preferred:
                include_mod(name)

            # Group mods by dependency level for sequential loading
            dependency_levels = {}
            for mod_name in load_order:
                if mod_name not in mods_to_load:
                    continue
                mod_info = self.discovered_mods[mod_name]
                if not mod_info.dependencies:
                    dependency_levels.setdefault(0, []).append(mod_name)
                else:
                    dependency_levels.setdefault(1, []).append(mod_name)

            # Load level 0 mods sequentially to avoid Qt threading issues
            if 0 in dependency_levels:
                for mod_name in dependency_levels[0]:
                    try:
                        results[mod_name] = self.load_mod(mod_name)
                    except Exception as e:
                        print(f"Error loading mod {mod_name}: {e}")
                        results[mod_name] = False

            # Load remaining mods sequentially in dependency order
            for level in sorted(k for k in dependency_levels.keys() if k != 0):
                for mod_name in dependency_levels[level]:
                    results[mod_name] = self.load_mod(mod_name)
                    
        except Exception as e:
            print(f"Error resolving dependencies: {e}")
            # Fall back to simple loading
            for mod_name in mods_to_load if 'mods_to_load' in locals() else self.discovered_mods:
                results[mod_name] = self.load_mod(mod_name)
        
        return results
    
    def unload_mod(self, mod_name: str) -> bool:
        """Unload a specific mod."""
        if mod_name not in self.loaded_mods:
            return False
        
        mod_info = self.loaded_mods[mod_name]
        
        try:
            # Call mod's cleanup if it exists
            if mod_info.mod_instance and hasattr(mod_info.mod_instance, 'cleanup'):
                mod_info.mod_instance.cleanup()
            
            # Remove from loaded mods
            del self.loaded_mods[mod_name]
            mod_info.loaded = False
            mod_info.mod_instance = None
            
            # Remove from sys.modules
            module_name = f"mods.{mod_info.namespace}"
            if module_name in sys.modules:
                del sys.modules[module_name]

            if self.event_system:
                try:
                    from .event_system import GameEvents
                    self.event_system.emit_event(GameEvents.MOD_UNLOAD, {
                        'mod_name': mod_name,
                        'mod_info': mod_info,
                    })
                except Exception as e:
                    print(f"Error emitting mod.unload event for {mod_name}: {e}")

            print(f"Unloaded mod: {mod_name}")
            return True
            
        except Exception as e:
            print(f"Error unloading mod {mod_name}: {e}")
            return False

    def unload_all_mods(self) -> Dict[str, bool]:
        """Unload all currently loaded mods."""
        results = {}
        
        try:
            # Unload in reverse order to handle dependencies
            for mod_name in reversed(list(self.loaded_mods.keys())):
                results[mod_name] = self.unload_mod(mod_name)
            
            print(f"Unloaded {len(results)} mods")
            return results
            
        except Exception as e:
            print(f"Error during mod unloading: {e}")
            return {}
    
    def reload_mod(self, mod_name: str) -> bool:
        """Reload a specific mod."""
        if not self.unload_mod(mod_name):
            return False
        return self.load_mod(mod_name)

    def reload_all_mods(self) -> Dict[str, bool]:
        """Reload all currently loaded mods."""
        to_reload = list(self.loaded_mods.keys())
        self.unload_all_mods()
        results = {}
        for name in to_reload:
            results[name] = self.load_mod(name)
        return results
    
    def get_mod_info(self, mod_name: str) -> Optional[ModInfo]:
        """Get information about a mod."""
        return self.discovered_mods.get(mod_name) or self.loaded_mods.get(mod_name)
    
    def is_mod_loaded(self, mod_name: str) -> bool:
        """Check if a mod is loaded."""
        return mod_name in self.loaded_mods

    def invalidate_discovery_cache(self):
        """Invalidate the discovery cache to force refresh on next discovery."""
        self._cache_valid = False
        self._discovery_cache = None
        self._cache_timestamp = 0

    def get_discovery_errors(self) -> List[str]:
        """Get any errors that occurred during mod discovery."""
        return getattr(self, '_discovery_errors', [])
    
    def _add_discovery_error(self, error: str):
        """Add a discovery error to the error list."""
        if not hasattr(self, '_discovery_errors'):
            self._discovery_errors = []
        self._discovery_errors.append(error)
        # Keep only the last 10 errors to avoid memory issues
        if len(self._discovery_errors) > 10:
            self._discovery_errors = self._discovery_errors[-10:]

def get_enabled_mods():
    """Get the list of enabled mod namespaces from settings in saved order."""
    return list(getattr(settings.settings, 'enabled_mods', []))

def set_enabled_mods(enabled_mods):
    """Save the ordered list of enabled mod namespaces to settings."""
    settings.settings.enabled_mods = list(enabled_mods)
    settings.settings.save()

# Global mod manager instance
mod_manager = ModManager()
