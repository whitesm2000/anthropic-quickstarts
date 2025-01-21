import asyncio
import argparse
from typing import Optional, Tuple
from screenshot_processor import ComputerInteraction
from output_handler import OutputHandler

def parse_coordinates(coord_str: Optional[str]) -> Optional[Tuple[int, int]]:
    """Parse coordinate string in format 'x,y'"""
    if not coord_str:
        return None
    try:
        x, y = map(int, coord_str.split(','))
        return (x, y)
    except ValueError:
        raise argparse.ArgumentTypeError("Coordinates must be in format 'x,y'")

async def main():
    parser = argparse.ArgumentParser(description='Computer Interaction Tool')
    parser.add_argument('action', choices=['screenshot', 'mouse_move', 'left_click', 'right_click', 
                                         'double_click', 'type'], help='Action to perform')
    parser.add_argument('--coordinates', type=str, help='Mouse coordinates in format "x,y"')
    parser.add_argument('--text', type=str, help='Text to type')
    parser.add_argument('--width', type=int, default=1024, help='Screen width')
    parser.add_argument('--height', type=int, default=768, help='Screen height')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory for screenshots and logs')

    args = parser.parse_args()

    # Initialize tools
    computer = ComputerInteraction(width=args.width, height=args.height)
    handler = OutputHandler(output_dir=args.output_dir)

    # Process coordinates if provided
    coordinates = parse_coordinates(args.coordinates) if args.coordinates else None

    # Validate arguments based on action
    if args.action == 'mouse_move' and not coordinates:
        parser.error("mouse_move action requires --coordinates")
    if args.action == 'type' and not args.text:
        parser.error("type action requires --text")

    try:
        # Execute the requested action
        if args.action == 'screenshot':
            result = await computer.take_screenshot()
        else:
            kwargs = {}
            if coordinates:
                kwargs['coordinate'] = coordinates
            if args.text:
                kwargs['text'] = args.text
            result = await computer.process_tool_use(args.action, **kwargs)

        # Process and log the result
        processed = handler.process_tool_result(
            {
                'output': result.output,
                'error': result.error,
                'base64_image': result.base64_image
            },
            args.action
        )

        # Print the result
        if processed.success:
            print(f"Action '{args.action}' completed successfully")
            if processed.screenshot_path:
                print(f"Screenshot saved to: {processed.screenshot_path}")
        else:
            print(f"Error performing '{args.action}': {processed.message}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 