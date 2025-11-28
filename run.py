#!/usr/bin/env python3
"""
Development Runner Script for Practice Portal.

This script performs health checks and runs the Django development server.
It acts as a minimal wrapper around manage.py with pre-flight validation.
"""
import os
import sys
import subprocess
import socket
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    PURPLE = '\033[95m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class DevRunner:
    """Development environment runner with health checks."""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.venv_dir = self.base_dir / 'venv'
        self.errors = []
        self.warnings = []
        self.venv_activated = False
    
    def print_header(self):
        """Print application header."""
        print(f"\n{Colors.PURPLE}{Colors.BOLD}")
        print("╔═══════════════════════════════════════════════════╗")
        print("║          DSAT SCHOOL - Practice Portal           ║")
        print("║              Development Server Runner            ║")
        print("╚═══════════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")
    
    def check_python_version(self):
        """Check if Python version is compatible."""
        print(f"{Colors.CYAN}[1/7] Checking Python version...{Colors.END}")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 11):
            self.errors.append(f"Python 3.11+ required, found {version.major}.{version.minor}")
            print(f"{Colors.RED}✗ Python {version.major}.{version.minor} (requires 3.11+){Colors.END}")
            return False
        print(f"{Colors.GREEN}✓ Python {version.major}.{version.minor}.{version.micro}{Colors.END}")
        return True
    
    def check_virtual_env(self):
        """Check if running in a virtual environment, create if needed."""
        print(f"{Colors.CYAN}[2/7] Checking virtual environment...{Colors.END}")
        
        # Check if already in virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if in_venv:
            print(f"{Colors.GREEN}✓ Virtual environment active{Colors.END}")
            self.venv_activated = True
            return True
        
        # Check if venv exists
        if not self.venv_dir.exists():
            print(f"{Colors.YELLOW}⚠ Virtual environment not found{Colors.END}")
            print(f"{Colors.CYAN}  → Creating virtual environment...{Colors.END}")
            try:
                subprocess.run([sys.executable, '-m', 'venv', str(self.venv_dir)], check=True)
                print(f"{Colors.GREEN}✓ Virtual environment created{Colors.END}")
            except subprocess.CalledProcessError as e:
                self.errors.append(f"Failed to create virtual environment: {str(e)}")
                print(f"{Colors.RED}✗ Failed to create virtual environment{Colors.END}")
                return False
        
        # Activate virtual environment by re-executing script in venv
        print(f"{Colors.YELLOW}  → Activating virtual environment...{Colors.END}")
        venv_python = self.venv_dir / 'bin' / 'python'
        
        if not venv_python.exists():
            self.errors.append("Virtual environment Python not found")
            print(f"{Colors.RED}✗ Virtual environment is corrupted{Colors.END}")
            return False
        
        # Re-execute the script with venv Python
        print(f"{Colors.GREEN}✓ Restarting with virtual environment...{Colors.END}\n")
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        
        return True
    
    def check_env_file(self):
        """Check if .env file exists."""
        print(f"{Colors.CYAN}[3/7] Checking environment file...{Colors.END}")
        env_file = self.base_dir / '.env'
        if not env_file.exists():
            self.errors.append(".env file not found")
            print(f"{Colors.RED}✗ .env file missing{Colors.END}")
            print(f"{Colors.YELLOW}  → Copy .env.example to .env and configure it{Colors.END}")
            return False
        print(f"{Colors.GREEN}✓ .env file exists{Colors.END}")
        return True
    
    def check_dependencies(self):
        """Check if required Python packages are installed, install if missing."""
        print(f"{Colors.CYAN}[4/7] Checking dependencies...{Colors.END}")
        required_packages = {
            'django': 'Django',
            'psycopg2': 'psycopg2-binary',
            'redis': 'redis',
            'celery': 'celery',
            'rest_framework': 'djangorestframework',
            'dotenv': 'python-dotenv',
        }
        missing = []
        
        for package, pip_name in required_packages.items():
            try:
                __import__(package)
            except ImportError:
                missing.append(pip_name)
        
        if missing:
            print(f"{Colors.YELLOW}⚠ Missing packages: {', '.join(missing)}{Colors.END}")
            print(f"{Colors.CYAN}  → Installing dependencies from requirements/dev.txt...{Colors.END}")
            
            requirements_file = self.base_dir / 'requirements' / 'dev.txt'
            if not requirements_file.exists():
                self.errors.append("requirements/dev.txt not found")
                print(f"{Colors.RED}✗ requirements/dev.txt not found{Colors.END}")
                return False
            
            try:
                # Install dependencies with progress output
                print(f"{Colors.CYAN}    Installing packages (this may take a minute)...{Colors.END}")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
                    check=True,
                    capture_output=False,
                    text=True
                )
                print(f"{Colors.GREEN}✓ Dependencies installed successfully{Colors.END}")
                
                # Verify installation
                still_missing = []
                for package in required_packages.keys():
                    try:
                        __import__(package)
                    except ImportError:
                        still_missing.append(package)
                
                if still_missing:
                    self.errors.append(f"Failed to install: {', '.join(still_missing)}")
                    print(f"{Colors.RED}✗ Some packages failed to install{Colors.END}")
                    return False
                
            except subprocess.CalledProcessError as e:
                self.errors.append(f"Failed to install dependencies: {e.stderr.decode() if e.stderr else str(e)}")
                print(f"{Colors.RED}✗ Failed to install dependencies{Colors.END}")
                print(f"{Colors.YELLOW}  → Try manually: pip install -r requirements/dev.txt{Colors.END}")
                return False
        else:
            print(f"{Colors.GREEN}✓ All dependencies installed{Colors.END}")
        
        return True
    
    def check_database(self):
        """Check if PostgreSQL is accessible."""
        print(f"{Colors.CYAN}[5/7] Checking database connection...{Colors.END}")
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv(self.base_dir / '.env')
        except ImportError:
            # If dotenv not available, try to continue without it
            pass
        
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = int(os.getenv('DB_PORT', '5432'))
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((db_host, db_port))
            sock.close()
            
            if result != 0:
                self.errors.append(f"Cannot connect to PostgreSQL at {db_host}:{db_port}")
                print(f"{Colors.RED}✗ PostgreSQL not accessible at {db_host}:{db_port}{Colors.END}")
                print(f"{Colors.YELLOW}  → Start PostgreSQL: sudo systemctl start postgresql{Colors.END}")
                return False
            
            print(f"{Colors.GREEN}✓ PostgreSQL accessible at {db_host}:{db_port}{Colors.END}")
            return True
        except Exception as e:
            self.errors.append(f"Database check failed: {str(e)}")
            print(f"{Colors.RED}✗ Database check failed: {str(e)}{Colors.END}")
            return False
    
    def check_redis(self):
        """Check if Redis is accessible."""
        print(f"{Colors.CYAN}[6/7] Checking Redis connection...{Colors.END}")
        
        try:
            from dotenv import load_dotenv
            load_dotenv(self.base_dir / '.env')
        except ImportError:
            pass
        
        redis_url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
        
        # Parse Redis URL
        if redis_url.startswith('redis://'):
            parts = redis_url.replace('redis://', '').split(':')
            redis_host = parts[0]
            redis_port = int(parts[1].split('/')[0]) if len(parts) > 1 else 6379
        else:
            redis_host = 'localhost'
            redis_port = 6379
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((redis_host, redis_port))
            sock.close()
            
            if result != 0:
                self.warnings.append(f"Cannot connect to Redis at {redis_host}:{redis_port}")
                print(f"{Colors.YELLOW}⚠ Redis not accessible at {redis_host}:{redis_port}{Colors.END}")
                print(f"{Colors.YELLOW}  → Start Redis: sudo systemctl start redis{Colors.END}")
                return False
            
            print(f"{Colors.GREEN}✓ Redis accessible at {redis_host}:{redis_port}{Colors.END}")
            return True
        except Exception as e:
            self.warnings.append(f"Redis check failed: {str(e)}")
            print(f"{Colors.YELLOW}⚠ Redis check failed: {str(e)}{Colors.END}")
            return False
    
    def check_migrations(self):
        """Check if migrations need to be applied, and apply them automatically."""
        print(f"{Colors.CYAN}[7/7] Checking migrations...{Colors.END}")
        
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
            import django
            django.setup()
            
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connections, DEFAULT_DB_ALIAS
            
            connection = connections[DEFAULT_DB_ALIAS]
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            
            if plan:
                print(f"{Colors.YELLOW}⚠ Pending migrations detected{Colors.END}")
                print(f"{Colors.CYAN}  → Applying migrations automatically...{Colors.END}")
                
                # Run migrations
                try:
                    manage_py = self.base_dir / 'manage.py'
                    result = subprocess.run(
                        [sys.executable, str(manage_py), 'migrate', '--noinput'],
                        check=True,
                        capture_output=False,
                        text=True
                    )
                    print(f"{Colors.GREEN}✓ Migrations applied successfully{Colors.END}")
                    return True
                except subprocess.CalledProcessError as e:
                    self.warnings.append("Failed to apply migrations")
                    print(f"{Colors.RED}✗ Failed to apply migrations{Colors.END}")
                    print(f"{Colors.YELLOW}  → Run manually: python manage.py migrate{Colors.END}")
                    return False
            
            print(f"{Colors.GREEN}✓ All migrations applied{Colors.END}")
            return True
        except Exception as e:
            self.warnings.append(f"Migration check failed: {str(e)}")
            print(f"{Colors.YELLOW}⚠ Migration check skipped: {str(e)}{Colors.END}")
            return False
    
    def print_summary(self):
        """Print health check summary."""
        print(f"\n{Colors.BOLD}Health Check Summary:{Colors.END}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}Errors ({len(self.errors)}):{Colors.END}")
            for error in self.errors:
                print(f"  {Colors.RED}✗ {error}{Colors.END}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}Warnings ({len(self.warnings)}):{Colors.END}")
            for warning in self.warnings:
                print(f"  {Colors.YELLOW}⚠ {warning}{Colors.END}")
        
        if not self.errors and not self.warnings:
            print(f"{Colors.GREEN}✓ All checks passed!{Colors.END}")
    
    def run_server(self, host='127.0.0.1', port=7777):
        """Run the Django development server."""
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}Cannot start server due to errors.{Colors.END}")
            print(f"{Colors.YELLOW}Please fix the errors above and try again.{Colors.END}\n")
            sys.exit(1)
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}Starting server with warnings...{Colors.END}")
        else:
            print(f"\n{Colors.GREEN}Starting development server...{Colors.END}")
        
        print(f"\n{Colors.PURPLE}{Colors.BOLD}Server Information:{Colors.END}")
        print(f"  {Colors.CYAN}URL:{Colors.END} http://{host}:{port}/")
        print(f"  {Colors.CYAN}Admin:{Colors.END} http://{host}:{port}/admin/")
        print(f"  {Colors.CYAN}API:{Colors.END} http://{host}:{port}/api/")
        print(f"  {Colors.CYAN}Health:{Colors.END} http://{host}:{port}/api/health/")
        print(f"\n{Colors.YELLOW}Press Ctrl+C to stop the server{Colors.END}\n")
        
        # Set Django settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
        
        # Run Django development server
        try:
            manage_py = self.base_dir / 'manage.py'
            subprocess.run([
                sys.executable,
                str(manage_py),
                'runserver',
                f'{host}:{port}'
            ])
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Server stopped by user{Colors.END}")
            print(f"{Colors.PURPLE}Thank you for using DSAT SCHOOL Practice Portal!{Colors.END}\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n{Colors.RED}Error running server: {str(e)}{Colors.END}\n")
            sys.exit(1)
    
    def run(self, host='127.0.0.1', port=7777):
        """Run health checks and start the server."""
        self.print_header()
        
        # Run health checks
        self.check_python_version()
        self.check_virtual_env()
        self.check_env_file()
        self.check_dependencies()
        self.check_database()
        self.check_redis()
        self.check_migrations()
        
        # Print summary
        self.print_summary()
        
        # Start server
        self.run_server(host, port)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='DSAT SCHOOL Practice Portal - Development Server Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Run on default 127.0.0.1:7777
  python run.py --host 0.0.0.0     # Run on all interfaces
  python run.py --port 8080        # Run on custom port
  python run.py -h 0.0.0.0 -p 3000 # Custom host and port
        """
    )
    
    parser.add_argument(
        '--host', '-H',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=7777,
        help='Port to bind to (default: 7777)'
    )
    
    args = parser.parse_args()
    
    runner = DevRunner()
    runner.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
