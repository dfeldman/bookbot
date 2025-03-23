import unittest
import os
import json
import tempfile
import shutil
from unittest import mock
import datetime

# Import the module to test
from action import (
    TokenTracker, Command, Action, ActionStatus, CommandRegistry,
    is_action_running, kill_running_action, get_recent_actions,
    STATE_FILE
)


# Mock classes for testing
class MockDoc:
    def __init__(self, name, properties=None, text=""):
        self.name = name
        self._properties = properties or {}
        self._text = text
    
    def get_property(self, key, default=None):
        return self._properties.get(key, default)
    
    def set_property(self, key, value):
        self._properties[key] = value
    
    def get_text(self):
        return self._text
    
    def update_text(self, text):
        self._text = text


class MockDocRepo:
    def __init__(self):
        self.docs = {}
    
    def create_doc(self, name, initial_properties=None, initial_text=""):
        doc = MockDoc(name, initial_properties, initial_text)
        self.docs[name] = doc
        return doc
    
    def get_doc(self, name):
        return self.docs.get(name)


# Test Command implementation
class TestCommand(Command):
    @property
    def name(self):
        return "test-command"
    
    @property
    def description(self):
        return "Test command"
    
    def execute(self, args):
        self.update_status("Running test command")
        if args and args[0] == "fail":
            return False
        return True


# Register the test command
CommandRegistry.register(TestCommand)


class TokenTrackerTest(unittest.TestCase):
    """Test the TokenTracker class."""
    
    def test_token_tracking(self):
        tracker = TokenTracker()
        self.assertEqual(tracker.input_tokens, 0)
        self.assertEqual(tracker.output_tokens, 0)
        
        tracker.add_tokens(100, 200)
        self.assertEqual(tracker.input_tokens, 100)
        self.assertEqual(tracker.output_tokens, 200)
        
        tracker.reset()
        self.assertEqual(tracker.input_tokens, 0)
        self.assertEqual(tracker.output_tokens, 0)
        
        tracker.add_tokens(50, 75)
        self.assertEqual(tracker.to_dict(), {"input_tokens": 50, "output_tokens": 75})


class CommandTest(unittest.TestCase):
    """Test the Command base class."""
    
    def setUp(self):
        self.doc_repo = MockDocRepo()
        self.command = TestCommand(self.doc_repo)
    
    def test_command_properties(self):
        self.assertEqual(self.command.name, "test-command")
        self.assertEqual(self.command.description, "Test command")
    
    def test_command_execution(self):
        # Test successful execution
        result = self.command.execute([])
        self.assertTrue(result)
        self.assertEqual(self.command.get_status(), "Running test command")
        
        # Test failed execution
        result = self.command.execute(["fail"])
        self.assertFalse(result)
    
    def test_command_status(self):
        self.command.update_status("Custom status")
        self.assertEqual(self.command.get_status(), "Custom status")
    
    def test_token_usage(self):
        self.command.token_tracker.add_tokens(100, 200)
        usage = self.command.get_token_usage()
        self.assertEqual(usage, {"input_tokens": 100, "output_tokens": 200})


class ActionTest(unittest.TestCase):
    """Test the Action class."""
    
    def setUp(self):
        self.doc_repo = MockDocRepo()
        self.command = TestCommand(self.doc_repo)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    
    def test_action_initialization(self):
        action = Action(self.command, ["arg1"], actions_dir=self.temp_dir)
        
        self.assertEqual(action.command, self.command)
        self.assertEqual(action.args, ["arg1"])
        self.assertEqual(action.status, ActionStatus.RUNNING)
        self.assertIsNotNone(action.start_time)
        self.assertIsNone(action.end_time)
    
    def test_action_run_success(self):
        action = Action(self.command, [], actions_dir=self.temp_dir)
        
        result = action.run()
        self.assertTrue(result)
        self.assertEqual(action.status, ActionStatus.SUCCESS)
        self.assertIsNotNone(action.end_time)
        
        # Check log file exists
        self.assertTrue(os.path.exists(action.log_file))
    
    def test_action_run_failure(self):
        action = Action(self.command, ["fail"], actions_dir=self.temp_dir)
        
        result = action.run()
        self.assertFalse(result)
        self.assertEqual(action.status, ActionStatus.FAILURE)
    
    def test_document_tracking(self):
        action = Action(self.command, [], actions_dir=self.temp_dir)
        
        action.record_input_doc("input1")
        action.record_output_doc("output1")
        
        self.assertEqual(action.input_docs, ["input1"])
        self.assertEqual(action.output_docs, ["output1"])
        
        action.run()
        
        # Check log contains document records
        with open(action.log_file, 'r') as f:
            log_data = json.load(f)
            self.assertEqual(log_data["input_docs"], ["input1"])
            self.assertEqual(log_data["output_docs"], ["output1"])
    
    def test_state_file(self):
        action = Action(self.command, ["arg1"], actions_dir=self.temp_dir)
        
        action.update_state_file()
        self.assertTrue(os.path.exists(STATE_FILE))
        
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            self.assertEqual(state["command"], "test-command")
            self.assertEqual(state["args"], ["arg1"])
            self.assertEqual(state["status"], ActionStatus.RUNNING)


class UtilityFunctionsTest(unittest.TestCase):
    """Test the utility functions."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    
    @mock.patch('action.os.kill')
    @mock.patch('action.os.path.exists')
    def test_is_action_running(self, mock_exists, mock_kill):
        # Test when state file doesn't exist
        mock_exists.return_value = False
        result = is_action_running()
        self.assertIsNone(result)
        
        # Test when state file exists but process is not running
        mock_exists.return_value = True
        mock_kill.side_effect = OSError()
        
        # Create a state file
        with open(STATE_FILE, 'w') as f:
            json.dump({"pid": 12345}, f)
        
        result = is_action_running()
        self.assertIsNone(result)
        mock_kill.assert_called_with(12345, 0)
    
    @mock.patch('action.os.kill')
    @mock.patch('action.os.path.exists')
    def test_kill_running_action(self, mock_exists, mock_kill):
        mock_exists.return_value = True
        
        # Create a state file
        with open(STATE_FILE, 'w') as f:
            json.dump({"pid": 12345}, f)
        
        result = kill_running_action()
        self.assertTrue(result)
        
        # SIGTERM should have been sent
        import signal
        mock_kill.assert_any_call(12345, signal.SIGTERM)
    
    def test_get_recent_actions(self):
        # Create some action log files
        for i in range(3):
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=i)
            filename = timestamp.strftime("%Y-%m-%d_%H-%M-%S") + f"_action{i}.json"
            filepath = os.path.join(self.temp_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump({
                    "command": f"action{i}",
                    "status": ActionStatus.SUCCESS
                }, f)
            
            # Add a small sleep to ensure file modification times are ordered
            import time
            time.sleep(0.1)
        
        # Get recent actions
        actions = get_recent_actions(count=2, actions_dir=self.temp_dir)
        
        self.assertEqual(len(actions), 2)
        # The most recent file should be action2 (the last one created)
        self.assertEqual(actions[0]["command"], "action2")
        self.assertEqual(actions[1]["command"], "action1")


class CommandRegistryTest(unittest.TestCase):
    """Test the CommandRegistry."""
    
    def setUp(self):
        self.doc_repo = MockDocRepo()
    
    def test_command_registration(self):
        # TestCommand is already registered in the global setup
        command_class = CommandRegistry.get_command_class("test-command")
        self.assertIsNotNone(command_class)
        
        # Create a command instance
        command = CommandRegistry.create_command("test-command", self.doc_repo)
        self.assertIsNotNone(command)
        self.assertEqual(command.name, "test-command")
        
        # Test with non-existent command
        command = CommandRegistry.create_command("nonexistent", self.doc_repo)
        self.assertIsNone(command)
    
    def test_get_all_commands(self):
        commands = CommandRegistry.get_all_commands()
        self.assertIn("test-command", commands)
        self.assertEqual(commands["test-command"]["description"], "Test command")


if __name__ == '__main__':
    unittest.main()