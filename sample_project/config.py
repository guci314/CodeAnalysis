"""
Configuration module with configuration classes and settings.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class BaseConfig:
    """Base configuration class."""
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, BaseConfig):
                result[key] = value.to_dict()
            elif isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseConfig':
        """Create configuration from dictionary."""
        return cls(**data)


@dataclass
class DatabaseConfig(BaseConfig):
    """Database configuration."""
    
    host: str = "localhost"
    port: int = 5432
    database: str = "app_db"
    username: str = "app_user"
    password: str = ""
    pool_size: int = 10
    pool_timeout: int = 30
    echo: bool = False
    ssl_mode: str = "prefer"
    
    @property
    def connection_string(self) -> str:
        """Get database connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
    
    def validate(self) -> List[str]:
        """Validate database configuration."""
        errors = []
        
        if not self.host:
            errors.append("Database host is required")
        
        if self.port <= 0 or self.port > 65535:
            errors.append("Database port must be between 1 and 65535")
        
        if not self.database:
            errors.append("Database name is required")
        
        if not self.username:
            errors.append("Database username is required")
        
        if self.pool_size < 1:
            errors.append("Pool size must be at least 1")
        
        return errors


@dataclass
class CacheConfig(BaseConfig):
    """Cache configuration."""
    
    backend: str = "memory"  # memory, redis, memcached
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    key_prefix: str = "app_cache"
    default_ttl: int = 3600  # 1 hour
    max_entries: int = 10000
    
    @property
    def connection_string(self) -> str:
        """Get cache connection string."""
        if self.backend == "redis":
            auth = f":{self.password}@" if self.password else ""
            return f"redis://{auth}{self.host}:{self.port}/{self.db}"
        elif self.backend == "memcached":
            return f"{self.host}:{self.port}"
        return "memory://"
    
    def validate(self) -> List[str]:
        """Validate cache configuration."""
        errors = []
        
        valid_backends = ["memory", "redis", "memcached"]
        if self.backend not in valid_backends:
            errors.append(f"Invalid cache backend. Must be one of: {', '.join(valid_backends)}")
        
        if self.backend != "memory" and not self.host:
            errors.append("Cache host is required for non-memory backends")
        
        if self.default_ttl < 0:
            errors.append("Default TTL cannot be negative")
        
        return errors


@dataclass
class SecurityConfig(BaseConfig):
    """Security configuration."""
    
    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    bcrypt_rounds: int = 12
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    csrf_enabled: bool = True
    secure_cookies: bool = True
    
    def validate(self) -> List[str]:
        """Validate security configuration."""
        errors = []
        
        if not self.secret_key:
            errors.append("Secret key is required")
        elif len(self.secret_key) < 32:
            errors.append("Secret key should be at least 32 characters long")
        
        if self.jwt_expiration_hours < 1:
            errors.append("JWT expiration must be at least 1 hour")
        
        if self.password_min_length < 6:
            errors.append("Password minimum length should be at least 6")
        
        if self.bcrypt_rounds < 4 or self.bcrypt_rounds > 31:
            errors.append("BCrypt rounds must be between 4 and 31")
        
        return errors


@dataclass
class APIConfig(BaseConfig):
    """API configuration."""
    
    base_url: str = "/api"
    version: str = "v1"
    title: str = "Sample API"
    description: str = "Sample API for code analysis"
    enable_docs: bool = True
    docs_url: str = "/docs"
    enable_cors: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 30
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    pagination_default: int = 20
    pagination_max: int = 100
    
    @property
    def full_base_url(self) -> str:
        """Get full base URL with version."""
        return f"{self.base_url}/{self.version}"
    
    def validate(self) -> List[str]:
        """Validate API configuration."""
        errors = []
        
        if not self.base_url.startswith("/"):
            errors.append("Base URL must start with /")
        
        if self.max_request_size < 1024:
            errors.append("Max request size must be at least 1KB")
        
        if self.request_timeout < 1:
            errors.append("Request timeout must be at least 1 second")
        
        if self.rate_limit_requests < 1:
            errors.append("Rate limit requests must be at least 1")
        
        if self.pagination_default < 1:
            errors.append("Default pagination size must be at least 1")
        
        if self.pagination_max < self.pagination_default:
            errors.append("Max pagination size must be >= default pagination size")
        
        return errors


@dataclass
class LoggingConfig(BaseConfig):
    """Logging configuration."""
    
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file_enabled: bool = True
    file_path: Path = Path("logs/app.log")
    file_max_bytes: int = 10 * 1024 * 1024  # 10MB
    file_backup_count: int = 5
    console_enabled: bool = True
    json_format: bool = False
    log_sql: bool = False
    
    def validate(self) -> List[str]:
        """Validate logging configuration."""
        errors = []
        
        if self.file_enabled:
            if not self.file_path.parent.exists():
                try:
                    self.file_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create log directory: {str(e)}")
            
            if self.file_max_bytes < 1024:
                errors.append("File max bytes must be at least 1KB")
            
            if self.file_backup_count < 0:
                errors.append("File backup count cannot be negative")
        
        return errors


@dataclass
class EmailConfig(BaseConfig):
    """Email configuration."""
    
    enabled: bool = True
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    from_address: str = "noreply@example.com"
    from_name: str = "Sample App"
    reply_to: Optional[str] = None
    max_recipients: int = 50
    
    def validate(self) -> List[str]:
        """Validate email configuration."""
        errors = []
        
        if self.enabled:
            if not self.smtp_host:
                errors.append("SMTP host is required when email is enabled")
            
            if self.smtp_port <= 0 or self.smtp_port > 65535:
                errors.append("SMTP port must be between 1 and 65535")
            
            if self.smtp_use_tls and self.smtp_use_ssl:
                errors.append("Cannot use both TLS and SSL")
            
            if not self.from_address:
                errors.append("From address is required")
            
            if self.max_recipients < 1:
                errors.append("Max recipients must be at least 1")
        
        return errors


@dataclass
class StorageConfig(BaseConfig):
    """Storage configuration."""
    
    backend: str = "local"  # local, s3, gcs, azure
    local_path: Path = Path("storage")
    s3_bucket: Optional[str] = None
    s3_region: str = "us-east-1"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_endpoint: Optional[str] = None
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx"
    ])
    
    def validate(self) -> List[str]:
        """Validate storage configuration."""
        errors = []
        
        valid_backends = ["local", "s3", "gcs", "azure"]
        if self.backend not in valid_backends:
            errors.append(f"Invalid storage backend. Must be one of: {', '.join(valid_backends)}")
        
        if self.backend == "local":
            if not self.local_path.exists():
                try:
                    self.local_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create storage directory: {str(e)}")
        
        elif self.backend == "s3":
            if not self.s3_bucket:
                errors.append("S3 bucket is required for S3 backend")
            if not self.s3_access_key or not self.s3_secret_key:
                errors.append("S3 credentials are required")
        
        if self.max_file_size < 1024:
            errors.append("Max file size must be at least 1KB")
        
        return errors


@dataclass
class Config(BaseConfig):
    """Main application configuration."""
    
    # Basic settings
    app_name: str = "Sample Application"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    testing: bool = False
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    
    # Additional settings
    timezone: str = "UTC"
    locale: str = "en_US"
    cache_ttl: int = 3600
    session_lifetime: int = 86400  # 24 hours
    maintenance_mode: bool = False
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    
    # Data processing settings
    data_processing: Dict[str, Any] = field(default_factory=lambda: {
        "batch_size": 1000,
        "parallel_workers": 4,
        "memory_limit": 1024 * 1024 * 1024,  # 1GB
        "temp_directory": "/tmp/data_processing"
    })
    
    def validate(self) -> List[str]:
        """Validate entire configuration."""
        errors = []
        
        # Validate sub-configurations
        errors.extend(self.database.validate())
        errors.extend(self.cache.validate())
        errors.extend(self.security.validate())
        errors.extend(self.api.validate())
        errors.extend(self.logging.validate())
        errors.extend(self.email.validate())
        errors.extend(self.storage.validate())
        
        # Validate main config
        if self.cache_ttl < 0:
            errors.append("Cache TTL cannot be negative")
        
        if self.session_lifetime < 60:
            errors.append("Session lifetime must be at least 60 seconds")
        
        # Environment-specific validations
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                errors.append("Debug mode should be disabled in production")
            if not self.security.secure_cookies:
                errors.append("Secure cookies should be enabled in production")
            if "*" in self.security.allowed_origins:
                errors.append("Wildcard origins should not be allowed in production")
        
        return errors
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'Config':
        """Load configuration from file."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        if path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {path.suffix}")
        
        return cls._from_nested_dict(data)
    
    @classmethod
    def _from_nested_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from nested dictionary."""
        # Convert environment string to enum
        if 'environment' in data:
            data['environment'] = Environment(data['environment'])
        
        # Convert sub-configurations
        if 'database' in data:
            data['database'] = DatabaseConfig(**data['database'])
        
        if 'cache' in data:
            data['cache'] = CacheConfig(**data['cache'])
        
        if 'security' in data:
            data['security'] = SecurityConfig(**data['security'])
        
        if 'api' in data:
            data['api'] = APIConfig(**data['api'])
        
        if 'logging' in data:
            if 'level' in data['logging']:
                data['logging']['level'] = LogLevel(data['logging']['level'])
            if 'file_path' in data['logging']:
                data['logging']['file_path'] = Path(data['logging']['file_path'])
            data['logging'] = LoggingConfig(**data['logging'])
        
        if 'email' in data:
            data['email'] = EmailConfig(**data['email'])
        
        if 'storage' in data:
            if 'local_path' in data['storage']:
                data['storage']['local_path'] = Path(data['storage']['local_path'])
            data['storage'] = StorageConfig(**data['storage'])
        
        return cls(**data)
    
    def to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to file."""
        path = Path(file_path)
        data = self.to_dict()
        
        if path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported configuration file format: {path.suffix}")
        
        logger.info(f"Configuration saved to {path}")


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get configuration from file or environment.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Configuration object
    """
    # Check for config file
    if config_path:
        return Config.from_file(config_path)
    
    # Check environment variable
    env_config_path = os.environ.get('APP_CONFIG')
    if env_config_path:
        return Config.from_file(env_config_path)
    
    # Load based on environment
    env = os.environ.get('APP_ENV', 'development').lower()
    
    # Try to find environment-specific config
    config_dir = Path('config')
    if config_dir.exists():
        for ext in ['.json', '.yaml', '.yml']:
            config_file = config_dir / f"{env}{ext}"
            if config_file.exists():
                return Config.from_file(config_file)
    
    # Return default config with environment set
    config = Config()
    config.environment = Environment(env)
    
    # Apply environment-specific defaults
    if config.environment == Environment.PRODUCTION:
        config.debug = False
        config.logging.level = LogLevel.WARNING
        config.security.secure_cookies = True
        config.api.enable_docs = False
    
    return config


# Example configuration files that could be created:
EXAMPLE_DEVELOPMENT_CONFIG = {
    "app_name": "Sample Application",
    "environment": "development",
    "debug": True,
    "database": {
        "host": "localhost",
        "port": 5432,
        "database": "app_dev",
        "username": "dev_user",
        "password": "dev_password"
    },
    "cache": {
        "backend": "memory",
        "default_ttl": 300
    },
    "security": {
        "secret_key": "dev-secret-key-change-in-production",
        "jwt_expiration_hours": 24
    },
    "api": {
        "enable_docs": True,
        "rate_limit_enabled": False
    },
    "logging": {
        "level": "DEBUG",
        "console_enabled": True,
        "file_enabled": True
    }
}

EXAMPLE_PRODUCTION_CONFIG = {
    "app_name": "Sample Application",
    "environment": "production",
    "debug": False,
    "database": {
        "host": "db.production.example.com",
        "port": 5432,
        "database": "app_prod",
        "username": "prod_user",
        "password": "${DB_PASSWORD}",
        "pool_size": 20,
        "ssl_mode": "require"
    },
    "cache": {
        "backend": "redis",
        "host": "redis.production.example.com",
        "password": "${REDIS_PASSWORD}",
        "default_ttl": 3600
    },
    "security": {
        "secret_key": "${SECRET_KEY}",
        "jwt_expiration_hours": 12,
        "allowed_origins": ["https://app.example.com"],
        "secure_cookies": True
    },
    "api": {
        "enable_docs": False,
        "rate_limit_enabled": True,
        "rate_limit_requests": 1000,
        "rate_limit_window": 3600
    },
    "logging": {
        "level": "WARNING",
        "console_enabled": False,
        "file_enabled": True,
        "json_format": True
    },
    "email": {
        "enabled": True,
        "smtp_host": "smtp.sendgrid.net",
        "smtp_port": 587,
        "smtp_username": "apikey",
        "smtp_password": "${SENDGRID_API_KEY}"
    }
}