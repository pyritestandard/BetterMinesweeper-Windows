# hotkeys.py - Hotkey configuration and management

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
import json
import os

class HotkeyManager:
    """Manages hotkey configuration and key sequence handling."""
    
    def __init__(self):
        self.hotkeys_file = os.path.join(os.path.dirname(__file__), "hotkeys.json")
        self.default_hotkeys = {
            "beginner": {
                "primary": "1",
                "alt": "B",
                "third": "",
                "description": "Switch to Beginner difficulty"
            },
            "intermediate": {
                "primary": "2", 
                "alt": "I",
                "third": "",
                "description": "Switch to Intermediate difficulty"
            },
            "expert": {
                "primary": "3",
                "alt": "E", 
                "third": "",
                "description": "Switch to Expert difficulty"
            },
            "restart": {
                "primary": "F2",
                "alt": "R",
                "third": "",
                "description": "Restart current game"
            },
            "options": {
                "primary": "Tab",
                "alt": "",
                "third": "",
                "description": "Open options menu"
            },
            "left_click": {
                "primary": "Space",
                "alt": "",
                "third": "",
                "description": "Simulate left mouse click",
            },
            "right_click": {
                "primary": "F",
                "alt": "",
                "third": "",
                "description": "Simulate right mouse click",
            },
            "stats": {
                "primary": "S",
                "alt": "",
                "third": "",
                "description": "Open statistics window"
            },
            "copy_seed": {
                "primary": "Ctrl+C",
                "alt": "",
                "third": "",
                "description": "Copy seed to clipboard"
            },
            "load_seed": {
                "primary": "Ctrl+V",
                "alt": "",
                "third": "",
                "description": "Load seed from clipboard"
            },
            "all_time_stats": {
                "primary": "Alt+S",
                "alt": "",
                "third": "",
                "description": "Open All-time Statistics"
            },
        }
        self.hotkeys = self.load_hotkeys()
    
    def load_hotkeys(self):
        """Load hotkeys from file, or return defaults if file doesn't exist."""
        if os.path.exists(self.hotkeys_file):
            try:
                with open(self.hotkeys_file, 'r') as f:
                    loaded = json.load(f)
                # Merge with defaults to ensure all keys exist (use deep copy)
                import copy
                result = copy.deepcopy(self.default_hotkeys)
                for action, bindings in loaded.items():
                    if action in result:
                        result[action].update(bindings)
                        # Ensure "third" key exists for all actions
                        if "third" not in result[action]:
                            result[action]["third"] = ""
                return result
            except (json.JSONDecodeError, IOError):
                pass
        import copy
        return copy.deepcopy(self.default_hotkeys)
    
    def save_hotkeys(self):
        """Save current hotkeys to file."""
        try:
            os.makedirs(os.path.dirname(self.hotkeys_file), exist_ok=True)
            with open(self.hotkeys_file, 'w') as f:
                json.dump(self.hotkeys, f, indent=2)
        except IOError:
            pass  # Fail silently
    
    def get_hotkey(self, action, key_type="primary"):
        """Get hotkey string for an action."""
        hotkey_data = self.hotkeys.get(action, {})
        return hotkey_data.get(key_type, "")
    
    def set_hotkey(self, action, key_type, key_sequence):
        """Set hotkey for an action."""
        if action not in self.hotkeys:
            import copy
            self.hotkeys[action] = copy.deepcopy(self.default_hotkeys.get(action, {}))
        self.hotkeys[action][key_type] = key_sequence
        self.save_hotkeys()
    
    def get_key_sequences(self, action):
        """Get QKeySequence objects for an action."""
        sequences = []
        hotkey_data = self.hotkeys.get(action, {})
        
        for key_type in ["primary", "alt", "third"]:
            key_str = hotkey_data.get(key_type, "")
            if key_str:
                try:
                    seq = QKeySequence(key_str)
                    if not seq.isEmpty():
                        sequences.append(seq)
                except:
                    pass  # Invalid key sequence
        
        return sequences
    
    def matches_key_event(self, event, action):
        """Check if a key event matches any hotkey for the given action."""
        sequences = self.get_key_sequences(action)
        
        # Get the key and modifiers from the event
        key = event.key()
        modifiers = event.modifiers()
        
        # Create a key sequence from the event
        # For PySide6, we need to handle the modifiers properly
        try:
            # Combine key and modifiers
            combined_key = key | int(modifiers)
            event_sequence = QKeySequence(combined_key)
        except:
            # Fallback: create sequence from string representation
            key_text = QKeySequence(key).toString()
            if modifiers != Qt.KeyboardModifier.NoModifier:
                modifier_text = ""
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    modifier_text += "Ctrl+"
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    modifier_text += "Shift+"
                if modifiers & Qt.KeyboardModifier.AltModifier:
                    modifier_text += "Alt+"
                event_sequence = QKeySequence(modifier_text + key_text)
            else:
                event_sequence = QKeySequence(key_text)
        
        # Check against all hotkey sequences for this action
        for seq in sequences:
            if event_sequence.matches(seq) == QKeySequence.SequenceMatch.ExactMatch:
                return True
        
        return False
    
    def get_all_actions(self):
        """Get list of all available actions."""
        return list(self.hotkeys.keys())
    
    def get_description(self, action):
        """Get description for an action."""
        return self.hotkeys.get(action, {}).get("description", action.title())
    
    def reset_to_defaults(self):
        """Reset all hotkeys to defaults by deleting the hotkeys file and reloading defaults."""
        if os.path.exists(self.hotkeys_file):
            try:
                os.remove(self.hotkeys_file)
            except Exception:
                pass  # Fail silently
        
        # Create a deep copy of defaults to avoid any reference issues
        import copy
        self.hotkeys = copy.deepcopy(self.default_hotkeys)
        
        self.save_hotkeys()

# Global instance
hotkey_manager = HotkeyManager()
