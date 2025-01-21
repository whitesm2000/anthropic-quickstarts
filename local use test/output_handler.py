import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class ProcessedOutput:
    action_type: str
    timestamp: str
    success: bool
    message: str
    screenshot_path: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

class OutputHandler:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / "action_log.json"
        self._initialize_log_file()

    def _initialize_log_file(self):
        """Initialize the log file if it doesn't exist"""
        if not self.log_file.exists():
            self.log_file.write_text("[]")

    def save_screenshot(self, base64_image: str, action_id: str) -> Optional[str]:
        """Save a base64 encoded screenshot to a file"""
        try:
            import base64
            screenshot_path = self.output_dir / f"screenshot_{action_id}.png"
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(base64_image))
            return str(screenshot_path)
        except Exception as e:
            print(f"Error saving screenshot: {e}")
            return None

    def process_tool_result(self, result: Dict[str, Any], action_type: str) -> ProcessedOutput:
        """Process the result from a tool operation"""
        from datetime import datetime
        
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        
        # Determine success and create message
        success = result.get("error") is None
        message = result.get("output", "") if success else result.get("error", "Unknown error")
        
        # Handle screenshot if present
        screenshot_path = None
        if result.get("base64_image"):
            screenshot_path = self.save_screenshot(
                result["base64_image"], 
                f"{action_type}_{timestamp.replace(':', '-')}"
            )
        
        # Create processed output
        processed = ProcessedOutput(
            action_type=action_type,
            timestamp=timestamp,
            success=success,
            message=message,
            screenshot_path=screenshot_path,
            additional_data={"raw_output": result.get("output")} if success else {"error": result.get("error")}
        )
        
        # Log the processed output
        self._log_action(processed)
        
        return processed

    def _log_action(self, processed_output: ProcessedOutput):
        """Log the processed output to the log file"""
        try:
            # Read existing logs
            logs = json.loads(self.log_file.read_text())
            
            # Append new log
            logs.append(asdict(processed_output))
            
            # Write updated logs
            self.log_file.write_text(json.dumps(logs, indent=2))
        except Exception as e:
            print(f"Error logging action: {e}")

    def get_action_history(self) -> list[ProcessedOutput]:
        """Retrieve the action history from the log file"""
        try:
            logs = json.loads(self.log_file.read_text())
            return [ProcessedOutput(**log) for log in logs]
        except Exception as e:
            print(f"Error reading action history: {e}")
            return []

# Example usage
if __name__ == "__main__":
    # Create handler
    handler = OutputHandler()
    
    # Example tool result
    example_result = {
        "output": "Action completed successfully",
        "base64_image": "SGVsbG8gV29ybGQ=",  # Example base64 string
    }
    
    # Process result
    processed = handler.process_tool_result(example_result, "test_action")
    print(f"Processed output: {processed}")
    
    # Get history
    history = handler.get_action_history()
    print(f"\nAction history: {history}") 