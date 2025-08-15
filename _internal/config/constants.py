# constants.py - Central location for all game constants

# Tile and board sizing constants
TILE_SIZE = 64

# Board border constants
BORDER_TOP = 4
BORDER_LEFT = 1
BORDER_RIGHT = 1
BORDER_BOTTOM = 1

# Default board configurations
BEGINNER_CONFIG = {
    'width': 9,
    'height': 9,
    'mines': 10
}

INTERMEDIATE_CONFIG = {
    'width': 16,
    'height': 16,
    'mines': 40
}

EXPERT_CONFIG = {
    'width': 30,
    'height': 16,
    'mines': 99
}

# Board size calculations (used in multiple places)
def get_window_size(board_width, board_height, tile_size=TILE_SIZE):
    """Calculate the native window size for a given board size."""
    # Use actual board dimensions without enforcing minimum visual size
    # to allow for classic small Minesweeper board sizes
    visual_width = board_width
    visual_height = board_height
    
    width = (visual_width + BORDER_LEFT + BORDER_RIGHT) * tile_size
    height = (visual_height + BORDER_TOP + BORDER_BOTTOM) * tile_size
    return width, height

# Tileset atlas coordinates
UNCOVERED_BLANK = (0, 2)

NUMBER_TILES = {
    1: (0, 0), 2: (1, 0), 3: (2, 0), 4: (3, 0),
    5: (0, 1), 6: (1, 1), 7: (2, 1), 8: (3, 1),
}

# Atlas coordinates for the digital-style counter used for the bomb and timer
# displays. Each number is composed of two tiles stacked vertically.
DIGIT_TILES = {
    0: ((4, 7), (4, 8)),
    1: ((0, 5), (0, 6)),
    2: ((1, 5), (1, 6)),
    3: ((2, 5), (2, 6)),
    4: ((3, 5), (3, 6)),
    5: ((4, 5), (4, 6)),
    6: ((0, 7), (0, 8)),
    7: ((1, 7), (1, 8)),
    8: ((2, 7), (2, 8)),
    9: ((3, 7), (3, 8)),
}

# Non-lit/unlit tile pair used for leading zeros and the initial display state.
DIGIT_OFF = ((0, 9), (0, 10))

BORDER_TILES = {
    "top_left":     (4, 2),
    "top_edge":     (5, 2),
    "top_right":    (6, 2),
    "upper_left":   (4, 3),
    "upper_edge":   (5, 3),
    "upper_right":  (6, 3),
    "side_left":    (3, 4),
    "side_right":   (3, 3),
    "bottom_left":  (4, 4),
    "bottom_edge":  (5, 4),
    "bottom_right": (6, 4),
}

# Decorative edge tiles for the upper border. These tiles occupy the
# second and third rows of the board (0-based rows 1 and 2) on the three
# columns nearest each side.
DECOR_EDGE_TOP1 = (4, 0)
DECOR_EDGE_TOP2 = (5, 0)
DECOR_EDGE_TOP3 = (6, 0)
DECOR_EDGE_TOP4 = (4, 1)
DECOR_EDGE_TOP5 = (5, 1)
DECOR_EDGE_TOP6 = (6, 1)

# Smiley face atlas coordinates
# States: 0=Normal, 1=Pressed, 2=Win, 3=Lose, 4=Surprised,
# 5=Annoyed, 6=Confused
SMILEY_ATLAS_LOOKUP = [
    [(5, 5), (6, 5), (5, 6), (6, 6)],  # Normal
    [(5, 9), (6, 9), (5, 10), (6, 10)],  # Pressed
    [(1, 9), (2, 9), (1, 10), (2, 10)],  # Win
    [(5, 7), (6, 7), (5, 8), (6, 8)],  # Lose
    [(3, 9), (4, 9), (3, 10), (4, 10)],  # Surprised
    [(3, 11), (4, 11), (3, 12), (4, 12)],  # Annoyed
    [(5, 11), (6, 11), (5, 12), (6, 12)],  # Confused
]

# Smiley face state constants
SMILEY_NORMAL = 0
SMILEY_PRESSED = 1
SMILEY_WIN = 2
SMILEY_LOSE = 3
SMILEY_SURPRISED = 4
SMILEY_ANNOYED = 5
SMILEY_CONFUSED = 6

# Tile state constants
COVERED = (0, 3)
FLAG = (1, 3)
QUESTION = (2, 3)
MINE_HIT = (1, 2)
MINE_LOSE = (3, 2)
FALSE_FLAG = (2, 2)

# Color used for tile hint highlights (RGBA)
HIGHLIGHT_OVERLAY_COLOR = (255, 255, 0, 80)  # Semi-transparent yellow

# Default colors for text-based number rendering
CLASSIC_NUMBER_COLORS = [
    "#0000FF",  # 1
    "#008000",  # 2
    "#FF0000",  # 3
    "#000080",  # 4
    "#800000",  # 5
    "#008080",  # 6
    "#000000",  # 7
    "#808080",  # 8
]

# Secondary color palette used for the letter and circle modes
ALT_COLOR_PALETTE = [
    "#ff4f4f",
    "#920000",
    "#025A0E",
    "#8A00B4",
    "#3460ff",
    "#f58231",
    "#795385",
    "#00a8be",
    "#202C5E",
    "#3dad46",
    "#d12397",
    "#885509",
]

# --- Mod Manager Constants (ported from newer version) ---

# Mod Framework Architecture
MOD_FRAMEWORK = {
    'SCRIPTING_LANGUAGE': 'python',  # Like Noita's Lua
    'INJECTION_SYSTEM': 'events',    # Like Minecraft's event bus
    'NAMESPACE_SEPARATOR': ':',      # Like Minecraft's "modname:item"
    'API_VERSION': '1.0.0'
}

# Registry System (Minecraft-inspired)
MOD_REGISTRIES = {
    'TILESETS': 'mods.registry.tilesets',
    'GAME_MODES': 'mods.registry.game_modes',
    'THEMES': 'mods.registry.themes',
    'SOUNDS': 'mods.registry.sounds',
    'DIFFICULTY_PRESETS': 'mods.registry.difficulties',
    'TILE_TYPES': 'mods.registry.tile_types',
    'RENDER_EFFECTS': 'mods.registry.effects'
}

# File Override System (Noita-inspired)
MOD_FILE_TYPES = {
    'TILESET_OVERRIDE': {'pattern': 'assets/tilesets/*.png', 'merge': False},
    'CONFIG_APPEND': {'pattern': 'config/*.json', 'merge': True},
    'THEME_MERGE': {'pattern': 'themes/*.json', 'merge': True},
    'SOUND_ADD': {'pattern': 'sounds/*.wav', 'merge': False},
    'SCRIPT_INJECT': {'pattern': 'scripts/*.py', 'merge': 'append'}
}

# Event System (Minecraft-inspired)
MOD_EVENT_REGISTRY = {
    'PRIORITY_LOWEST': 1000,
    'PRIORITY_LOW': 750,
    'PRIORITY_NORMAL': 500,
    'PRIORITY_HIGH': 250,
    'PRIORITY_HIGHEST': 0,
    'PRIORITY_MONITOR': -1000  # Read-only events
}

# Dependency System (both games)
MOD_DEPENDENCY_TYPES = {
    'REQUIRED': 'hard_dependency',      # Must be present
    'OPTIONAL': 'soft_dependency',      # Enhances if present
    'INCOMPATIBLE': 'conflict',         # Cannot coexist
    'BEFORE': 'load_order_before',      # Load before this mod
    'AFTER': 'load_order_after'         # Load after this mod
}

# Namespace System (Minecraft-inspired)
MOD_NAMESPACE_RULES = {
    'RESERVED_NAMES': ['core', 'base', 'system', 'builtin'],
    'VALID_CHARS': 'abcdefghijklmnopqrstuvwxyz0123456789_',
    'MAX_LENGTH': 32,
    'CASE_SENSITIVE': False
}

# Mod Settings Schema
MOD_SETTINGS_SCHEMA = {
    'NAMESPACE_SEPARATOR': '.',
    'RESERVED_NAMESPACES': ['core', 'base', 'system', 'builtin', 'game'],
    'DEFAULT_NAMESPACE': 'mods',
    'ALLOW_NESTED_NAMESPACES': True,
    'MAX_NAMESPACE_DEPTH': 3
}

# Mod API Permissions (sandboxing)
MOD_API_LEVELS = {
    'COSMETIC': {
        'file_access': ['assets/mods/{mod_name}/**'],
        'registry_access': ['TILESETS', 'THEMES', 'SOUNDS'],
        'event_access': ['ui.*', 'render.*'],
        'settings_access': ['mods.{mod_name}.*']
    },
    'GAMEPLAY': {
        'file_access': ['assets/mods/{mod_name}/**', 'config/mods/{mod_name}/**'],
        'registry_access': ['GAME_MODES', 'DIFFICULTY_PRESETS', 'TILE_TYPES'],
        'event_access': ['game.*', 'ui.*', 'render.*'],
        'settings_access': ['mods.{mod_name}.*', 'core.display_mode']
    },
    'SYSTEM': {
        'file_access': ['**'],  # Full access (dangerous)
        'registry_access': ['**'],
        'event_access': ['**'],
        'settings_access': ['**']
    }
}

# Mod Discovery and Loading (both games)
MOD_DISCOVERY = {
    'SEARCH_PATHS': ['mods/', 'workshop/'],
    'MANIFEST_FILES': ['mod.json', 'mod.toml'],
    'REQUIRED_FIELDS': ['name', 'version', 'api_version'],
    'OPTIONAL_FIELDS': ['description', 'author', 'dependencies', 'permissions']
}

# Conflict Resolution Strategies
MOD_CONFLICT_RESOLUTION = {
    'ASSET_CONFLICTS': {
        'PRIORITY_OVERRIDE': 'highest_priority_wins',
        'USER_CHOICE': 'prompt_user_selection',
        'MERGE_COMPATIBLE': 'attempt_intelligent_merge',
        'NAMESPACE_ISOLATION': 'separate_by_namespace'
    },
    'SETTING_CONFLICTS': {
        'NAMESPACE_REQUIRED': True,
        'OVERRIDE_WARNINGS': True,
        'BACKUP_ORIGINAL': True
    },
    'CODE_CONFLICTS': {
        'EVENT_PRIORITY': 'priority_based_execution_order',
        'HOOK_CHAINING': 'allow_multiple_handlers',
        'GRACEFUL_FAILURE': 'continue_on_mod_error'
    }
}

# Performance and Safety (Noita-inspired)
MOD_SAFETY_LIMITS = {
    'MAX_MODS_LOADED': 50,
    'MAX_MEMORY_PER_MOD': 100 * 1024 * 1024,  # 100MB
    'MAX_TOTAL_MOD_MEMORY': 1024 * 1024 * 1024,  # 1GB
    'MAX_EXECUTION_TIME_MS': 100,  # Per frame
    'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50MB per file
    'ALLOWED_IMPORTS': ['json', 'math', 'random', 'os.path']  # Whitelist
}

# Mod Development Tools
MOD_DEV_TOOLS = {
    'HOT_RELOAD': True,              # Reload mods without restart
    'DEBUG_MODE': True,              # Extra logging and validation
    'PROFILING': True,               # Performance monitoring
    'CRASH_ISOLATION': True,         # Prevent mod crashes from killing game
    'LINT_CHECKING': True,           # Validate mod code
    'DEPENDENCY_GRAPH': True         # Visualize mod relationships
}


# Mod manager initialization helper functions
def initialize_mod_system():
    """Initialize the mod manager."""
    try:
        from config.settings import settings
        if not settings.enable_mod_loader:
            print("Mod loader is disabled, skipping mod manager initialization")
            return False

        from mods.mod_integration import initialize_mod_system as init_mods
        return init_mods()
    except Exception as e:
        print(f"Error initializing mod manager: {e}")
        return False


def cleanup_mod_system():
    """Clean up the mod manager."""
    try:
        from config.settings import settings
        if not settings.enable_mod_loader:
            return  # Nothing to clean up if never initialized

        from mods.mod_integration import cleanup_mod_system as cleanup_mods
        cleanup_mods()
    except Exception as e:
        print(f"Error cleaning up mod manager: {e}")

