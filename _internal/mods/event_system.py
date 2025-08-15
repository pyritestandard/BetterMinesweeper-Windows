# event_system.py - Event-driven mod communication system
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import IntEnum
import traceback

from config.constants import MOD_EVENT_REGISTRY

class EventPriority(IntEnum):
    """Event priority levels."""
    HIGHEST = MOD_EVENT_REGISTRY['PRIORITY_HIGHEST']
    HIGH = MOD_EVENT_REGISTRY['PRIORITY_HIGH']
    NORMAL = MOD_EVENT_REGISTRY['PRIORITY_NORMAL']
    LOW = MOD_EVENT_REGISTRY['PRIORITY_LOW']
    LOWEST = MOD_EVENT_REGISTRY['PRIORITY_LOWEST']
    MONITOR = MOD_EVENT_REGISTRY['PRIORITY_MONITOR']

@dataclass
class Event:
    """Base event class."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False
    
    def cancel(self):
        """Cancel this event."""
        self.cancelled = True
    
    def is_cancelled(self) -> bool:
        """Check if event is cancelled."""
        return self.cancelled

@dataclass
class EventHandler:
    """Represents an event handler registration."""
    callback: Callable[[Event], None]
    priority: int
    mod_name: str
    event_name: str
    
    def __lt__(self, other):
        return self.priority < other.priority

class EventSystem:
    """Centralized event system for mod communication."""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.event_stats: Dict[str, int] = {}
        
    def register_handler(self, event_name: str, callback: Callable[[Event], None], 
                        priority: int = EventPriority.NORMAL, mod_name: str = "core") -> bool:
        """Register an event handler."""
        try:
            if event_name not in self.handlers:
                self.handlers[event_name] = []

            handler = EventHandler(callback, priority, mod_name, event_name)

            # Insert handler while keeping the list sorted by priority. Using
            # bisect avoids re-sorting the entire list every registration.
            from bisect import insort
            insort(self.handlers[event_name], handler)
            
            return True
            
        except Exception as e:
            print(f"Error registering event handler for {event_name}: {e}")
            return False
    
    def unregister_handler(self, event_name: str, callback: Callable[[Event], None], 
                          mod_name: str = "core") -> bool:
        """Unregister an event handler."""
        if event_name not in self.handlers:
            return False
        
        handlers = self.handlers[event_name]
        for i, handler in enumerate(handlers):
            if handler.callback == callback and handler.mod_name == mod_name:
                del handlers[i]
                return True
        
        return False
    
    def unregister_mod_handlers(self, mod_name: str):
        """Remove all handlers for a specific mod."""
        for event_name in self.handlers:
            self.handlers[event_name] = [
                handler for handler in self.handlers[event_name] 
                if handler.mod_name != mod_name
            ]
    
    def emit_event(self, event_name: str, data: Dict[str, Any] = None) -> Event:
        """Emit an event and call all registered handlers."""
        event = Event(event_name, data or {})
        
        if event_name in self.handlers:
            for handler in self.handlers[event_name]:
                if event.is_cancelled() and handler.priority != EventPriority.MONITOR:
                    # Skip non-monitor handlers if event is cancelled
                    continue
                
                try:
                    handler.callback(event)
                except Exception as e:
                    print(f"Error in event handler {handler.mod_name}.{event_name}: {e}")
                    print(traceback.format_exc())
        
        # Update statistics
        self.event_stats[event_name] = self.event_stats.get(event_name, 0) + 1
        
        return event
    
    def get_handlers(self, event_name: str) -> List[EventHandler]:
        """Get all handlers for an event."""
        return self.handlers.get(event_name, [])
    
    def get_event_stats(self) -> Dict[str, int]:
        """Get event emission statistics."""
        return self.event_stats.copy()
    
    def clear_stats(self):
        """Clear event statistics."""
        self.event_stats.clear()

# Predefined game events
class GameEvents:
    """Common game event names."""
    # Game state events
    GAME_START = "game.start"
    GAME_END = "game.end"
    GAME_RESET = "game.reset"
    GAME_WIN = "game.win"
    GAME_LOSE = "game.lose"
    
    # Tile events
    TILE_REVEAL = "game.tile.reveal"
    TILE_FLAG = "game.tile.flag"
    TILE_QUESTION = "game.tile.question"
    TILE_CHORD = "game.tile.chord"
    
    # Board events
    BOARD_GENERATE = "game.board.generate"
    BOARD_RESIZE = "game.board.resize"
    FIRST_CLICK = "game.board.first_click"
    
    # UI events
    UI_RENDER = "ui.render"
    UI_TILE_DRAW = "ui.tile.draw"
    UI_WINDOW_RESIZE = "ui.window.resize"
    UI_THEME_CHANGE = "ui.theme.change"
    
    # Mod events
    MOD_LOAD = "mod.load"
    MOD_UNLOAD = "mod.unload"
    MOD_ERROR = "mod.error"

# Global event system instance
event_system = EventSystem()

# Decorator for easy event handler registration
def event_handler(event_name: str, priority: int = EventPriority.NORMAL):
    """Decorator for registering event handlers."""
    def decorator(func):
        func._event_name = event_name
        func._event_priority = priority
        return func
    return decorator
