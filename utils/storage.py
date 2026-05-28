import os
import json
from typing import Dict, Any, Optional

DEFAULT_STATE = {
    "startup_name": "New Horizon",
    "startup_idea": "A space-exploration API service.",
    "stage": "Idea",
    "budget": 25000.0,
    "valuation": 50000.0,
    "mrr": 0.0,
    "users": 0,
    "code_quality": 100.0,  # Percentage, 0-100
    "tech_debt": 0.0,       # Accumulated points
    "day": 1,
    "logs": [
        {
            "sender": "System",
            "message": "Welcome to StartupForge-AI! Pitch your idea to get started.",
            "timestamp": "Day 1"
        }
    ],
    "tasks": {
        "backlog": [],
        "in_progress": [],
        "completed": []
    },
    "agents": {
        "CEO": {"energy": 100, "focus": "Strategy", "mood": "Excited", "level": 1},
        "CTO": {"energy": 100, "focus": "Architecture", "mood": "Focused", "level": 1},
        "PM": {"energy": 100, "focus": "Planning", "mood": "Calm", "level": 1},
        "Developer": {"energy": 100, "focus": "Coding", "mood": "Tired", "level": 1},
        "Marketer": {"energy": 100, "focus": "Growth", "mood": "Energetic", "level": 1}
    },
    "reports": [],
    "memories": []
}


class SaveManager:
    """Manages serialization and deserialization of the Startup Forge simulation state."""
    
    def __init__(self, saves_dir: str = "saves"):
        self.saves_dir = saves_dir
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
            
    def get_save_path(self, filename: str) -> str:
        """Helper to get full path to a save file."""
        if not filename.endswith(".json"):
            filename += ".json"
        return os.path.join(self.saves_dir, filename)

    def save_state(self, state: Dict[str, Any], filename: str = "current_game.json") -> bool:
        """Serializes and saves the state dict to a JSON file."""
        try:
            path = self.get_save_path(filename)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_state(self, filename: str = "current_game.json") -> Dict[str, Any]:
        """Loads and deserializes state dict from JSON file. Returns DEFAULT_STATE if missing/corrupt."""
        path = self.get_save_path(filename)
        if not os.path.exists(path):
            return DEFAULT_STATE.copy()
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            # Ensure all default keys exist (basic migration capability)
            merged = DEFAULT_STATE.copy()
            merged.update(loaded)
            return merged
        except Exception as e:
            print(f"Error loading state from {path}: {e}. Returning defaults.")
            return DEFAULT_STATE.copy()

    def list_saves(self) -> list:
        """Lists all available JSON saves."""
        try:
            return [f for f in os.listdir(self.saves_dir) if f.endswith(".json")]
        except Exception:
            return []
