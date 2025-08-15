import os
import sys
import json
from PySide6.QtCore import Qt

# Default order for stats in the default "Stats" group.
# This now includes the previously "General" (always shown) items so they are
# user-toggleable: time, estimated remaining time, 3BV total, and 3BV/s.
DEFAULT_STATS_DISPLAY_ORDER = [
    'time',
    'projected_time',
    'threebv',
    'threebv_s',
]

class Settings:
    def __init__(self):
        self.chord_left_click    = True
        self.chord_middle_click  = True
        self.auto_chord_on_tile  = False
        self.auto_chord_on_flag  = False
        self.first_click_mode    = 0    # 0=empty, 1=any safe, 2=off
        self.classic_click_behavior = True
        self.fast_reveal_preview = False
        self.drag_to_paint_flags = False
        self.allow_question_marks= False
        self.surprised_face      = False
        self.allow_flag_win      = False
        self.drag_reveal         = False
        self.flag_all_on_win     = True
        self.use_text_for_numbers = True
        self.display_mode = 0  # 0=Classic, 1=Random Colors, 2=Random Letters, 3=Colored Circles
        self.window_width = None
        self.window_height = None
        self.chrome_padding_width = None
        self.chrome_padding_height = None
        self.tile_size = None
        # Classic scaling/board options
        self.use_classic_scale = False
        self.lock_classic_scale = False
        self.classic_beginner_8x8 = False
        self.auto_flag_surround = False
        self.auto_flag_isolated_mines = False
        self.auto_flag_isolated_mines_radius = 2
        self.keyboard_as_mouse_enabled = False
        self.open_stats_on_start = True
        self.stats_window_follows_game = True  # Enable stats window following by default
        self.stats_display_order = list(DEFAULT_STATS_DISPLAY_ORDER)
        # New stats grouping system (default group is named "General")
        self.stats_groups = {
            "General": list(DEFAULT_STATS_DISPLAY_ORDER)
        }
        # Stats presets system
        self.stats_presets = {}
        # Counter customization options
        self.left_counter_mode = "mines"  # "mines" or "safe"
        # Whether to display leading zeros on the left counter
        # False = hide zeros, True = show zeros
        self.left_counter_zero_mode = False
        self.show_left_counter = True
        self.hide_left_counter = False
        self.timer_start_on_one = False
        # Whether to display leading zeros on the right counter
        self.right_counter_zero_mode = False
        self.show_right_counter = True
        self.hide_right_counter = False
        self._prev_first_click_mode = None
        self._forced_first_click_off = False
        self.last_game_mode = None  # Store last played game mode
        self.stats_window_offset_x = None  # Stats window X offset from game window
        self.stats_window_offset_y = None  # Stats window Y offset from game window
        self.enabled_mods = []  # Ordered list of enabled mod namespaces
        self.enable_mod_loader = False  # Master toggle for mod manager
        self._mods_initialized = False  # Track if mods have been initialized
        self.use_sqlite_stats = True  # Use SQLite for stats storage (instead of QSettings)
        
        # Personal Best pop-up settings (Display tab)
        # Master toggle plus individual types
        self.enable_pb_popups = True       # Master toggle
        self.pb_popup_streak = True         # Show on new best win streak (per difficulty)
        self.pb_popup_3bvs = True           # Show on new best 3BV/s
        self.pb_popup_rtime = True          # Show on new best real time

        # Pause recording of all-time stats and PBs
        self.pause_alltime_recording = False

        # Game mode override system - never touches user settings!
        self._game_mode_overrides = {}  # Dict of setting_name -> override_value
        self._game_mode_active = None   # Name of active game mode
        
        # Determine where to store user_settings.json:
        # - In development: alongside this file (repo's config/)
        # - In PyInstaller dist: external folder next to the EXE (dist/BetterMinesweeper/config)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            # On macOS app bundles, sys.executable is .../My.app/Contents/MacOS/<exe>
            # Write configs to the external dist folder next to the .app
            if sys.platform == 'darwin':
                app_parent = os.path.abspath(os.path.join(base_dir, '..', '..', '..'))
                config_dir = os.path.join(app_parent, 'config')
            else:
                config_dir = os.path.join(base_dir, 'config')
        else:
            config_dir = os.path.dirname(__file__)
        try:
            os.makedirs(config_dir, exist_ok=True)
        except Exception:
            # If we cannot create the directory, fallback to temp-safe default
            pass
        self._config_path = os.path.join(config_dir, 'user_settings.json')
        self.load()

    def save(self):
        data = {}
        for k in self.__dict__:
            if not k.startswith('_') or k in ['_prev_first_click_mode', '_forced_first_click_off']:
                # NEVER save overridden values - always get the real user setting
                data[k] = object.__getattribute__(self, k)
        try:
            with open(self._config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def migrate_stats_to_groups(self):
        """Migrate old stats_display_order to new stats_groups system."""
        # Only migrate if we have the old system and haven't already migrated
        if hasattr(self, 'stats_display_order') and self.stats_display_order:
            # If stats_groups only has the default "Stats" group or is empty, migrate
            if len(self.stats_groups) <= 1 and "Stats" in self.stats_groups:
                # If "Stats" group is empty or matches default, replace with old order
                if not self.stats_groups["Stats"] or self.stats_groups["Stats"] == list(DEFAULT_STATS_DISPLAY_ORDER):
                    self.stats_groups["Stats"] = list(self.stats_display_order)
                    print(f"Migrated {len(self.stats_display_order)} stats to new grouping system")
                    # Save immediately after migration
                    self.save()

    def load(self):
        """Load settings from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r') as f:
                    data = json.load(f)
                for k, v in data.items():
                    if hasattr(self, k):
                        setattr(self, k, v)
                # Ensure new attributes exist if not in file
                if not hasattr(self, '_prev_first_click_mode'):
                    self._prev_first_click_mode = None
                if not hasattr(self, '_forced_first_click_off'):
                    self._forced_first_click_off = False
                if not hasattr(self, 'tile_size'):
                    self.tile_size = None
                if not hasattr(self, 'chrome_padding_width'):
                    self.chrome_padding_width = None
                if not hasattr(self, 'chrome_padding_height'):
                    self.chrome_padding_height = None
                if not hasattr(self, 'enable_mod_loader'):
                    self.enable_mod_loader = True
                if not hasattr(self, 'enabled_mods'):
                    self.enabled_mods = []
                if not hasattr(self, '_mods_initialized'):
                    self._mods_initialized = False
                if not hasattr(self, 'keyboard_as_mouse_enabled'):
                    self.keyboard_as_mouse_enabled = False
                if not hasattr(self, 'open_stats_on_start'):
                    self.open_stats_on_start = False
                if not hasattr(self, 'auto_flag_isolated_mines'):
                    self.auto_flag_isolated_mines = False
                if not hasattr(self, 'auto_flag_isolated_mines_radius'):
                    self.auto_flag_isolated_mines_radius = 2
                if not hasattr(self, 'stats_display_order'):
                    self.stats_display_order = list(DEFAULT_STATS_DISPLAY_ORDER)
                if not hasattr(self, 'stats_groups'):
                    self.stats_groups = {"General": list(DEFAULT_STATS_DISPLAY_ORDER)}
                if not hasattr(self, 'stats_presets'):
                    self.stats_presets = {}
                if not hasattr(self, 'left_counter_mode'):
                    self.left_counter_mode = 'mines'
                if not hasattr(self, 'left_counter_zero_mode'):
                    self.left_counter_zero_mode = False
                if not hasattr(self, 'show_left_counter'):
                    self.show_left_counter = True
                if not hasattr(self, 'hide_left_counter'):
                    self.hide_left_counter = False
                if not hasattr(self, 'timer_start_on_one'):
                    self.timer_start_on_one = False
                if not hasattr(self, 'right_counter_zero_mode'):
                    self.right_counter_zero_mode = False
                if not hasattr(self, 'show_right_counter'):
                    self.show_right_counter = True
                if not hasattr(self, 'hide_right_counter'):
                    self.hide_right_counter = False
                if not hasattr(self, 'use_classic_scale'):
                    self.use_classic_scale = False
                if not hasattr(self, 'lock_classic_scale'):
                    self.lock_classic_scale = False
                if not hasattr(self, 'classic_beginner_8x8'):
                    self.classic_beginner_8x8 = False
                if not hasattr(self, 'stats_window_offset_x'):
                    self.stats_window_offset_x = None
                if not hasattr(self, 'stats_window_offset_y'):
                    self.stats_window_offset_y = None
                if not hasattr(self, 'stats_window_follows_game'):
                    self.stats_window_follows_game = True
                if not hasattr(self, 'use_sqlite_stats'):
                    self.use_sqlite_stats = True  # Default to SQLite for new installs
                # PB pop-up settings migration defaults
                if not hasattr(self, 'enable_pb_popups'):
                    self.enable_pb_popups = False
                if not hasattr(self, 'pb_popup_streak'):
                    self.pb_popup_streak = True
                if not hasattr(self, 'pb_popup_3bvs'):
                    self.pb_popup_3bvs = True
                if not hasattr(self, 'pb_popup_rtime'):
                    self.pb_popup_rtime = True
                if not hasattr(self, 'pause_alltime_recording'):
                    self.pause_alltime_recording = False
                # Rename default group from 'Stats' to 'General' for older configs
                try:
                    if isinstance(self.stats_groups, dict):
                        if 'General' not in self.stats_groups and 'Stats' in self.stats_groups:
                            self.stats_groups['General'] = self.stats_groups['Stats']
                            del self.stats_groups['Stats']
                            # Persist rename
                            self.save()
                except Exception:
                    pass
                self.migrate_stats_to_groups()
            except Exception as e:
                print(f"Error loading settings: {e}")
        else:
            # File does not exist, save defaults to create it
            self.save()
    
    def set_game_mode_overrides(self, mode_name, overrides):
        """Set setting overrides for a game mode without touching user settings."""
        self._game_mode_active = mode_name
        self._game_mode_overrides = overrides.copy()
    
    def clear_game_mode_overrides(self):
        """Clear all game mode overrides."""
        self._game_mode_active = None
        self._game_mode_overrides = {}
    
    def __getattribute__(self, name):
        """Override attribute access to return game mode values when active."""
        # Get the override dict safely
        try:
            overrides = object.__getattribute__(self, '_game_mode_overrides')
            if overrides and name in overrides:
                return overrides[name]
        except AttributeError:
            # _game_mode_overrides doesn't exist yet (during __init__)
            pass
        
        # Return normal attribute
        return object.__getattribute__(self, name)

settings = Settings()
