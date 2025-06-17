"""
OpenRouter API integration for BookBot.

This module provides functions for validating OpenRouter API tokens
and checking account balances.
"""

import requests
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


def validate_openrouter_token(api_key: str) -> Dict[str, Any]:
    """
    Validate an OpenRouter API token and get account balance.
    
    Args:
        api_key: The OpenRouter API key to validate
    
    Returns:
        dict: Status information including validity and balance
    """
    if not api_key:
        return {
            'valid': False,
            'error': 'API key is required'
        }
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Try to get account balance/credits
        response = requests.get(
            f"{OPENROUTER_API_BASE}/auth/key",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'valid': True,
                'balance': data.get('data', {}).get('credit_balance', 0.0),
                'currency': 'USD',
                'label': data.get('data', {}).get('label', 'API Key'),
                'usage': data.get('data', {}).get('usage', 0.0)
            }
        elif response.status_code == 401:
            return {
                'valid': False,
                'error': 'Invalid API key'
            }
        elif response.status_code == 403:
            return {
                'valid': False,
                'error': 'API key access denied'
            }
        else:
            logger.warning(f"OpenRouter API returned status {response.status_code}: {response.text}")
            return {
                'valid': False,
                'error': f'API validation failed (status {response.status_code})'
            }
            
    except requests.exceptions.Timeout:
        logger.error("Timeout while validating OpenRouter API key")
        return {
            'valid': False,
            'error': 'Request timeout - please try again'
        }
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while validating OpenRouter API key")
        return {
            'valid': False,
            'error': 'Connection error - please check your internet connection'
        }
    except Exception as e:
        logger.error(f"Error validating OpenRouter API key: {e}")
        return {
            'valid': False,
            'error': 'An error occurred while validating the API key'
        }


def get_available_models(api_key: str) -> Dict[str, Any]:
    """
    Get available models for the OpenRouter API key.
    
    Args:
        api_key: The OpenRouter API key
    
    Returns:
        dict: Available models or error information
    """
    if not api_key:
        return {
            'success': False,
            'error': 'API key is required'
        }
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{OPENROUTER_API_BASE}/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'models': data.get('data', [])
            }
        else:
            return {
                'success': False,
                'error': f'Failed to fetch models (status {response.status_code})'
            }
            
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return {
            'success': False,
            'error': 'An error occurred while fetching models'
        }
