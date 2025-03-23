import os
import json
import time
import signal
import inspect
import logging
import datetime
import subprocess
import traceback
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union, Type, Set, Callable
from pathlib import Path
from functools import wraps

# Import existing classes
from bot import BookWriter, BotType, LLMError, generate_content

# Configure logging
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_ACTIONS_DIR = "actions"
STATE_FILE = "state.json"


class TokenTracker:
    """
    Utility class for tracking token usage across commands.
    """
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
    
    def add_tokens(self, input_tokens: int, output_tokens: int):
        """Add tokens to the running count"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
    
    def reset(self):
        """Reset token counts"""
        self.input_tokens = 0
        self.output_tokens = 0
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for serialization"""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens
        }


# Decorator to automatically track tokens from generate_content calls
def track_tokens(token_tracker):
    """
    Decorator to track tokens used in generate_content calls.
    
    Args:
        token_tracker: TokenTracker instance to update
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Call the original function
            result = func(*args, **kwargs)
            
            # Get the output document to extract token usage
            if 'output_doc_name' in kwargs:
                doc_name = kwargs['output_doc_name']
                doc_repo = kwargs.get('doc_repo', None)
                
                if doc_repo:
                    doc = doc_repo.get_doc(doc_name)
                    if doc:
                        # Extract token usage from document properties
                        input_tokens = doc.get_property("input_tokens", 0)
                        output_tokens = doc.get_property("output_tokens", 0)
                        
                        # Update token tracker
                        token_tracker.add_tokens(input_tokens, output_tokens)
            
            return result
        return wrapper
    return decorator


# Enhanced version of generate_content that tracks tokens
def tracked_generate_content(token_tracker: TokenTracker, **kwargs):
    """
    Wrapper for generate_content that tracks token usage.
    
    Args:
        token_tracker: TokenTracker instance to update
        **kwargs: Arguments to pass to generate_content
    
    Returns:
        Result from generate_content
    """
    result = generate_content(**kwargs)
    
    # Extract token usage from output document
    if 'output_doc_name' in kwargs and 'doc_repo' in kwargs:
        doc_name = kwargs['output_doc_name']
        doc_repo = kwargs['doc_repo']
        
        doc = doc_repo.get_doc(doc_name)
        if doc:
            # Extract token usage from document properties
            input_tokens = doc.get_property("input_tokens", 0)
            output_tokens = doc.get_property("output_tokens", 0)
            
            # Update token tracker
            token_tracker.add_tokens(input_tokens, output_tokens)
    
    return result


# Action status enum
class ActionStatus:
    """Status values for Actions"""
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


class Command(ABC):
    """
    Base class for all commands.
    
    Commands define specific book writing workflows like writing chapters,
    editing content, generating outlines, etc. Each command should implement
    the execute method and provide detailed documentation.
    """
    
    def __init__(self, doc_repo, api_key: Optional[str] = None):
        """
        Initialize a Command.
        
        Args:
            doc_repo: Document repository
            api_key: OpenRouter API key (default: None, will use env var)
        """
        self.doc_repo = doc_repo
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.token_tracker = TokenTracker()
        self.book_writer = BookWriter(doc_repo, api_key=self.api_key)
        
        # For status tracking
        self.current_status = "Initializing"
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the command name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a brief description of the command"""
        pass
    
    @property
    def usage(self) -> str:
        """Return usage instructions"""
        return f"{self.name} [args]"
    
    @abstractmethod
    def execute(self, args: List[str]) -> bool:
        """
        Execute the command with the given arguments.
        
        Args:
            args: List of command arguments
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def update_status(self, status: str):
        """
        Update the current status of the command.
        
        Args:
            status: New status message
        """
        self.current_status = status
        logger.info(f"Status: {status}")
    
    def get_status(self) -> str:
        """
        Get the current status of the command.
        
        Returns:
            Current status message
        """
        return self.current_status
    
    def get_token_usage(self) -> Dict[str, int]:
        """
        Get the current token usage.
        
        Returns:
            Dictionary with input_tokens and output_tokens
        """
        return self.token_tracker.to_dict()
    
    def generate_content(self, **kwargs) -> str:
        """
        Wrapper for generate_content that tracks token usage.
        
        Args:
            **kwargs: Arguments to pass to generate_content
            
        Returns:
            Generated content
        """
        return tracked_generate_content(self.token_tracker, 
                                      doc_repo=self.doc_repo, 
                                      api_key=self.api_key,
                                      **kwargs)
    
    @classmethod
    def get_arg_info(cls) -> Dict[str, str]:
        """
        Get information about required arguments.
        
        Returns:
            Dictionary of argument names and descriptions
        """
        return {}


class Action:
    """
    Represents a running Command with metadata.
    
    Actions track the execution of commands, logging their progress,
    success/failure status, and token usage.
    """
    
    def __init__(self, command: Command, args: List[str], actions_dir: str = DEFAULT_ACTIONS_DIR):
        """
        Initialize an Action.
        
        Args:
            command: Command to execute
            args: Command arguments
            actions_dir: Directory to store action logs
        """
        self.command = command
        self.args = args
        self.actions_dir = actions_dir
        self.pid = os.getpid()
        self.start_time = datetime.datetime.now().isoformat()
        self.end_time = None
        self.status = ActionStatus.RUNNING
        self.input_docs = []
        self.output_docs = []
        self.log_file = self._create_log_file()
        
        # Ensure actions directory exists
        os.makedirs(actions_dir, exist_ok=True)
    
    def _create_log_file(self) -> str:
        """
        Create a log file name for this action.
        
        Returns:
            Path to the log file
        """
        # Format: actions/YYYY-MM-DD_HH-MM-SS_CommandName.json
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}_{self.command.name}.json"
        return os.path.join(self.actions_dir, filename)
    
    def update_state_file(self):
        """Update the state file with current action information."""
        state = {
            "pid": self.pid,
            "command": self.command.name,
            "args": self.args,
            "start_time": self.start_time,
            "status": self.status,
            "current_step": self.command.get_status(),
            "log_file": self.log_file
        }
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
    def record_input_doc(self, doc_name: str):
        """
        Record an input document used by this action.
        
        Args:
            doc_name: Name of the input document
        """
        if doc_name not in self.input_docs:
            self.input_docs.append(doc_name)
    
    def record_output_doc(self, doc_name: str):
        """
        Record an output document produced by this action.
        
        Args:
            doc_name: Name of the output document
        """
        if doc_name not in self.output_docs:
            self.output_docs.append(doc_name)
    
    def save_log(self):
        """Save the action log to a JSON file."""
        log_data = {
            "command": self.command.name,
            "args": self.args,
            "pid": self.pid,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "input_docs": self.input_docs,
            "output_docs": self.output_docs,
            "token_usage": self.command.get_token_usage()
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def run(self) -> bool:
        """
        Run the command and track its execution.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting action: {self.command.name} {' '.join(self.args)}")
        
        try:
            # Update state file to indicate we're running
            self.update_state_file()
            
            # Execute the command
            success = self.command.execute(self.args)
            
            # Update status based on result
            self.status = ActionStatus.SUCCESS if success else ActionStatus.FAILURE
            self.end_time = datetime.datetime.now().isoformat()
            
            # Save the final log
            self.save_log()
            
            # Clean up state file
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            
            logger.info(f"Action completed with status: {self.status}")
            return success
            
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update status to failure
            self.status = ActionStatus.FAILURE
            self.end_time = datetime.datetime.now().isoformat()
            
            # Save the log with error information
            self.save_log()
            
            # Clean up state file
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            
            return False


def is_action_running() -> Optional[Dict[str, Any]]:
    """
    Check if an action is currently running.
    
    Returns:
        Action information dictionary if an action is running, None otherwise
    """
    if not os.path.exists(STATE_FILE):
        return None
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        # Check if the process is still running
        pid = state.get("pid")
        if pid:
            try:
                # Send signal 0 to check if process exists (doesn't actually send a signal)
                os.kill(pid, 0)
                return state
            except OSError:
                # Process is not running, clean up state file
                os.remove(STATE_FILE)
                return None
        
        return None
    
    except (json.JSONDecodeError, KeyError):
        # Invalid state file, remove it
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        return None


def kill_running_action() -> bool:
    """
    Kill a currently running action.
    
    Returns:
        True if an action was killed, False otherwise
    """
    action_info = is_action_running()
    if not action_info:
        return False
    
    pid = action_info.get("pid")
    if not pid:
        return False
    
    try:
        # Send SIGTERM to the process
        os.kill(pid, signal.SIGTERM)
        
        # Wait a moment for clean shutdown
        time.sleep(1)
        
        # Check if it's still running, force kill if needed
        try:
            os.kill(pid, 0)
            # Process is still running, send SIGKILL
            os.kill(pid, signal.SIGKILL)
        except OSError:
            # Process has already terminated
            pass
        
        # Clean up state file
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        
        return True
    
    except OSError:
        # Could not kill process
        return False


def get_recent_actions(count: int = 10, actions_dir: str = DEFAULT_ACTIONS_DIR) -> List[Dict[str, Any]]:
    """
    Get a list of recent actions.
    
    Args:
        count: Maximum number of actions to return
        actions_dir: Directory containing action logs
    
    Returns:
        List of action information dictionaries, sorted by start time (newest first)
    """
    if not os.path.exists(actions_dir):
        return []
    
    action_files = []
    for filename in os.listdir(actions_dir):
        if filename.endswith('.json'):
            action_files.append(os.path.join(actions_dir, filename))
    
    # Sort files by modification time (newest first)
    action_files.sort(key=os.path.getmtime, reverse=True)
    
    # Read the most recent files
    actions = []
    for file_path in action_files[:count]:
        try:
            with open(file_path, 'r') as f:
                action_data = json.load(f)
                # Add the file path for reference
                action_data['log_file'] = file_path
                actions.append(action_data)
        except (json.JSONDecodeError, KeyError):
            # Skip invalid files
            continue
    
    return actions


def get_available_commands() -> Dict[str, Dict[str, str]]:
    """
    Get a dictionary of all available commands with their documentation.
    
    Returns:
        Dictionary mapping command names to their documentation
    """
    # This function assumes all Command subclasses are imported
    commands = {}
    
    # Find all Command subclasses
    for name, obj in globals().items():
        if (inspect.isclass(obj) and 
            issubclass(obj, Command) and 
            obj != Command):  # Exclude the base class
            
            # Create an instance to access properties
            # This assumes all Command subclasses accept doc_repo as first arg
            try:
                instance = obj(None)
                cmd_name = instance.name
                commands[cmd_name] = {
                    "description": instance.description,
                    "usage": instance.usage,
                    "args": obj.get_arg_info(),
                    "class_name": name
                }
            except:
                # Skip commands that can't be instantiated this way
                pass
    
    return commands


def render_action_log_as_text(action_data: Dict[str, Any]) -> str:
    """
    Render an action log as formatted text.
    
    Args:
        action_data: Action log data
    
    Returns:
        Formatted text representation
    """
    lines = []
    lines.append(f"Command: {action_data.get('command')}")
    lines.append(f"Arguments: {' '.join(action_data.get('args', []))}")
    lines.append(f"Start Time: {action_data.get('start_time')}")
    lines.append(f"End Time: {action_data.get('end_time', 'N/A')}")
    lines.append(f"Status: {action_data.get('status', 'unknown')}")
    
    # Add input documents
    lines.append("\nInput Documents:")
    for doc in action_data.get('input_docs', []):
        lines.append(f"  - {doc}")
    
    # Add output documents
    lines.append("\nOutput Documents:")
    for doc in action_data.get('output_docs', []):
        lines.append(f"  - {doc}")
    
    # Add token usage
    token_usage = action_data.get('token_usage', {})
    lines.append("\nToken Usage:")
    lines.append(f"  Input Tokens: {token_usage.get('input_tokens', 0)}")
    lines.append(f"  Output Tokens: {token_usage.get('output_tokens', 0)}")
    
    return "\n".join(lines)


def render_action_log_as_html(action_data: Dict[str, Any]) -> str:
    """
    Render an action log as HTML.
    
    Args:
        action_data: Action log data
    
    Returns:
        HTML representation
    """
    html = []
    html.append("<div class='action-log'>")
    html.append(f"<h2>Command: {action_data.get('command')}</h2>")
    
    # Basic information
    html.append("<table class='action-info'>")
    html.append("<tr><th>Arguments</th><td>" + " ".join(action_data.get('args', [])) + "</td></tr>")
    html.append(f"<tr><th>Start Time</th><td>{action_data.get('start_time')}</td></tr>")
    html.append(f"<tr><th>End Time</th><td>{action_data.get('end_time', 'N/A')}</td></tr>")
    
    # Style status based on value
    status = action_data.get('status', 'unknown')
    status_class = {
        ActionStatus.SUCCESS: "success",
        ActionStatus.FAILURE: "failure",
        ActionStatus.RUNNING: "running"
    }.get(status, "unknown")
    
    html.append(f"<tr><th>Status</th><td class='status-{status_class}'>{status}</td></tr>")
    html.append("</table>")
    
    # Add input documents
    html.append("<h3>Input Documents</h3>")
    html.append("<ul>")
    for doc in action_data.get('input_docs', []):
        html.append(f"<li>{doc}</li>")
    html.append("</ul>")
    
    # Add output documents
    html.append("<h3>Output Documents</h3>")
    html.append("<ul>")
    for doc in action_data.get('output_docs', []):
        html.append(f"<li>{doc}</li>")
    html.append("</ul>")
    
    # Add token usage
    token_usage = action_data.get('token_usage', {})
    html.append("<h3>Token Usage</h3>")
    html.append("<table class='token-usage'>")
    html.append(f"<tr><th>Input Tokens</th><td>{token_usage.get('input_tokens', 0)}</td></tr>")
    html.append(f"<tr><th>Output Tokens</th><td>{token_usage.get('output_tokens', 0)}</td></tr>")
    html.append("</table>")
    
    html.append("</div>")
    return "\n".join(html)


class CommandRegistry:
    """
    Registry for all available commands.
    
    This class provides a central place to register and lookup commands,
    making it easier to discover available commands and create instances.
    """
    
    _commands: Dict[str, Type[Command]] = {}
    
    @classmethod
    def register(cls, command_class: Type[Command]):
        """
        Register a command class.
        
        Args:
            command_class: Command class to register
        """
        # Create a temporary instance to get the name
        try:
            temp_instance = command_class(None)
            name = temp_instance.name
            cls._commands[name] = command_class
            logger.debug(f"Registered command: {name}")
        except Exception as e:
            logger.error(f"Failed to register command {command_class.__name__}: {str(e)}")
    
    @classmethod
    def get_command_class(cls, name: str) -> Optional[Type[Command]]:
        """
        Get a command class by name.
        
        Args:
            name: Command name
            
        Returns:
            Command class or None if not found
        """
        return cls._commands.get(name)
    
    @classmethod
    def create_command(cls, name: str, doc_repo, api_key: Optional[str] = None) -> Optional[Command]:
        """
        Create a command instance by name.
        
        Args:
            name: Command name
            doc_repo: Document repository
            api_key: OpenRouter API key
            
        Returns:
            Command instance or None if not found
        """
        command_class = cls.get_command_class(name)
        if not command_class:
            return None
        
        return command_class(doc_repo, api_key)
    
    @classmethod
    def get_all_commands(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered commands.
        
        Returns:
            Dictionary mapping command names to their documentation
        """
        result = {}
        
        for name, command_class in cls._commands.items():
            try:
                # Create an instance to access properties
                instance = command_class(None)
                result[name] = {
                    "description": instance.description,
                    "usage": instance.usage,
                    "args": command_class.get_arg_info(),
                    "class_name": command_class.__name__
                }
            except Exception as e:
                logger.error(f"Error getting info for command {name}: {str(e)}")
                # Include basic info even if instantiation fails
                result[name] = {
                    "description": "Error: Could not load command info",
                    "class_name": command_class.__name__,
                    "error": str(e)
                }
        
        return result


# Example command implementation
class WriteChapterCommand(Command):
    """
    Command to write a chapter using a prompt template.
    """
    
    @property
    def name(self) -> str:
        return "write-chapter-example"
    
    @property
    def description(self) -> str:
        return "Write a chapter using a specified prompt template"
    
    @property
    def usage(self) -> str:
        return "write-chapter <chapter_name> <prompt_name> <chapter_number> <outline_doc> <setting_doc> <characters_doc> [<previous_chapter_doc>]"
    
    @classmethod
    def get_arg_info(cls) -> Dict[str, str]:
        return {
            "chapter_name": "Name of the output chapter document",
            "prompt_name": "Name of the prompt template to use",
            "chapter_number": "Chapter number",
            "outline_doc": "Name of the outline document",
            "setting_doc": "Name of the setting document",
            "characters_doc": "Name of the characters document",
            "previous_chapter_doc": "Name of the previous chapter document (optional)"
        }
    
    def execute(self, args: List[str]) -> bool:
        # Validate arguments
        if len(args) < 6:
            logger.error(f"Not enough arguments. Usage: {self.usage}")
            return False
        
        # Parse arguments
        chapter_name = args[0]
        prompt_name = args[1]
        chapter_number = args[2]
        outline_doc_name = args[3]
        setting_doc_name = args[4]
        characters_doc_name = args[5]
        previous_chapter_doc_name = args[6] if len(args) > 6 else ""
        
        self.update_status(f"Starting to write chapter {chapter_number}")
        
        # Get required documents
        outline_doc = self.doc_repo.get_doc(outline_doc_name)
        setting_doc = self.doc_repo.get_doc(setting_doc_name)
        characters_doc = self.doc_repo.get_doc(characters_doc_name)
        
        if not outline_doc:
            logger.error(f"Outline document '{outline_doc_name}' not found")
            return False
        
        if not setting_doc:
            logger.error(f"Setting document '{setting_doc_name}' not found")
            return False
        
        if not characters_doc:
            logger.error(f"Characters document '{characters_doc_name}' not found")
            return False
        
        # Get previous chapter if specified
        previous_chapter_doc = None
        if previous_chapter_doc_name:
            previous_chapter_doc = self.doc_repo.get_doc(previous_chapter_doc_name)
            if not previous_chapter_doc:
                logger.error(f"Previous chapter document '{previous_chapter_doc_name}' not found")
                return False
        
        # Record input documents
        self.update_status("Preparing documents")
        
        # Here we would record input docs if we had access to the Action instance
        # This is handled in the run() method of the Action class
        
        # Set up template variables
        template_vars = {
            "chapter_number": chapter_number,
            "outline": outline_doc,
            "setting": setting_doc,
            "characters": characters_doc,
            "previous_chapter": previous_chapter_doc or ""
        }
        
        # Generate the chapter
        self.update_status(f"Generating chapter {chapter_number} content")
        try:
            content = self.generate_content(
                output_doc_name=chapter_name,
                prompt_doc_name=prompt_name,
                template_vars=template_vars,
                command=f"write_chapter_{chapter_number}"
            )
            
            self.update_status(f"Successfully wrote chapter {chapter_number}")
            return True
            
        except LLMError as e:
            self.update_status(f"Error generating chapter: {str(e)}")
            return False
        
        except Exception as e:
            self.update_status(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return False


# Register the example command
CommandRegistry.register(WriteChapterCommand)