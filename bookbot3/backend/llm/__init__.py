"""
LLM module for BookBot.

This module provides the main interface for making LLM calls.
Currently uses the fake LLM implementation, but is designed to be
easily extended to support real LLM providers like OpenRouter.
"""

from typing import Optional, Callable, Dict, Any
from .fake_llm import FakeLLMCall, get_fake_api_token_status

# Import OpenRouter validation
try:
    from .openrouter import validate_openrouter_token
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False
    validate_openrouter_token = None


class LLMCall:
    """
    Main LLM call interface.
    
    This class provides a unified interface for making LLM calls
    regardless of the underlying provider.
    """
    
    def __init__(
        self,
        model: str,
        api_key: str,
        target_word_count: int,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        llm_params: Optional[dict] = None,
        model_mode: Optional[str] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize an LLM call.
        
        Args:
            model: The model name to use
            api_key: The API key for the LLM provider
            target_word_count: Target number of words to generate
            prompt: The user prompt for the LLM.
            system_prompt: The system prompt for the LLM.
            llm_params: Other parameters for the LLM call (e.g., temperature).
            model_mode: Optional model mode override (e.g., "fake")
            log_callback: Optional callback for logging progress
        """
        self.model = model
        self.api_key = api_key
        self.target_word_count = target_word_count
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.llm_params = llm_params if llm_params is not None else {}
        self.model_mode = model_mode
        self.log_callback = log_callback
        
        # Results (set after execute())
        self.output_text: Optional[str] = None
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.cost: float = 0.0
        self.stop_reason: str = ""
        self.execution_time: float = 0.0
        self.error_status: Optional[str] = None
        
        # Determine which implementation to use
        self._use_fake = self._should_use_fake()
        
        if self._use_fake:
            self._impl = FakeLLMCall(
                model=self.model,
                api_key=self.api_key,
                target_word_count=self.target_word_count,
                prompt=self.prompt,
                system_prompt=self.system_prompt,
                llm_params=self.llm_params,
                log_callback=self.log_callback
            )
        else:
            # TODO: Implement real LLM providers
            raise NotImplementedError("Real LLM providers not yet implemented")
    
    def set_prompt(self, prompt: str):
        """Set the prompt for the LLM call."""
        self.prompt = prompt # Update self.prompt as well
        # Ensure _impl is initialized and has a prompt attribute or setter
        if hasattr(self, '_impl') and self._impl:
            if hasattr(self._impl, 'set_prompt') and callable(self._impl.set_prompt):
                self._impl.set_prompt(prompt)
            elif hasattr(self._impl, 'prompt'):
                self._impl.prompt = prompt
            # If neither, the underlying implementation might not support dynamic prompt setting after init
    
    def _should_use_fake(self) -> bool:
        """Determine whether to use the fake LLM implementation."""
        # Always use fake for now since real LLM providers aren't implemented
        return True
        
        # Future logic:
        # if self.model_mode == "fake":
        #     return True
        # if not self.api_key:
        #     return True
        # return False
    
    def execute(self) -> bool:
        """
        Execute the LLM call.
        
        Returns:
            bool: True if successful, False if error
        """
        if self.model_mode and self.log_callback:
            self.log_callback(f"Model mode override: {self.model_mode}")
        
        success = self._impl.execute()
        
        # Copy results from implementation
        self.output_text = self._impl.output_text
        self.input_tokens = self._impl.input_tokens
        self.output_tokens = self._impl.output_tokens
        self.cost = self._impl.cost
        self.stop_reason = self._impl.stop_reason
        self.execution_time = self._impl.execution_time
        self.error_status = self._impl.error_status
        
        return success
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the LLM call results to a dictionary."""
        return {
            'model': self.model,
            'model_mode': self.model_mode,
            'target_word_count': self.target_word_count,
            'output_text': self.output_text,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'cost': self.cost,
            'stop_reason': self.stop_reason,
            'execution_time': self.execution_time,
            'error_status': self.error_status,
            'used_fake': self._use_fake
        }


def get_api_token_status(api_key: str) -> Dict[str, Any]:
    """
    Get the status and balance for an API token.
    
    Args:
        api_key: The API key to check
    
    Returns:
        dict: Status information including balance or error
    """
    # Special development/test tokens use fake validation
    if api_key in ['test-key', 'dev-token', 'fake-token']:
        return get_fake_api_token_status(api_key)
    
    # Try real OpenRouter validation first if available
    if OPENROUTER_AVAILABLE and validate_openrouter_token:
        try:
            result = validate_openrouter_token(api_key)
            if result.get('valid') or 'error' in result:
                return result
        except Exception as e:
            print(f"OpenRouter validation failed: {e}")
    
    # Fallback to fake implementation for development
    return get_fake_api_token_status(api_key)
