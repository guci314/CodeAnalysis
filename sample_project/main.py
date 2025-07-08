"""
Main application file that integrates all modules.
"""

import sys
import argparse
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import from local modules
from data_processing import DataProcessor, TimeSeriesProcessor, DataValidator, merge_datasets
from utilities import (
    FileHandler, StringUtils, Cache, timer, retry,
    validate_email, parse_datetime, format_bytes
)
from models import (
    User, Product, Order, Task, Status, Priority,
    InMemoryRepository, ModelFactory, Notification
)
from api_service import (
    APIService, UserAPI, ProductAPI, OrderAPI,
    AuthenticationMiddleware, RateLimiter
)
from config import Config, DatabaseConfig, APIConfig, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Application:
    """Main application class that orchestrates all components."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize application with configuration."""
        self.config = get_config(config_path)
        self.repositories = self._initialize_repositories()
        self.services = self._initialize_services()
        self.cache = Cache[Any](ttl=self.config.cache_ttl)
        self.data_processor = DataProcessor(self.config.data_processing)
        self.file_handler = FileHandler()
        logger.info("Application initialized successfully")
    
    def _initialize_repositories(self) -> Dict[str, InMemoryRepository]:
        """Initialize all repositories."""
        return {
            'users': InMemoryRepository(),
            'products': InMemoryRepository(),
            'orders': InMemoryRepository(),
            'tasks': InMemoryRepository(),
            'notifications': InMemoryRepository()
        }
    
    def _initialize_services(self) -> Dict[str, APIService]:
        """Initialize API services."""
        return {
            'users': UserAPI(self.repositories['users']),
            'products': ProductAPI(self.repositories['products']),
            'orders': OrderAPI(self.repositories['orders'])
        }
    
    @timer
    def create_user(self, username: str, email: str, full_name: str,
                   roles: Optional[List[str]] = None) -> User:
        """Create a new user in the system."""
        # Validate input
        if not validate_email(email):
            raise ValueError(f"Invalid email address: {email}")
        
        # Check if user already exists
        existing_users = self.repositories['users'].find_by_criteria({'email': email})
        if existing_users:
            raise ValueError(f"User with email {email} already exists")
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            roles=roles or ['user']
        )
        
        # Save to repository
        self.repositories['users'].save(user)
        
        # Create welcome notification
        self._create_notification(
            user.id,
            "Welcome to the Application",
            f"Welcome {user.display_name}! Your account has been created successfully.",
            "success"
        )
        
        logger.info(f"User created: {user.username} ({user.id})")
        return user
    
    def create_product(self, name: str, description: str, price: float,
                      category: str, inventory: int = 0) -> Product:
        """Create a new product."""
        product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            inventory_count=inventory
        )
        
        self.repositories['products'].save(product)
        logger.info(f"Product created: {product.name} ({product.sku})")
        return product
    
    def create_order(self, user_id: str, items: List[Dict[str, Any]]) -> Order:
        """Create a new order for a user."""
        # Validate user exists
        user = self.repositories['users'].find_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Create order
        order = Order(user_id=user_id)
        
        # Add items and validate inventory
        for item in items:
            product = self.repositories['products'].find_by_id(item['product_id'])
            if not product:
                raise ValueError(f"Product not found: {item['product_id']}")
            
            if product.inventory_count < item['quantity']:
                raise ValueError(f"Insufficient inventory for {product.name}")
            
            order.add_item(product.id, item['quantity'], product.price)
            
            # Update inventory
            product.update_inventory(-item['quantity'])
            self.repositories['products'].save(product)
        
        # Save order
        self.repositories['orders'].save(order)
        
        # Create notification
        self._create_notification(
            user_id,
            "Order Created",
            f"Your order {order.id} has been created successfully. Total: {order.formatted_price}",
            "info"
        )
        
        logger.info(f"Order created: {order.id} for user {user_id}")
        return order
    
    def create_task(self, title: str, description: str, assignee_id: Optional[str] = None,
                   priority: Priority = Priority.MEDIUM, due_date: Optional[datetime] = None) -> Task:
        """Create a new task."""
        task = Task(title=title, description=description, priority=priority)
        
        if assignee_id:
            # Validate assignee exists
            assignee = self.repositories['users'].find_by_id(assignee_id)
            if not assignee:
                raise ValueError(f"Assignee not found: {assignee_id}")
            task.assign_to(assignee_id)
        
        if due_date:
            task.set_due_date(due_date)
        
        self.repositories['tasks'].save(task)
        
        # Notify assignee
        if assignee_id:
            self._create_notification(
                assignee_id,
                "New Task Assigned",
                f"You have been assigned a new task: {task.title}",
                "info"
            )
        
        logger.info(f"Task created: {task.title} ({task.id})")
        return task
    
    def _create_notification(self, recipient_id: str, title: str, 
                           message: str, type: str = "info") -> Notification:
        """Create a notification for a user."""
        notification = Notification(
            recipient_id=recipient_id,
            title=title,
            message=message,
            type=type,
            expires_at=datetime.now() + timedelta(days=30)
        )
        
        self.repositories['notifications'].save(notification)
        return notification
    
    @timer
    def process_data_file(self, file_path: str) -> Dict[str, Any]:
        """Process a data file and return analysis results."""
        logger.info(f"Processing data file: {file_path}")
        
        # Check cache first
        cache_key = f"processed_{file_path}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached result")
            return cached_result
        
        # Process file
        try:
            df = self.data_processor.process_csv(file_path)
            
            # Validate data
            validator = DataValidator()
            quality_report = validator.check_data_quality(df)
            
            # Calculate statistics
            stats = {}
            for col in df.select_dtypes(include=['float64', 'int64']).columns:
                stats[col] = self.data_processor.calculate_statistics(tuple(df[col].values))
            
            result = {
                'file': file_path,
                'rows': len(df),
                'columns': len(df.columns),
                'quality_report': quality_report,
                'statistics': stats,
                'processed_at': datetime.now().isoformat()
            }
            
            # Cache result
            self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise
    
    def generate_reports(self) -> Dict[str, Any]:
        """Generate various reports from the system data."""
        reports = {}
        
        # User report
        users = self.repositories['users'].find_all()
        reports['user_summary'] = {
            'total_users': len(users),
            'active_users': sum(1 for u in users if u.is_active),
            'admin_users': sum(1 for u in users if u.is_admin),
            'users_by_role': self._count_by_attribute(users, 'roles')
        }
        
        # Product report
        products = self.repositories['products'].find_all()
        reports['product_summary'] = {
            'total_products': len(products),
            'available_products': sum(1 for p in products if p.is_available),
            'out_of_stock': sum(1 for p in products if p.inventory_count == 0),
            'products_by_category': self._count_by_attribute(products, 'category'),
            'total_inventory_value': sum(p.price * p.inventory_count for p in products)
        }
        
        # Order report
        orders = self.repositories['orders'].find_all()
        reports['order_summary'] = {
            'total_orders': len(orders),
            'orders_by_status': self._count_by_attribute(orders, 'status'),
            'total_revenue': sum(o.total_amount for o in orders if o.status == Status.COMPLETED),
            'average_order_value': sum(o.total_amount for o in orders) / len(orders) if orders else 0
        }
        
        # Task report
        tasks = self.repositories['tasks'].find_all()
        reports['task_summary'] = {
            'total_tasks': len(tasks),
            'tasks_by_status': self._count_by_attribute(tasks, 'status'),
            'tasks_by_priority': self._count_by_attribute(tasks, 'priority'),
            'overdue_tasks': sum(1 for t in tasks if t.is_overdue)
        }
        
        reports['generated_at'] = datetime.now().isoformat()
        return reports
    
    def _count_by_attribute(self, items: List[Any], attribute: str) -> Dict[str, int]:
        """Count items by a specific attribute."""
        counts = {}
        for item in items:
            value = getattr(item, attribute, None)
            if isinstance(value, list):
                for v in value:
                    counts[str(v)] = counts.get(str(v), 0) + 1
            else:
                key = str(value.value if hasattr(value, 'value') else value)
                counts[key] = counts.get(key, 0) + 1
        return counts
    
    def export_data(self, export_type: str, output_path: str) -> None:
        """Export system data to file."""
        logger.info(f"Exporting {export_type} data to {output_path}")
        
        data = {}
        
        if export_type == 'all' or export_type == 'users':
            data['users'] = [u.to_dict() for u in self.repositories['users'].find_all()]
        
        if export_type == 'all' or export_type == 'products':
            data['products'] = [p.to_dict() for p in self.repositories['products'].find_all()]
        
        if export_type == 'all' or export_type == 'orders':
            data['orders'] = [o.to_dict() for o in self.repositories['orders'].find_all()]
        
        if export_type == 'all' or export_type == 'tasks':
            data['tasks'] = [t.to_dict() for t in self.repositories['tasks'].find_all()]
        
        # Save to file
        self.file_handler.write_json(data, output_path)
        logger.info(f"Data exported successfully to {output_path}")
    
    def run_maintenance(self) -> Dict[str, Any]:
        """Run maintenance tasks."""
        logger.info("Running maintenance tasks")
        
        results = {
            'expired_notifications': 0,
            'completed_orders': 0,
            'cache_cleared': False
        }
        
        # Clean up expired notifications
        notifications = self.repositories['notifications'].find_all()
        for notification in notifications:
            if notification.is_expired:
                self.repositories['notifications'].delete(notification.id)
                results['expired_notifications'] += 1
        
        # Clear cache if needed
        if self.cache.size() > 1000:
            self.cache.clear()
            results['cache_cleared'] = True
        
        logger.info(f"Maintenance completed: {results}")
        return results


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Sample Application')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--action', choices=['demo', 'export', 'report', 'maintenance'],
                       default='demo', help='Action to perform')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Initialize application
        app = Application(args.config)
        
        if args.action == 'demo':
            # Run demo
            logger.info("Running demo...")
            
            # Create sample users
            user1 = app.create_user("john_doe", "john@example.com", "John Doe", ["user", "customer"])
            user2 = app.create_user("jane_admin", "jane@example.com", "Jane Smith", ["user", "admin"])
            
            # Create sample products
            product1 = app.create_product("Laptop", "High-performance laptop", 999.99, "Electronics", 50)
            product2 = app.create_product("Mouse", "Wireless mouse", 29.99, "Electronics", 200)
            product3 = app.create_product("Notebook", "A5 notebook", 5.99, "Stationery", 500)
            
            # Create sample order
            order = app.create_order(user1.id, [
                {'product_id': product1.id, 'quantity': 1},
                {'product_id': product2.id, 'quantity': 2}
            ])
            
            # Create sample tasks
            task1 = app.create_task(
                "Review new features",
                "Review and test new features for the next release",
                assignee_id=user2.id,
                priority=Priority.HIGH,
                due_date=datetime.now() + timedelta(days=7)
            )
            
            task2 = app.create_task(
                "Update documentation",
                "Update API documentation with new endpoints",
                assignee_id=user1.id,
                priority=Priority.MEDIUM,
                due_date=datetime.now() + timedelta(days=14)
            )
            
            logger.info("Demo completed successfully")
            
        elif args.action == 'export':
            output_path = args.output or 'export.json'
            app.export_data('all', output_path)
            
        elif args.action == 'report':
            reports = app.generate_reports()
            print(json.dumps(reports, indent=2))
            
        elif args.action == 'maintenance':
            results = app.run_maintenance()
            print(f"Maintenance results: {results}")
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()