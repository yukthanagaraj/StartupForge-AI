import os
import json
import time
from typing import Dict, Any, List, Optional

class ForgeSaveManager:
    """Manages serialization/deserialization of simulation runs, reports, and memories."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.saves_dir = os.path.join(base_dir, "saves")
        self.reports_dir = os.path.join(base_dir, "saved_reports")
        self.memory_dir = os.path.join(base_dir, "memory")
        self.exports_dir = os.path.join(base_dir, "exports")

        # Guarantee all directories exist
        for d in [self.saves_dir, self.reports_dir, self.memory_dir, self.exports_dir]:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)

    # =========================================================================
    # SIMULATION STATES (RE-USED & STANDARDIZED FROM STORAGE.PY)
    # =========================================================================

    def get_save_path(self, filename: str) -> str:
        if not filename.endswith(".json"):
            filename += ".json"
        return os.path.join(self.saves_dir, filename)

    def save_state(self, state: Dict[str, Any], filename: str = "current_game.json") -> bool:
        try:
            path = self.get_save_path(filename)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_state(self, filename: str = "current_game.json", default_state: Dict[str, Any] = None) -> Dict[str, Any]:
        path = self.get_save_path(filename)
        if not os.path.exists(path):
            return default_state.copy() if default_state else {}
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            if default_state:
                merged = default_state.copy()
                merged.update(loaded)
                return merged
            return loaded
        except Exception as e:
            print(f"Error loading state: {e}")
            return default_state.copy() if default_state else {}

    # =========================================================================
    # REPORTS STORAGE (saved_reports/)
    # =========================================================================

    def save_report(self, title: str, report_type: str, day: int, content: Any) -> Dict[str, Any]:
        """Saves a report both as JSON (structured metadata) and Markdown (human readable)."""
        timestamp_ms = int(time.time() * 1000)
        report_id = f"rpt_{timestamp_ms}"
        filename_base = f"report_{timestamp_ms}"
        
        # Structure the report dict
        report_data = {
            "id": report_id,
            "title": title,
            "type": report_type,
            "day": day,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": content
        }

        # 1. Save JSON representation
        json_path = os.path.join(self.reports_dir, f"{filename_base}.json")
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving report JSON: {e}")

        # 2. Save Markdown representation
        md_path = os.path.join(self.reports_dir, f"{filename_base}.md")
        try:
            md_content = self.convert_report_to_markdown(report_data)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
        except Exception as e:
            print(f"Error saving report MD: {e}")

        return report_data

    def list_reports(self) -> List[Dict[str, Any]]:
        """Scans saved_reports/ directory and returns list of reports, sorted newest first."""
        reports = []
        if not os.path.exists(self.reports_dir):
            return reports

        for filename in os.listdir(self.reports_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.reports_dir, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data["_filename_base"] = filename.replace(".json", "")
                        reports.append(data)
                except Exception as e:
                    print(f"Error reading report {filename}: {e}")

        # Sort by creation time (id has timestamp) or date
        reports.sort(key=lambda r: r.get("id", ""), reverse=True)
        return reports

    def delete_report(self, filename_base: str) -> bool:
        """Deletes both JSON and Markdown representation of a report."""
        success = False
        for ext in [".json", ".md"]:
            path = os.path.join(self.reports_dir, f"{filename_base}{ext}")
            if os.path.exists(path):
                try:
                    os.remove(path)
                    success = True
                except Exception as e:
                    print(f"Error deleting report file {path}: {e}")
        return success

    def convert_report_to_markdown(self, report: Dict[str, Any]) -> str:
        """Converts a structured report into a high-fidelity Markdown page."""
        title = report.get("title", "Untitled Forge Report")
        rtype = report.get("type", "General")
        day = report.get("day", 1)
        created_at = report.get("timestamp", "N/A")
        content = report.get("content", "")

        md = []
        md.append(f"# {title}")
        md.append(f"**Metadata**:")
        md.append(f"- **Report Type**: {rtype}")
        md.append(f"- **Simulation Stage**: Operational Day {day}")
        md.append(f"- **Compiled At**: {created_at}")
        md.append(f"\n---\n")

        if isinstance(content, list):
            # Probably a board/sprint meeting conversation logs
            md.append("## 💬 Virtual Board Meeting Transcript\n")
            for msg in content:
                sender = msg.get("sender", "Agent")
                role = msg.get("role", "Co-Founder")
                text = msg.get("message", "")
                md.append(f"### 👾 {sender} ({role})")
                md.append(f"> {text}\n")
        else:
            # Standard single block string text report
            md.append("## 📋 Details & Deliverables\n")
            md.append(str(content))

        md.append("\n---\n*Report generated automatically by StartupForge-AI Engine.*")
        return "\n".join(md)

    # =========================================================================
    # CORE COMPANY MEMORIES STORAGE (memory/)
    # =========================================================================

    def get_memory_file_path(self) -> str:
        return os.path.join(self.memory_dir, "company_memory.json")

    def save_memories(self, memories: List[Dict[str, Any]]) -> bool:
        try:
            path = self.get_memory_file_path()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(memories, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving memories: {e}")
            return False

    def load_memories(self) -> List[Dict[str, Any]]:
        path = self.get_memory_file_path()
        if not os.path.exists(path):
            # Prepopulate with standard guidelines if empty
            defaults = [
                {
                    "id": "mem_1",
                    "text": "Target early-adopter tech professionals first to validate our product value.",
                    "category": "Strategy"
                },
                {
                    "id": "mem_2",
                    "text": "Codebase scalability is a priority; CTO prefers robust serverless setups.",
                    "category": "Tech Stack"
                }
            ]
            self.save_memories(defaults)
            return defaults
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading memories: {e}")
            return []

    def add_memory_item(self, text: str, category: str) -> Dict[str, Any]:
        memories = self.load_memories()
        item_id = f"mem_{int(time.time() * 1000)}"
        new_item = {
            "id": item_id,
            "text": text,
            "category": category
        }
        memories.append(new_item)
        self.save_memories(memories)
        return new_item

    def delete_memory_item(self, item_id: str) -> bool:
        memories = self.load_memories()
        filtered = [m for m in memories if m.get("id") != item_id]
        if len(filtered) < len(memories):
            self.save_memories(filtered)
            return True
        return False

    # =========================================================================
    # PERSISTENT CHAT HISTORY STORAGE (memory/chat_memory.json)
    # =========================================================================

    def get_chat_memory_path(self) -> str:
        return os.path.join(self.memory_dir, "chat_memory.json")

    def save_chat_history(self, chat_history: List[Dict[str, Any]]) -> bool:
        try:
            path = self.get_chat_memory_path()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(chat_history, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving chat history: {e}")
            return False

    def load_chat_history(self) -> List[Dict[str, Any]]:
        path = self.get_chat_memory_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return []

    def add_chat_entry(self, topic: str, mode: str, day: int, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        history = self.load_chat_history()
        entry_id = f"chat_{int(time.time() * 1000)}"
        new_entry = {
            "id": entry_id,
            "topic": topic,
            "mode": mode,
            "day": day,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "messages": messages
        }
        history.append(new_entry)
        self.save_chat_history(history)
        return new_entry

    def clear_chat_history(self) -> bool:
        try:
            path = self.get_chat_memory_path()
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception as e:
            print(f"Error clearing chat history: {e}")
            return False

