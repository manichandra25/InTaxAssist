# Create the complete project structure with all files
import os
import json

# Create main project directory structure
project_name = "tax-filing-system"
os.makedirs(project_name, exist_ok=True)

# Create backend directory
backend_dir = os.path.join(project_name, "backend")
os.makedirs(backend_dir, exist_ok=True)

# Create services directory
services_dir = os.path.join(backend_dir, "services")
os.makedirs(services_dir, exist_ok=True)

# Create frontend directory
frontend_dir = os.path.join(project_name, "frontend")
os.makedirs(frontend_dir, exist_ok=True)

print(f"Created project structure for {project_name}")
print("Directories created:")
print(f"  - {project_name}/")
print(f"  - {project_name}/backend/")
print(f"  - {project_name}/backend/services/")
print(f"  - {project_name}/frontend/")