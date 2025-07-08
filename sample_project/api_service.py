"""
API service module with class-based views and middleware.
"""

from typing import Dict, List, Optional, Any, Callable, Type
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from functools import wraps
import json
import hashlib
import hmac
import logging
from dataclasses import dataclass
from enum import Enum
import re

from models import (
    BaseModel, User, Product, Order, Task, Status, Priority,
    AbstractRepository, InMemoryRepository
)
from utilities import (
    validate_email, validate_url, timer, Cache,
    StringUtils, generate_id
)

logger = logging.getLogger(__name__)


class HTTPMethod(Enum):
    """HTTP methods enumeration."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class HTTPStatus:
    """HTTP status codes."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500


@dataclass
class Request:
    """HTTP request representation."""
    method: HTTPMethod
    path: str
    headers: Dict[str, str]
    params: Dict[str, str]
    body: Optional[Dict[str, Any]] = None
    user: Optional[User] = None
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get header value (case-insensitive)."""
        return self.headers.get(name.lower(), default)
    
    def get_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get query parameter value."""
        return self.params.get(name, default)


@dataclass
class Response:
    """HTTP response representation."""
    status: int
    body: Optional[Any] = None
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        
        # Set content type if not specified
        if 'content-type' not in self.headers:
            self.headers['content-type'] = 'application/json'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'status': self.status,
            'headers': self.headers,
            'body': self.body
        }


class Middleware(ABC):
    """Abstract base class for middleware."""
    
    @abstractmethod
    def process_request(self, request: Request) -> Optional[Response]:
        """
        Process incoming request.
        Return Response to short-circuit, or None to continue.
        """
        pass
    
    @abstractmethod
    def process_response(self, request: Request, response: Response) -> Response:
        """Process outgoing response."""
        pass


class AuthenticationMiddleware(Middleware):
    """Middleware for handling authentication."""
    
    def __init__(self, secret_key: str, user_repository: AbstractRepository):
        """Initialize with secret key and user repository."""
        self.secret_key = secret_key
        self.user_repository = user_repository
        self.token_cache = Cache[str](ttl=3600)  # 1 hour TTL
    
    def process_request(self, request: Request) -> Optional[Response]:
        """Authenticate incoming request."""
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.path):
            return None
        
        # Get authorization header
        auth_header = request.get_header('authorization')
        if not auth_header:
            return Response(
                status=HTTPStatus.UNAUTHORIZED,
                body={'error': 'Authorization header required'}
            )
        
        # Validate token
        if not auth_header.startswith('Bearer '):
            return Response(
                status=HTTPStatus.UNAUTHORIZED,
                body={'error': 'Invalid authorization format'}
            )
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        user_id = self._validate_token(token)
        
        if not user_id:
            return Response(
                status=HTTPStatus.UNAUTHORIZED,
                body={'error': 'Invalid or expired token'}
            )
        
        # Get user from repository
        user = self.user_repository.find_by_id(user_id)
        if not user or not user.is_active:
            return Response(
                status=HTTPStatus.UNAUTHORIZED,
                body={'error': 'User not found or inactive'}
            )
        
        # Attach user to request
        request.user = user
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        """Add security headers to response."""
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block'
        })
        return response
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public."""
        public_patterns = [
            r'^/api/auth/login$',
            r'^/api/auth/register$',
            r'^/api/health$',
            r'^/api/docs'
        ]
        
        for pattern in public_patterns:
            if re.match(pattern, path):
                return True
        return False
    
    def _validate_token(self, token: str) -> Optional[str]:
        """Validate JWT token and return user ID."""
        # Check cache first
        cached_user_id = self.token_cache.get(token)
        if cached_user_id:
            return cached_user_id
        
        try:
            # Simple token validation (in production, use proper JWT)
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (base64)
            import base64
            payload = json.loads(base64.b64decode(parts[1] + '=='))
            
            # Check expiration
            if 'exp' in payload and payload['exp'] < datetime.now().timestamp():
                return None
            
            # Verify signature
            expected_signature = self._generate_signature(parts[0], parts[1])
            if parts[2] != expected_signature:
                return None
            
            user_id = payload.get('user_id')
            if user_id:
                self.token_cache.set(token, user_id)
            
            return user_id
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None
    
    def _generate_signature(self, header: str, payload: str) -> str:
        """Generate token signature."""
        message = f"{header}.{payload}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def generate_token(self, user: User) -> str:
        """Generate JWT token for user."""
        import base64
        
        # Create header
        header = base64.b64encode(json.dumps({
            'alg': 'HS256',
            'typ': 'JWT'
        }).encode()).decode().rstrip('=')
        
        # Create payload
        payload = base64.b64encode(json.dumps({
            'user_id': user.id,
            'username': user.username,
            'exp': (datetime.now() + timedelta(hours=24)).timestamp()
        }).encode()).decode().rstrip('=')
        
        # Create signature
        signature = self._generate_signature(header, payload)
        
        return f"{header}.{payload}.{signature}"


class RateLimiter(Middleware):
    """Middleware for rate limiting."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts: Dict[str, List[datetime]] = {}
    
    def process_request(self, request: Request) -> Optional[Response]:
        """Check rate limit for request."""
        # Get client identifier (IP or user ID)
        client_id = self._get_client_id(request)
        
        # Clean old requests
        self._clean_old_requests(client_id)
        
        # Check rate limit
        if client_id not in self.request_counts:
            self.request_counts[client_id] = []
        
        request_times = self.request_counts[client_id]
        
        if len(request_times) >= self.max_requests:
            return Response(
                status=429,  # Too Many Requests
                body={'error': 'Rate limit exceeded'},
                headers={
                    'X-RateLimit-Limit': str(self.max_requests),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int((request_times[0] + timedelta(seconds=self.window_seconds)).timestamp()))
                }
            )
        
        # Record request
        request_times.append(datetime.now())
        
        return None
    
    def process_response(self, request: Request, response: Response) -> Response:
        """Add rate limit headers to response."""
        client_id = self._get_client_id(request)
        request_times = self.request_counts.get(client_id, [])
        
        remaining = max(0, self.max_requests - len(request_times))
        
        response.headers.update({
            'X-RateLimit-Limit': str(self.max_requests),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Window': str(self.window_seconds)
        })
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        if request.user:
            return f"user_{request.user.id}"
        
        # In real implementation, get IP address
        return request.get_header('x-forwarded-for', 'unknown')
    
    def _clean_old_requests(self, client_id: str) -> None:
        """Remove requests older than the time window."""
        if client_id not in self.request_counts:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=self.window_seconds)
        self.request_counts[client_id] = [
            t for t in self.request_counts[client_id]
            if t > cutoff_time
        ]


class APIService(ABC):
    """Abstract base class for API services."""
    
    def __init__(self, repository: AbstractRepository):
        """Initialize with repository."""
        self.repository = repository
        self.validators: Dict[str, Callable] = {}
        self.serializers: Dict[str, Callable] = {}
    
    @abstractmethod
    def get_routes(self) -> Dict[str, Dict[HTTPMethod, Callable]]:
        """Get route mapping for this service."""
        pass
    
    def handle_request(self, request: Request) -> Response:
        """Handle incoming request."""
        # Get routes
        routes = self.get_routes()
        
        # Find matching route
        for pattern, methods in routes.items():
            if self._match_route(pattern, request.path):
                if request.method not in methods:
                    return Response(
                        status=HTTPStatus.METHOD_NOT_ALLOWED,
                        body={'error': f'Method {request.method.value} not allowed'}
                    )
                
                # Call handler
                handler = methods[request.method]
                return handler(request)
        
        return Response(
            status=HTTPStatus.NOT_FOUND,
            body={'error': 'Endpoint not found'}
        )
    
    def _match_route(self, pattern: str, path: str) -> bool:
        """Match route pattern against path."""
        # Convert route pattern to regex
        # e.g., /users/{id} -> /users/([^/]+)
        regex_pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', pattern)
        regex_pattern = f'^{regex_pattern}$'
        
        return bool(re.match(regex_pattern, path))
    
    def paginate(self, items: List[Any], page: int = 1, 
                per_page: int = 20) -> Dict[str, Any]:
        """Paginate list of items."""
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            'items': items[start:end],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }


class UserAPI(APIService):
    """API service for user management."""
    
    def get_routes(self) -> Dict[str, Dict[HTTPMethod, Callable]]:
        """Get user API routes."""
        return {
            '/api/users': {
                HTTPMethod.GET: self.list_users,
                HTTPMethod.POST: self.create_user
            },
            '/api/users/{id}': {
                HTTPMethod.GET: self.get_user,
                HTTPMethod.PUT: self.update_user,
                HTTPMethod.DELETE: self.delete_user
            },
            '/api/users/{id}/roles': {
                HTTPMethod.POST: self.add_role,
                HTTPMethod.DELETE: self.remove_role
            }
        }
    
    @timer
    def list_users(self, request: Request) -> Response:
        """List all users with pagination."""
        try:
            # Get pagination params
            page = int(request.get_param('page', '1'))
            per_page = int(request.get_param('per_page', '20'))
            
            # Get filter params
            is_active = request.get_param('is_active')
            role = request.get_param('role')
            
            # Get all users
            users = self.repository.find_all()
            
            # Apply filters
            if is_active is not None:
                users = [u for u in users if u.is_active == (is_active.lower() == 'true')]
            
            if role:
                users = [u for u in users if u.has_role(role)]
            
            # Paginate
            result = self.paginate(users, page, per_page)
            
            # Serialize users
            result['items'] = [self._serialize_user(u) for u in result['items']]
            
            return Response(status=HTTPStatus.OK, body=result)
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return Response(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                body={'error': 'Failed to list users'}
            )
    
    def get_user(self, request: Request) -> Response:
        """Get single user by ID."""
        # Extract ID from path
        match = re.match(r'/api/users/([^/]+)', request.path)
        if not match:
            return Response(
                status=HTTPStatus.BAD_REQUEST,
                body={'error': 'Invalid user ID'}
            )
        
        user_id = match.group(1)
        user = self.repository.find_by_id(user_id)
        
        if not user:
            return Response(
                status=HTTPStatus.NOT_FOUND,
                body={'error': 'User not found'}
            )
        
        return Response(
            status=HTTPStatus.OK,
            body=self._serialize_user(user)
        )
    
    def create_user(self, request: Request) -> Response:
        """Create new user."""
        if not request.body:
            return Response(
                status=HTTPStatus.BAD_REQUEST,
                body={'error': 'Request body required'}
            )
        
        # Validate required fields
        required_fields = ['username', 'email', 'full_name']
        for field in required_fields:
            if field not in request.body:
                return Response(
                    status=HTTPStatus.BAD_REQUEST,
                    body={'error': f'Field {field} is required'}
                )
        
        # Validate email
        if not validate_email(request.body['email']):
            return Response(
                status=HTTPStatus.BAD_REQUEST,
                body={'error': 'Invalid email address'}
            )
        
        # Check if user exists
        existing = self.repository.find_by_criteria({'email': request.body['email']})
        if existing:
            return Response(
                status=HTTPStatus.CONFLICT,
                body={'error': 'User with this email already exists'}
            )
        
        # Create user
        try:
            user = User(
                username=request.body['username'],
                email=request.body['email'],
                full_name=request.body['full_name'],
                roles=request.body.get('roles', ['user'])
            )
            
            self.repository.save(user)
            
            return Response(
                status=HTTPStatus.CREATED,
                body=self._serialize_user(user),
                headers={'Location': f'/api/users/{user.id}'}
            )
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return Response(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                body={'error': 'Failed to create user'}
            )
    
    def update_user(self, request: Request) -> Response:
        """Update existing user."""
        # Extract ID from path
        match = re.match(r'/api/users/([^/]+)', request.path)
        if not match:
            return Response(
                status=HTTPStatus.BAD_REQUEST,
                body={'error': 'Invalid user ID'}
            )
        
        user_id = match.group(1)
        user = self.repository.find_by_id(user_id)
        
        if not user:
            return Response(
                status=HTTPStatus.NOT_FOUND,
                body={'error': 'User not found'}
            )
        
        # Check permissions
        if request.user.id != user_id and not request.user.is_admin:
            return Response(
                status=HTTPStatus.FORBIDDEN,
                body={'error': 'Insufficient permissions'}
            )
        
        # Update fields
        if request.body:
            if 'email' in request.body:
                if not validate_email(request.body['email']):
                    return Response(
                        status=HTTPStatus.BAD_REQUEST,
                        body={'error': 'Invalid email address'}
                    )
                user.email = request.body['email']
            
            if 'full_name' in request.body:
                user.full_name = request.body['full_name']
            
            if 'is_active' in request.body and request.user.is_admin:
                user.is_active = request.body['is_active']
            
            self.repository.save(user)
        
        return Response(
            status=HTTPStatus.OK,
            body=self._serialize_user(user)
        )
    
    def delete_user(self, request: Request) -> Response:
        """Delete user."""
        # Extract ID from path
        match = re.match(r'/api/users/([^/]+)', request.path)
        if not match:
            return Response(
                status=HTTPStatus.BAD_REQUEST,
                body={'error': 'Invalid user ID'}
            )
        
        user_id = match.group(1)
        
        # Check permissions
        if not request.user.is_admin:
            return Response(
                status=HTTPStatus.FORBIDDEN,
                body={'error': 'Admin privileges required'}
            )
        
        if self.repository.delete(user_id):
            return Response(status=HTTPStatus.NO_CONTENT)
        else:
            return Response(
                status=HTTPStatus.NOT_FOUND,
                body={'error': 'User not found'}
            )
    
    def add_role(self, request: Request) -> Response:
        """Add role to user."""
        # Implementation here
        pass
    
    def remove_role(self, request: Request) -> Response:
        """Remove role from user."""
        # Implementation here
        pass
    
    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """Serialize user for API response."""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'roles': user.roles,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }


class ProductAPI(APIService):
    """API service for product management."""
    
    def get_routes(self) -> Dict[str, Dict[HTTPMethod, Callable]]:
        """Get product API routes."""
        return {
            '/api/products': {
                HTTPMethod.GET: self.list_products,
                HTTPMethod.POST: self.create_product
            },
            '/api/products/{id}': {
                HTTPMethod.GET: self.get_product,
                HTTPMethod.PUT: self.update_product,
                HTTPMethod.DELETE: self.delete_product
            },
            '/api/products/{id}/inventory': {
                HTTPMethod.POST: self.update_inventory
            }
        }
    
    def list_products(self, request: Request) -> Response:
        """List products with filtering."""
        try:
            # Get filter params
            category = request.get_param('category')
            min_price = request.get_param('min_price')
            max_price = request.get_param('max_price')
            available_only = request.get_param('available_only', 'false').lower() == 'true'
            
            # Get all products
            products = self.repository.find_all()
            
            # Apply filters
            if category:
                products = [p for p in products if p.category == category]
            
            if min_price:
                products = [p for p in products if p.price >= float(min_price)]
            
            if max_price:
                products = [p for p in products if p.price <= float(max_price)]
            
            if available_only:
                products = [p for p in products if p.is_available]
            
            # Sort by price
            sort_by = request.get_param('sort_by', 'name')
            reverse = request.get_param('order', 'asc') == 'desc'
            
            if sort_by == 'price':
                products.sort(key=lambda p: p.price, reverse=reverse)
            elif sort_by == 'name':
                products.sort(key=lambda p: p.name, reverse=reverse)
            
            # Paginate
            page = int(request.get_param('page', '1'))
            per_page = int(request.get_param('per_page', '20'))
            result = self.paginate(products, page, per_page)
            
            # Serialize
            result['items'] = [self._serialize_product(p) for p in result['items']]
            
            return Response(status=HTTPStatus.OK, body=result)
            
        except Exception as e:
            logger.error(f"Error listing products: {str(e)}")
            return Response(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                body={'error': 'Failed to list products'}
            )
    
    def get_product(self, request: Request) -> Response:
        """Get single product."""
        # Implementation similar to get_user
        pass
    
    def create_product(self, request: Request) -> Response:
        """Create new product."""
        # Check admin permission
        if not request.user.is_admin:
            return Response(
                status=HTTPStatus.FORBIDDEN,
                body={'error': 'Admin privileges required'}
            )
        
        # Implementation here
        pass
    
    def update_product(self, request: Request) -> Response:
        """Update product."""
        # Implementation here
        pass
    
    def delete_product(self, request: Request) -> Response:
        """Delete product."""
        # Implementation here
        pass
    
    def update_inventory(self, request: Request) -> Response:
        """Update product inventory."""
        # Implementation here
        pass
    
    def _serialize_product(self, product: Product) -> Dict[str, Any]:
        """Serialize product for API response."""
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'currency': product.currency,
            'sku': product.sku,
            'category': product.category,
            'tags': product.tags,
            'inventory_count': product.inventory_count,
            'is_available': product.is_available,
            'images': product.images,
            'created_at': product.created_at.isoformat()
        }


class OrderAPI(APIService):
    """API service for order management."""
    
    def get_routes(self) -> Dict[str, Dict[HTTPMethod, Callable]]:
        """Get order API routes."""
        return {
            '/api/orders': {
                HTTPMethod.GET: self.list_orders,
                HTTPMethod.POST: self.create_order
            },
            '/api/orders/{id}': {
                HTTPMethod.GET: self.get_order,
                HTTPMethod.PATCH: self.update_order_status
            }
        }
    
    def list_orders(self, request: Request) -> Response:
        """List orders for user."""
        # Implementation here
        pass
    
    def get_order(self, request: Request) -> Response:
        """Get single order."""
        # Implementation here
        pass
    
    def create_order(self, request: Request) -> Response:
        """Create new order."""
        # Implementation here
        pass
    
    def update_order_status(self, request: Request) -> Response:
        """Update order status."""
        # Implementation here
        pass


class APIRouter:
    """Main API router that delegates to services."""
    
    def __init__(self):
        """Initialize router."""
        self.services: List[APIService] = []
        self.middleware: List[Middleware] = []
    
    def add_service(self, service: APIService) -> None:
        """Register API service."""
        self.services.append(service)
    
    def add_middleware(self, middleware: Middleware) -> None:
        """Add middleware to pipeline."""
        self.middleware.append(middleware)
    
    def handle_request(self, request: Request) -> Response:
        """Handle incoming request through middleware pipeline."""
        # Process request through middleware
        for mw in self.middleware:
            response = mw.process_request(request)
            if response:
                return response
        
        # Find matching service
        response = None
        for service in self.services:
            routes = service.get_routes()
            for pattern in routes.keys():
                if self._match_route(pattern, request.path):
                    response = service.handle_request(request)
                    break
            
            if response:
                break
        
        if not response:
            response = Response(
                status=HTTPStatus.NOT_FOUND,
                body={'error': 'Endpoint not found'}
            )
        
        # Process response through middleware (in reverse order)
        for mw in reversed(self.middleware):
            response = mw.process_response(request, response)
        
        return response
    
    def _match_route(self, pattern: str, path: str) -> bool:
        """Check if path matches route pattern."""
        regex_pattern = re.sub(r'\{(\w+)\}', r'[^/]+', pattern)
        return bool(re.match(f'^{regex_pattern}', path))