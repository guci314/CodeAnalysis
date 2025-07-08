"""
Sample project package for code analysis testing.
"""

__version__ = "1.0.0"
__author__ = "Sample Author"
__email__ = "author@example.com"

# Import main components
from .models import User, Product, Order, Task, Status, Priority
from .data_processing import DataProcessor, TimeSeriesProcessor, DataValidator
from .utilities import FileHandler, StringUtils, Cache, timer, retry
from .api_service import APIService, UserAPI, ProductAPI, OrderAPI
from .config import Config, get_config

__all__ = [
    # Models
    'User', 'Product', 'Order', 'Task', 'Status', 'Priority',
    
    # Data Processing
    'DataProcessor', 'TimeSeriesProcessor', 'DataValidator',
    
    # Utilities
    'FileHandler', 'StringUtils', 'Cache', 'timer', 'retry',
    
    # API Services
    'APIService', 'UserAPI', 'ProductAPI', 'OrderAPI',
    
    # Configuration
    'Config', 'get_config',
]