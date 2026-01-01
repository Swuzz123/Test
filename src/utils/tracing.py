import time
import json
from datetime import datetime
from typing import Optional, Dict

# ============================================================================
# LOGGING & TRACING SYSTEM
# ============================================================================
class AgentLogger:
  """Comprehensive logging and tracing for multi-agent system"""
  
  def __init__(self):
    self.logs = []
    self.start_time = None
    self.phase_times = {}
      
  def start_session(self, project_name: str):
    self.start_time = time.time()
    self.log("SESSION_START", f"Starting SRS generation for: {project_name}", level="INFO")
      
  def log(self, event_type: str, message: str, data: Optional[Dict] = None, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    elapsed = time.time() - self.start_time if self.start_time else 0
    
    log_entry = {
      "timestamp": timestamp,
      "elapsed_seconds": round(elapsed, 2),
      "level": level,
      "event_type": event_type,
      "message": message,
      "data": data or {}
    }
    
    self.logs.append(log_entry)
    
    # Console output with colors
    color_codes = {
      "INFO": "\033[94m",      # Blue
      "SUCCESS": "\033[92m",   # Green
      "WARNING": "\033[93m",   # Yellow
      "ERROR": "\033[91m",     # Red
      "TOOL": "\033[96m",      # Cyan
      "AGENT": "\033[95m"      # Magenta
    }
    
    reset = "\033[0m"
    color = color_codes.get(level, "")
    
    print(f"{color}[{timestamp}] [{level}] {event_type}: {message}{reset}")
    if data and level in ["TOOL", "ERROR"]:
      print(f"{color}  -> Data: {json.dumps(data, indent=2)[:200]}...{reset}")
  
  def start_phase(self, phase_name: str):
    self.phase_times[phase_name] = time.time()
    self.log("PHASE_START", f"Starting phase: {phase_name}", level="INFO")
  
  def end_phase(self, phase_name: str):
    if phase_name in self.phase_times:
        duration = time.time() - self.phase_times[phase_name]
        self.log("PHASE_END", f"Completed phase: {phase_name}", 
                  data={"duration_seconds": round(duration, 2)}, level="SUCCESS")
  
  def export_trace(self, filename: str = "srs_trace.json"):
    """Export full trace log to JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
      json.dump({
        "session_info": {
          "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
          "total_duration": round(time.time() - self.start_time, 2)
        },
        "logs": self.logs
      }, f, indent=2, ensure_ascii=False)
    
    print(f"\nTrace log exported to: {filename}")

# Global logger instance
logger = AgentLogger()