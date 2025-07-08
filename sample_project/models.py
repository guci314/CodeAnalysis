"""
Data models and classes for the application.
"""

from typing import List, Dict, Optional, Any, Union, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid
from abc import ABC, abstractmethod
import json


class Status(Enum):
    """Status enumeration for various entities."""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BaseModel:
    """Base model with common fields."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Enum):
                result[key] = value.value
            elif hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result
    
    def to_json(self) -> str:
        """Convert model to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class User(BaseModel):
    """User model with authentication details."""
    username: str = ""
    email: str = ""
    full_name: str = ""
    is_active: bool = True
    is_admin: bool = False
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    roles: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.username:
            raise ValueError("Username is required")
        if not self.email:
            raise ValueError("Email is required")
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return role in self.roles
    
    def add_role(self, role: str) -> None:
        """Add role to user."""
        if role not in self.roles:
            self.roles.append(role)
            self.update_timestamp()
    
    def remove_role(self, role: str) -> None:
        """Remove role from user."""
        if role in self.roles:
            self.roles.remove(role)
            self.update_timestamp()
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences."""
        self.preferences.update(preferences)
        self.update_timestamp()
    
    @property
    def display_name(self) -> str:
        """Get display name for user."""
        return self.full_name or self.username


@dataclass
class Product(BaseModel):
    """Product model for e-commerce."""
    name: str = ""
    description: str = ""
    price: float = 0.0
    currency: str = "USD"
    sku: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    inventory_count: int = 0
    is_available: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate product data."""
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        if not self.name:
            raise ValueError("Product name is required")
        if not self.sku:
            self.sku = self._generate_sku()
    
    def _generate_sku(self) -> str:
        """Generate SKU from product details."""
        prefix = self.category[:3].upper() if self.category else "PRD"
        return f"{prefix}-{self.id[:8].upper()}"
    
    def update_inventory(self, quantity: int) -> None:
        """Update inventory count."""
        self.inventory_count += quantity
        self.is_available = self.inventory_count > 0
        self.update_timestamp()
    
    def add_tag(self, tag: str) -> None:
        """Add tag to product."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.update_timestamp()
    
    def set_price(self, price: float, currency: Optional[str] = None) -> None:
        """Set product price."""
        if price < 0:
            raise ValueError("Price cannot be negative")
        self.price = price
        if currency:
            self.currency = currency
        self.update_timestamp()
    
    @property
    def formatted_price(self) -> str:
        """Get formatted price string."""
        return f"{self.currency} {self.price:.2f}"


@dataclass
class Order(BaseModel):
    """Order model for purchases."""
    user_id: str = ""
    items: List[Dict[str, Any]] = field(default_factory=list)
    status: Status = Status.PENDING
    total_amount: float = 0.0
    currency: str = "USD"
    shipping_address: Dict[str, str] = field(default_factory=dict)
    billing_address: Dict[str, str] = field(default_factory=dict)
    payment_method: str = ""
    tracking_number: Optional[str] = None
    notes: str = ""
    
    def add_item(self, product_id: str, quantity: int, price: float) -> None:
        """Add item to order."""
        item = {
            'product_id': product_id,
            'quantity': quantity,
            'price': price,
            'subtotal': quantity * price
        }
        self.items.append(item)
        self._recalculate_total()
        self.update_timestamp()
    
    def remove_item(self, product_id: str) -> None:
        """Remove item from order."""
        self.items = [item for item in self.items if item['product_id'] != product_id]
        self._recalculate_total()
        self.update_timestamp()
    
    def _recalculate_total(self) -> None:
        """Recalculate order total."""
        self.total_amount = sum(item['subtotal'] for item in self.items)
    
    def update_status(self, new_status: Status) -> None:
        """Update order status with validation."""
        valid_transitions = {
            Status.PENDING: [Status.ACTIVE, Status.CANCELLED],
            Status.ACTIVE: [Status.COMPLETED, Status.FAILED, Status.CANCELLED],
            Status.COMPLETED: [],
            Status.FAILED: [Status.PENDING],
            Status.CANCELLED: []
        }
        
        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            self.update_timestamp()
        else:
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
    
    @property
    def item_count(self) -> int:
        """Get total number of items in order."""
        return sum(item['quantity'] for item in self.items)


class Task(BaseModel):
    """Task model for task management."""
    
    def __init__(self, title: str, description: str = "", 
                 priority: Priority = Priority.MEDIUM, **kwargs):
        """Initialize task with required fields."""
        super().__init__(**kwargs)
        self.title = title
        self.description = description
        self.priority = priority
        self.status = Status.PENDING
        self.assignee_id: Optional[str] = None
        self.due_date: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.tags: Set[str] = set()
        self.subtasks: List['Task'] = []
        self.parent_id: Optional[str] = None
        self.dependencies: List[str] = []
        self.attachments: List[Dict[str, str]] = []
        self.comments: List[Dict[str, Any]] = []
    
    def assign_to(self, user_id: str) -> None:
        """Assign task to user."""
        self.assignee_id = user_id
        self.update_timestamp()
    
    def set_due_date(self, due_date: datetime) -> None:
        """Set task due date."""
        if due_date < datetime.now():
            raise ValueError("Due date cannot be in the past")
        self.due_date = due_date
        self.update_timestamp()
    
    def mark_complete(self) -> None:
        """Mark task as completed."""
        if self.status != Status.ACTIVE:
            raise ValueError("Only active tasks can be marked as complete")
        self.status = Status.COMPLETED
        self.completed_at = datetime.now()
        self.update_timestamp()
    
    def add_subtask(self, subtask: 'Task') -> None:
        """Add subtask to this task."""
        subtask.parent_id = self.id
        self.subtasks.append(subtask)
        self.update_timestamp()
    
    def add_dependency(self, task_id: str) -> None:
        """Add dependency to another task."""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.update_timestamp()
    
    def add_comment(self, user_id: str, comment: str) -> None:
        """Add comment to task."""
        self.comments.append({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'comment': comment,
            'created_at': datetime.now().isoformat()
        })
        self.update_timestamp()
    
    def add_attachment(self, filename: str, url: str, size: int) -> None:
        """Add attachment to task."""
        self.attachments.append({
            'id': str(uuid.uuid4()),
            'filename': filename,
            'url': url,
            'size': size,
            'uploaded_at': datetime.now().isoformat()
        })
        self.update_timestamp()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date or self.status == Status.COMPLETED:
            return False
        return datetime.now() > self.due_date
    
    @property
    def progress(self) -> float:
        """Calculate task progress based on subtasks."""
        if not self.subtasks:
            return 100.0 if self.status == Status.COMPLETED else 0.0
        
        completed = sum(1 for task in self.subtasks if task.status == Status.COMPLETED)
        return (completed / len(self.subtasks)) * 100


class AbstractRepository(ABC):
    """Abstract base class for repositories."""
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[BaseModel]:
        """Find entity by ID."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[BaseModel]:
        """Find all entities."""
        pass
    
    @abstractmethod
    def save(self, entity: BaseModel) -> BaseModel:
        """Save entity."""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        pass


class InMemoryRepository(AbstractRepository):
    """In-memory implementation of repository."""
    
    def __init__(self):
        """Initialize repository."""
        self._storage: Dict[str, BaseModel] = {}
    
    def find_by_id(self, id: str) -> Optional[BaseModel]:
        """Find entity by ID."""
        return self._storage.get(id)
    
    def find_all(self) -> List[BaseModel]:
        """Find all entities."""
        return list(self._storage.values())
    
    def save(self, entity: BaseModel) -> BaseModel:
        """Save entity."""
        entity.update_timestamp()
        self._storage[entity.id] = entity
        return entity
    
    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        if id in self._storage:
            del self._storage[id]
            return True
        return False
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[BaseModel]:
        """Find entities matching criteria."""
        results = []
        for entity in self._storage.values():
            match = True
            for key, value in criteria.items():
                if not hasattr(entity, key) or getattr(entity, key) != value:
                    match = False
                    break
            if match:
                results.append(entity)
        return results


@dataclass
class Notification(BaseModel):
    """Notification model for system messages."""
    recipient_id: str = ""
    title: str = ""
    message: str = ""
    type: str = "info"  # info, warning, error, success
    is_read: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    
    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.is_read = True
        self.update_timestamp()
    
    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at


class ModelFactory:
    """Factory for creating model instances."""
    
    _models = {
        'user': User,
        'product': Product,
        'order': Order,
        'task': Task,
        'notification': Notification
    }
    
    @classmethod
    def create(cls, model_type: str, **kwargs) -> BaseModel:
        """Create model instance by type."""
        model_class = cls._models.get(model_type.lower())
        if not model_class:
            raise ValueError(f"Unknown model type: {model_type}")
        return model_class(**kwargs)
    
    @classmethod
    def register_model(cls, name: str, model_class: type) -> None:
        """Register new model type."""
        cls._models[name.lower()] = model_class