#!/usr/bin/env python3
"""
Command Line Interface for BookBot

This module provides a CLI entry point for the BookBot writing system,
allowing users to run commands, track actions, and manage the writing process.
"""

import os
import sys
import argparse
import logging
import signal
import traceback
from typing import List, Dict, Any, Optional
import importlib
import json
import inspect

# Import command and action handling
from actions import (
    Command, Action, CommandRegistry, is_action_running, 
    kill_running_action, get_recent_actions, render_action_log_as_text,
    WriteChapterCommand
)

# Import document handling
from doc import Doc, DocRepo

# Import other components as needed
import outline_util



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Define default paths
DEFAULT_REPO_PATH = os.environ.get("BOOKBOT_REPO_PATH", "./book_repo")
DEFAULT_COMMANDS_MODULE = "commands"


def register_built_in_commands():
    """Register built-in commands with the command registry."""
    CommandRegistry.register(WriteChapterCommand)
    # Register other built-in commands here


def discover_and_register_commands(commands_module: str = DEFAULT_COMMANDS_MODULE):
    """
    Discover and register commands from the specified module.
    
    Args:
        commands_module: Name of the module containing commands
    """
    try:
        # Import the commands module
        module = importlib.import_module(commands_module)
        
        # Find all Command subclasses in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, Command) and 
                obj != Command):  # Exclude the base class
                
                CommandRegistry.register(obj)
                logger.debug(f"Discovered and registered command: {name}")
                
    except ImportError:
        logger.warning(f"Could not import commands module: {commands_module}")
    except Exception as e:
        logger.error(f"Error discovering commands: {str(e)}")


def load_commands() -> Dict[str, Dict[str, Any]]:
    """
    Load all available commands.
    
    Returns:
        Dictionary mapping command names to their metadata
    """
    # Register built-in commands
    register_built_in_commands()
    
    # Discover and register commands from modules
    discover_and_register_commands()
    
    # Get all registered commands
    return CommandRegistry.get_all_commands()


def handle_interrupt(action: Action, signum, frame):
    """
    Handle interrupt signal (SIGINT, SIGTERM).
    
    Args:
        action: Current action being executed
        signum: Signal number
        frame: Current stack frame
    """
    signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    logger.warning(f"\nReceived {signal_name}. Cancelling action and cleaning up...")
    
    # Update action status and end time
    action.status = "failure"
    action.end_time = datetime.datetime.now().isoformat()
    
    # Save the action log
    action.save_log()
    
    # Clean up state file
    if os.path.exists("state.json"):
        os.remove("state.json")
    
    # Exit with error code
    sys.exit(1)


def list_commands(args: argparse.Namespace):
    """
    List all available commands.
    
    Args:
        args: Command-line arguments
    """
    commands = load_commands()
    
    if not commands:
        print("No commands available.")
        return
    
    print(f"\nAvailable commands ({len(commands)}):\n")
    
    # Find the longest command name for formatting
    max_name_len = max(len(name) for name in commands.keys())
    
    # Print each command with its description
    for name, info in sorted(commands.items()):
        description = info.get("description", "No description available")
        print(f"  {name:{max_name_len}} - {description}")
    
    print("\nUse 'cli.py <command> --help' for more information on a specific command.")


def list_history(args: argparse.Namespace):
    """
    List recent action history.
    
    Args:
        args: Command-line arguments
    """
    count = args.count if hasattr(args, 'count') else 10
    actions = get_recent_actions(count)
    
    if not actions:
        print("No action history available.")
        return
    
    print(f"\nRecent actions ({len(actions)}):\n")
    
    for i, action in enumerate(actions):
        # Format timestamp
        timestamp = action.get("start_time", "Unknown")
        if len(timestamp) > 19:  # Trim ISO format for readability
            timestamp = timestamp[:19]
        
        # Get command and status
        command = action.get("command", "Unknown")
        status = action.get("status", "Unknown")
        cmd_args = " ".join(action.get("args", []))
        
        # Format status with color if supported
        status_formatted = status
        if sys.stdout.isatty():  # Check if running in a terminal that supports colors
            if status == "success":
                status_formatted = f"\033[92m{status}\033[0m"  # Green
            elif status == "failure":
                status_formatted = f"\033[91m{status}\033[0m"  # Red
            elif status == "running":
                status_formatted = f"\033[93m{status}\033[0m"  # Yellow
        
        print(f"  {i+1}. [{timestamp}] {command} {cmd_args} - {status_formatted}")
    
    print("\nUse 'cli.py history <index>' to view details of a specific action.")


def show_history_detail(args: argparse.Namespace):
    """
    Show detailed information about a specific action.
    
    Args:
        args: Command-line arguments
    """
    if not hasattr(args, 'index') or args.index is None:
        list_history(args)
        return
    
    # Get recent actions
    actions = get_recent_actions(20)  # Fetch enough to cover likely indexes
    
    if not actions:
        print("No action history available.")
        return
    
    try:
        # Convert to 0-based index and get the action
        index = int(args.index) - 1
        if index < 0 or index >= len(actions):
            print(f"Invalid index. Please choose a number between 1 and {len(actions)}.")
            return
            
        action = actions[index]
        
        # Render the action detail
        detail = render_action_log_as_text(action)
        print("\nAction Details:\n")
        print(detail)
        
    except ValueError:
        print(f"Invalid index: {args.index}. Please use a number.")


def check_running_action():
    """
    Check if an action is currently running.
    
    Returns:
        Action information dict if an action is running, None otherwise
    """
    action_info = is_action_running()
    if action_info:
        command = action_info.get("command", "Unknown")
        args = " ".join(action_info.get("args", []))
        pid = action_info.get("pid", "Unknown")
        status = action_info.get("current_step", "Running")
        
        print(f"\nWARNING: An action is already running:")
        print(f"  Command: {command} {args}")
        print(f"  PID: {pid}")
        print(f"  Status: {status}")
        print("\nUse 'cli.py kill' to terminate the running action if you believe it's stuck.")
        
    return action_info


def kill_action(args: argparse.Namespace):
    """
    Kill a currently running action.
    
    Args:
        args: Command-line arguments
    """
    action_info = check_running_action()
    
    if not action_info:
        print("No action is currently running.")
        return
    
    if not hasattr(args, 'force') or not args.force:
        # Prompt for confirmation unless --force is used
        command = action_info.get("command", "Unknown")
        args_str = " ".join(action_info.get("args", []))
        pid = action_info.get("pid", "Unknown")
        
        confirm = input(f"Kill running action '{command} {args_str}' (PID {pid})? [y/N]: ")
        if confirm.lower() not in ("y", "yes"):
            print("Operation cancelled.")
            return
    
    # Kill the action
    success = kill_running_action()
    if success:
        print("Action terminated successfully.")
    else:
        print("Failed to terminate action. It may have already completed or been killed externally.")


def execute_command(args: argparse.Namespace):
    """
    Execute a command with the provided arguments.
    
    Args:
        args: Command-line arguments
    """
    # Check if a command is already running
    if is_action_running():
        if not hasattr(args, 'force') or not args.force:
            check_running_action()
            return
        else:
            # Force kill the running action if --force is used
            kill_running_action()
    
    # Load all available commands
    available_commands = load_commands()
    
    # Check if the command exists
    if args.command not in available_commands:
        print(f"Unknown command: {args.command}")
        print("\nAvailable commands:")
        for cmd in sorted(available_commands.keys()):
            print(f"  {cmd}")
        return
    
    # Get command info
    command_info = available_commands[args.command]
    command_class_name = command_info.get("class_name")
    
    # Create command instance
    try:
        # Initialize document repository
        doc_repo = DocRepo(args.repo_path)
        
        # Create command instance
        command = CommandRegistry.create_command(args.command, doc_repo, args.api_key)
        
        if not command:
            print(f"Failed to create command instance for {args.command}")
            return
            
        # Get required arguments info
        arg_info = command_class_name.get_arg_info() if hasattr(command_class_name, 'get_arg_info') else {}
        
        # Check if required arguments are provided
        if len(args.args) < len(arg_info):
            print(f"Insufficient arguments for command '{args.command}'")
            print(f"\nUsage: {command.usage}")
            print("\nRequired arguments:")
            for i, (name, desc) in enumerate(arg_info.items()):
                print(f"  {i+1}. {name}: {desc}")
            return
        
        # Create action
        action = Action(command, args.args)
        
        # Set up signal handlers for graceful interruption
        signal.signal(signal.SIGINT, lambda signum, frame: handle_interrupt(action, signum, frame))
        signal.signal(signal.SIGTERM, lambda signum, frame: handle_interrupt(action, signum, frame))
        
        # Run the action
        success = action.run()
        
        if success:
            print(f"\nCommand '{args.command}' completed successfully.")
            
            # Show token usage
            token_usage = command.get_token_usage()
            if token_usage:
                print("\nToken usage:")
                print(f"  Input tokens: {token_usage.get('input_tokens', 0)}")
                print(f"  Output tokens: {token_usage.get('output_tokens', 0)}")
        else:
            print(f"\nCommand '{args.command}' failed.")
        
    except Exception as e:
        print(f"Error executing command '{args.command}': {str(e)}")
        if args.verbose:
            traceback.print_exc()


def setup_argument_parser():
    """
    Set up the argument parser.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="BookBot Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py list                     # List available commands
  python cli.py history                  # Show command history
  python cli.py history 3                # Show details of the 3rd most recent action
  python cli.py write-chapter 3          # Write chapter 3
  python cli.py kill                     # Kill a running action
  python cli.py --dry-run write-chapter 3 # Run in dry-run mode without making API calls
        """
    )
    
    # Global options
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--repo-path', default=DEFAULT_REPO_PATH, help=f'Path to the document repository (default: {DEFAULT_REPO_PATH})')
    parser.add_argument('--api-key', help='OpenRouter API key (default: OPENROUTER_API_KEY environment variable)')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode without making API calls')
    parser.add_argument('--cheap-mode', action='store_true', help='Use cheaper LLM models')
    
    # Set up subparsers for commands
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # List commands
    list_parser = subparsers.add_parser('list', help='List available commands')
    list_parser.set_defaults(func=list_commands)
    
    # Command history
    history_parser = subparsers.add_parser('history', help='Show command history')
    history_parser.add_argument('index', nargs='?', help='Index of the action to show details for')
    history_parser.add_argument('-c', '--count', type=int, default=10, help='Number of actions to show (default: 10)')
    history_parser.set_defaults(func=show_history_detail)
    
    # Kill action
    kill_parser = subparsers.add_parser('kill', help='Kill a running action')
    kill_parser.add_argument('-f', '--force', action='store_true', help='Kill without confirmation')
    kill_parser.set_defaults(func=kill_action)
    
    # If no action is specified, the first positional argument is assumed to be a command
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    return parser


def configure_environment(args: argparse.Namespace):
    """
    Configure environment variables based on command-line arguments.
    
    Args:
        args: Command-line arguments
    """
    # Set up logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Configure dry-run mode
    if args.dry_run:
        os.environ["BOOKBOT_DRY_RUN"] = "true"
        logger.info("Dry-run mode enabled")
    
    # Configure cheap mode
    if args.cheap_mode:
        os.environ["BOOKBOT_CHEAP_MODE"] = "true"
        logger.info("Cheap mode enabled")
    
    # Set API key if provided
    if args.api_key:
        os.environ["OPENROUTER_API_KEY"] = args.api_key
    elif not os.environ.get("OPENROUTER_API_KEY") and not args.dry_run:
        logger.warning("No OpenRouter API key provided. Set the OPENROUTER_API_KEY environment variable or use --api-key")


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Configure environment
    configure_environment(args)
    
    try:
        if args.action:
            # Execute the function associated with the specified action
            args.func(args)
        elif args.command:
            # Execute the specified command
            execute_command(args)
        else:
            # No action or command specified, show help
            parser.print_help()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if hasattr(args, 'verbose') and args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())