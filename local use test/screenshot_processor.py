import asyncio
import base64
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

@dataclass
class ToolResult:
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None

class ComputerInteraction:
    def __init__(self, width: int = 1024, height: int = 768):
        self.width = width
        self.height = height
        self.display_num = 1
        self._display_prefix = f"DISPLAY=:{self.display_num} "
        self.xdotool = f"{self._display_prefix}xdotool"
        self._screenshot_delay = 2.0
        self.output_dir = Path("/tmp/outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def take_screenshot(self) -> ToolResult:
        """Take a screenshot and return the base64 encoded image."""
        try:
            # Use the existing screenshot functionality
            screenshot_cmd = f"{self._display_prefix}gnome-screenshot -f {self.output_dir}/screenshot.png -p"
            process = await asyncio.create_subprocess_shell(
                screenshot_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                screenshot_path = self.output_dir / "screenshot.png"
                if screenshot_path.exists():
                    base64_image = base64.b64encode(screenshot_path.read_bytes()).decode()
                    return ToolResult(output="Screenshot captured successfully", base64_image=base64_image)
            
            return ToolResult(error=f"Screenshot failed: {stderr.decode()}")
        except Exception as e:
            return ToolResult(error=f"Error taking screenshot: {str(e)}")

    async def process_tool_use(self, action: str, **kwargs) -> ToolResult:
        """Process different tool actions like mouse movements, keyboard input, etc."""
        try:
            if action == "mouse_move":
                x, y = kwargs.get("coordinate", (0, 0))
                cmd = f"{self.xdotool} mousemove --sync {x} {y}"
            elif action == "type":
                text = kwargs.get("text", "")
                cmd = f"{self.xdotool} type --delay 12 -- '{text}'"
            elif action == "left_click":
                cmd = f"{self.xdotool} click 1"
            elif action == "right_click":
                cmd = f"{self.xdotool} click 3"
            elif action == "double_click":
                cmd = f"{self.xdotool} click --repeat 2 --delay 500 1"
            else:
                return ToolResult(error=f"Unsupported action: {action}")

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # Take a screenshot after the action
            await asyncio.sleep(self._screenshot_delay)
            screenshot_result = await self.take_screenshot()

            return ToolResult(
                output=stdout.decode() if stdout else "Action completed",
                error=stderr.decode() if stderr else None,
                base64_image=screenshot_result.base64_image
            )
        except Exception as e:
            return ToolResult(error=f"Error processing tool action: {str(e)}")

async def main():
    # Example usage
    computer = ComputerInteraction()
    
    # Take initial screenshot
    result = await computer.take_screenshot()
    print("Screenshot result:", result.output or result.error)
    
    # Example tool use
    actions = [
        ("mouse_move", {"coordinate": (100, 100)}),
        ("left_click", {}),
        ("type", {"text": "Hello World"}),
    ]
    
    for action, kwargs in actions:
        result = await computer.process_tool_use(action, **kwargs)
        print(f"\nAction {action} result:", result.output or result.error)

if __name__ == "__main__":
    asyncio.run(main()) 