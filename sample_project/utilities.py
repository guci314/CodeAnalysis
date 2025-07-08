"""
Utility functions and helpers for the application.
"""

import os
import json
import yaml
import hashlib
import re
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from functools import wraps
import time
import logging
from pathlib import Path
import urllib.parse
import requests
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')


def timer(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each failure
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator


def memoize(maxsize: int = 128):
    """Simple memoization decorator with size limit."""
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_order = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            
            if key in cache:
                return cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = result
            cache_order.append(key)
            
            # Remove oldest entries if cache is full
            if len(cache) > maxsize:
                oldest_key = cache_order.pop(0)
                del cache[oldest_key]
            
            return result
        
        wrapper.cache_clear = lambda: cache.clear() or cache_order.clear()
        return wrapper
    return decorator


class FileHandler:
    """Utility class for file operations."""
    
    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read JSON file and return parsed content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {str(e)}")
            raise
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
    
    @staticmethod
    def write_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
        """Write data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            logger.info(f"Successfully wrote JSON to {file_path}")
        except Exception as e:
            logger.error(f"Failed to write JSON to {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def read_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read YAML file and return parsed content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in file {file_path}: {str(e)}")
            raise
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> Path:
        """Ensure directory exists, create if it doesn't."""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
        """Calculate hash of file contents."""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()


class StringUtils:
    """String manipulation utilities."""
    
    @staticmethod
    def camel_to_snake(name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def snake_to_camel(name: str, capitalize_first: bool = True) -> str:
        """Convert snake_case to CamelCase."""
        components = name.split('_')
        if capitalize_first:
            return ''.join(x.title() for x in components)
        else:
            return components[0] + ''.join(x.title() for x in components[1:])
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = '...') -> str:
        """Truncate text to specified length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove invalid characters from filename."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext
        
        return filename


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def parse_datetime(date_string: str, formats: Optional[List[str]] = None) -> Optional[datetime]:
    """
    Parse datetime string with multiple format attempts.
    
    Args:
        date_string: String to parse
        formats: List of datetime formats to try
        
    Returns:
        Parsed datetime or None if parsing fails
    """
    if formats is None:
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse datetime string: {date_string}")
    return None


def format_bytes(size: int) -> str:
    """Format byte size to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge into dict1
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


class Cache(Generic[T]):
    """Thread-safe cache implementation."""
    
    def __init__(self, ttl: Optional[int] = None):
        """
        Initialize cache.
        
        Args:
            ttl: Time to live in seconds (None for no expiration)
        """
        self._cache: Dict[str, Tuple[T, Optional[datetime]]] = {}
        self._lock = threading.RLock()
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            if expiry and datetime.now() > expiry:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        with self._lock:
            expiry = None
            if ttl or self.ttl:
                expiry = datetime.now() + timedelta(seconds=ttl or self.ttl)
            
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get number of items in cache."""
        with self._lock:
            return len(self._cache)


@retry(max_attempts=3, delay=1.0)
def fetch_url(url: str, timeout: int = 30) -> str:
    """
    Fetch content from URL with retry logic.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Response text
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def generate_id(prefix: str = '', length: int = 8) -> str:
    """Generate unique ID with optional prefix."""
    timestamp = int(time.time() * 1000)
    random_part = hashlib.sha256(os.urandom(32)).hexdigest()[:length]
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_part}"
    return f"{timestamp}_{random_part}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide numbers, returning default on division by zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp value between min and max."""
    return max(min_value, min(value, max_value))