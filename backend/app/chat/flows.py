"""Conversation flow definitions for resource creation."""
from typing import Dict, Any, List, Optional, Tuple
from ..models.schemas import ResourceType, ConversationState
from ..services.vm_service import VMService, OS_IMAGES, VM_SIZES
from ..services.vnet_service import VNetService, AZURE_REGIONS
from ..services.storage_service import StorageService, STORAGE_SKUS, STORAGE_KINDS, ACCESS_TIERS
from ..services.aks_service import AKSService, AKS_VM_SIZES, K8S_VERSIONS, NETWORK_PLUGINS
from ..services.database_service import (
    DatabaseService, 
    POSTGRESQL_SKUS, POSTGRESQL_VERSIONS,
    MYSQL_SKUS, MYSQL_VERSIONS,
    SQL_TIERS, COSMOS_CONSISTENCY_LEVELS
)


class ResourceFlows:
    """Defines conversation flows for different resource types."""
    
    # Resource selection options
    RESOURCE_OPTIONS = {
        "vm": ("Virtual Machine", ResourceType.VIRTUAL_MACHINE),
        "vnet": ("Virtual Network", ResourceType.VIRTUAL_NETWORK),
        "storage": ("Storage Account", ResourceType.STORAGE_ACCOUNT),
        "aks": ("AKS Cluster", ResourceType.AKS_CLUSTER),
        "postgresql": ("PostgreSQL Database", ResourceType.POSTGRESQL),
        "mysql": ("MySQL Database", ResourceType.MYSQL),
        "sqldb": ("Azure SQL Database", ResourceType.SQL_DATABASE),
        "cosmosdb": ("Cosmos DB", ResourceType.COSMOSDB),
    }
    
    # Configuration questions for each resource type
    VM_QUESTIONS = [
        {
            "key": "name",
            "question": "What would you like to name your Virtual Machine?",
            "validation": lambda x: len(x) >= 1 and len(x) <= 64,
            "error": "VM name must be between 1 and 64 characters.",
            "default": None
        },
        {
            "key": "size",
            "question": "Select a VM size:",
            "options": VM_SIZES,
            "default": "Standard_B2s"
        },
        {
            "key": "os_image",
            "question": "Select an operating system:",
            "options": list(OS_IMAGES.keys()),
            "default": "Ubuntu2204"
        },
        {
            "key": "os_disk_type",
            "question": "Select OS disk type:",
            "options": ["Standard_LRS", "StandardSSD_LRS", "Premium_LRS"],
            "default": "Standard_LRS"
        },
        {
            "key": "admin_username",
            "question": "Enter admin username:",
            "validation": lambda x: len(x) >= 1 and len(x) <= 64 and x.lower() not in ["admin", "administrator", "root"],
            "error": "Username must be 1-64 characters and cannot be 'admin', 'administrator', or 'root'.",
            "default": "azureuser"
        },
        {
            "key": "create_public_ip",
            "question": "Create a public IP address for remote access?",
            "options": ["yes", "no"],
            "default": "yes",
            "transform": lambda x: x.lower() == "yes"
        }
    ]
    
    VNET_QUESTIONS = [
        {
            "key": "name",
            "question": "What would you like to name your Virtual Network?",
            "validation": lambda x: len(x) >= 2 and len(x) <= 64,
            "error": "VNet name must be between 2 and 64 characters.",
            "default": None
        },
        {
            "key": "address_space",
            "question": "Enter the address space (CIDR notation, e.g., 10.0.0.0/16):",
            "validation": lambda x: "/" in x and len(x.split("/")) == 2,
            "error": "Please enter a valid CIDR notation (e.g., 10.0.0.0/16).",
            "default": "10.0.0.0/16"
        },
        {
            "key": "subnet_name",
            "question": "Enter the name for the default subnet:",
            "default": "default"
        },
        {
            "key": "subnet_prefix",
            "question": "Enter the subnet address prefix (e.g., 10.0.0.0/24):",
            "validation": lambda x: "/" in x and len(x.split("/")) == 2,
            "error": "Please enter a valid CIDR notation (e.g., 10.0.0.0/24).",
            "default": "10.0.0.0/24"
        }
    ]
    
    STORAGE_QUESTIONS = [
        {
            "key": "name",
            "question": "Enter a name for your Storage Account (3-24 chars, lowercase letters and numbers only):",
            "validation": lambda x: len(x) >= 3 and len(x) <= 24 and x.isalnum() and x.islower(),
            "error": "Storage account name must be 3-24 characters, lowercase letters and numbers only.",
            "default": None
        },
        {
            "key": "sku",
            "question": "Select storage redundancy (SKU):",
            "options": STORAGE_SKUS,
            "default": "Standard_LRS"
        },
        {
            "key": "kind",
            "question": "Select storage account kind:",
            "options": STORAGE_KINDS,
            "default": "StorageV2"
        },
        {
            "key": "access_tier",
            "question": "Select access tier:",
            "options": ACCESS_TIERS,
            "default": "Hot"
        }
    ]
    
    AKS_QUESTIONS = [
        {
            "key": "name",
            "question": "What would you like to name your AKS cluster?",
            "validation": lambda x: len(x) >= 1 and len(x) <= 63 and x.replace("-", "").replace("_", "").isalnum(),
            "error": "AKS name must be 1-63 characters, alphanumeric, hyphens, and underscores only.",
            "default": None
        },
        {
            "key": "dns_prefix",
            "question": "Enter a DNS prefix for the cluster:",
            "validation": lambda x: len(x) >= 1 and x.replace("-", "").isalnum(),
            "error": "DNS prefix must be alphanumeric with optional hyphens.",
            "default": None
        },
        {
            "key": "kubernetes_version",
            "question": "Select Kubernetes version:",
            "options": K8S_VERSIONS,
            "default": "1.28"
        },
        {
            "key": "node_count",
            "question": "How many nodes in the default node pool? (1-100):",
            "validation": lambda x: x.isdigit() and 1 <= int(x) <= 100,
            "error": "Node count must be between 1 and 100.",
            "default": "3",
            "transform": lambda x: int(x)
        },
        {
            "key": "node_vm_size",
            "question": "Select VM size for nodes:",
            "options": AKS_VM_SIZES,
            "default": "Standard_D2s_v3"
        },
        {
            "key": "network_plugin",
            "question": "Select network plugin:",
            "options": NETWORK_PLUGINS,
            "default": "azure"
        }
    ]
    
    POSTGRESQL_QUESTIONS = [
        {
            "key": "name",
            "question": "Enter a name for your PostgreSQL server (3-63 chars, lowercase, hyphens allowed):",
            "validation": lambda x: len(x) >= 3 and len(x) <= 63 and x.replace("-", "").isalnum(),
            "error": "Server name must be 3-63 characters, lowercase letters, numbers, and hyphens.",
            "default": None
        },
        {
            "key": "version",
            "question": "Select PostgreSQL version:",
            "options": POSTGRESQL_VERSIONS,
            "default": "15"
        },
        {
            "key": "sku",
            "question": "Select compute tier/SKU:",
            "options": POSTGRESQL_SKUS,
            "default": "Standard_B1ms"
        },
        {
            "key": "storage_gb",
            "question": "Storage size in GB (32-16384):",
            "validation": lambda x: x.isdigit() and 32 <= int(x) <= 16384,
            "error": "Storage must be between 32 and 16384 GB.",
            "default": "32",
            "transform": lambda x: int(x)
        },
        {
            "key": "admin_username",
            "question": "Enter admin username:",
            "validation": lambda x: len(x) >= 1 and x.lower() not in ["admin", "administrator", "root", "postgres", "azure_superuser"],
            "error": "Username cannot be reserved words like admin, postgres, root, etc.",
            "default": "pgadmin"
        }
    ]
    
    MYSQL_QUESTIONS = [
        {
            "key": "name",
            "question": "Enter a name for your MySQL server (3-63 chars, lowercase, hyphens allowed):",
            "validation": lambda x: len(x) >= 3 and len(x) <= 63 and x.replace("-", "").isalnum(),
            "error": "Server name must be 3-63 characters, lowercase letters, numbers, and hyphens.",
            "default": None
        },
        {
            "key": "version",
            "question": "Select MySQL version:",
            "options": MYSQL_VERSIONS,
            "default": "8.0.21"
        },
        {
            "key": "sku",
            "question": "Select compute tier/SKU:",
            "options": MYSQL_SKUS,
            "default": "Standard_B1ms"
        },
        {
            "key": "storage_gb",
            "question": "Storage size in GB (20-16384):",
            "validation": lambda x: x.isdigit() and 20 <= int(x) <= 16384,
            "error": "Storage must be between 20 and 16384 GB.",
            "default": "32",
            "transform": lambda x: int(x)
        },
        {
            "key": "admin_username",
            "question": "Enter admin username:",
            "validation": lambda x: len(x) >= 1 and x.lower() not in ["admin", "administrator", "root", "mysql", "azure_superuser"],
            "error": "Username cannot be reserved words like admin, mysql, root, etc.",
            "default": "mysqladmin"
        }
    ]
    
    SQLDB_QUESTIONS = [
        {
            "key": "name",
            "question": "Enter a name for your SQL Database:",
            "validation": lambda x: len(x) >= 1 and len(x) <= 128,
            "error": "Database name must be 1-128 characters.",
            "default": None
        },
        {
            "key": "server_name",
            "question": "Enter a name for the SQL Server (will be created):",
            "validation": lambda x: len(x) >= 1 and len(x) <= 63 and x.replace("-", "").isalnum(),
            "error": "Server name must be 1-63 characters, lowercase letters, numbers, and hyphens.",
            "default": None
        },
        {
            "key": "tier",
            "question": "Select pricing tier:",
            "options": SQL_TIERS,
            "default": "Basic"
        },
        {
            "key": "admin_username",
            "question": "Enter admin username:",
            "validation": lambda x: len(x) >= 1 and x.lower() not in ["admin", "administrator", "sa", "root"],
            "error": "Username cannot be reserved words like admin, sa, root.",
            "default": "sqladmin"
        }
    ]
    
    COSMOSDB_QUESTIONS = [
        {
            "key": "name",
            "question": "Enter a name for your Cosmos DB account (3-44 chars, lowercase):",
            "validation": lambda x: len(x) >= 3 and len(x) <= 44 and x.replace("-", "").isalnum() and x.islower(),
            "error": "Account name must be 3-44 characters, lowercase letters, numbers, and hyphens.",
            "default": None
        },
        {
            "key": "api_type",
            "question": "Select API type:",
            "options": ["SQL", "MongoDB", "Cassandra", "Table", "Gremlin"],
            "default": "SQL"
        },
        {
            "key": "consistency_level",
            "question": "Select default consistency level:",
            "options": COSMOS_CONSISTENCY_LEVELS,
            "default": "Session"
        },
        {
            "key": "enable_free_tier",
            "question": "Enable free tier? (400 RU/s and 5 GB free per account):",
            "options": ["yes", "no"],
            "default": "no",
            "transform": lambda x: x.lower() == "yes"
        }
    ]
    
    @classmethod
    def get_questions_for_resource(cls, resource_type: ResourceType) -> List[Dict[str, Any]]:
        """Get the list of questions for a resource type."""
        questions_map = {
            ResourceType.VIRTUAL_MACHINE: cls.VM_QUESTIONS,
            ResourceType.VIRTUAL_NETWORK: cls.VNET_QUESTIONS,
            ResourceType.STORAGE_ACCOUNT: cls.STORAGE_QUESTIONS,
            ResourceType.AKS_CLUSTER: cls.AKS_QUESTIONS,
            ResourceType.POSTGRESQL: cls.POSTGRESQL_QUESTIONS,
            ResourceType.MYSQL: cls.MYSQL_QUESTIONS,
            ResourceType.SQL_DATABASE: cls.SQLDB_QUESTIONS,
            ResourceType.COSMOSDB: cls.COSMOSDB_QUESTIONS,
        }
        return questions_map.get(resource_type, [])
    
    @classmethod
    def get_available_regions(cls) -> List[str]:
        """Get list of available Azure regions."""
        return AZURE_REGIONS
    
    @classmethod
    def parse_resource_selection(cls, user_input: str) -> Optional[ResourceType]:
        """Parse user input to determine resource type."""
        user_input = user_input.lower().strip()
        
        # Direct matches
        for key, (name, resource_type) in cls.RESOURCE_OPTIONS.items():
            if key in user_input or name.lower() in user_input:
                return resource_type
        
        # Partial matches
        if "virtual machine" in user_input or "vm" in user_input:
            return ResourceType.VIRTUAL_MACHINE
        if "virtual network" in user_input or "vnet" in user_input or ("network" in user_input and "vn" in user_input):
            return ResourceType.VIRTUAL_NETWORK
        if "storage" in user_input or "blob" in user_input:
            return ResourceType.STORAGE_ACCOUNT
        if "aks" in user_input or "kubernetes" in user_input or "k8s" in user_input:
            return ResourceType.AKS_CLUSTER
        if "postgresql" in user_input or "postgres" in user_input or "pgsql" in user_input:
            return ResourceType.POSTGRESQL
        if "mysql" in user_input:
            return ResourceType.MYSQL
        if "sql" in user_input and "cosmos" not in user_input:
            return ResourceType.SQL_DATABASE
        if "cosmos" in user_input or "documentdb" in user_input or "nosql" in user_input:
            return ResourceType.COSMOSDB
        if "database" in user_input or "db" in user_input:
            # Generic database - default to PostgreSQL
            return ResourceType.POSTGRESQL
        
        return None
    
    @classmethod
    def validate_answer(
        cls,
        question: Dict[str, Any],
        answer: str
    ) -> Tuple[bool, Optional[str], Any]:
        """
        Validate an answer against a question's rules.
        Returns (is_valid, error_message, transformed_value)
        """
        answer = answer.strip()
        
        # Use default if answer is empty
        if not answer and question.get("default") is not None:
            answer = str(question["default"])
        
        # Check if answer is in options (if options exist)
        if "options" in question:
            options = question["options"]
            # Try to match by index
            if answer.isdigit():
                idx = int(answer) - 1
                if 0 <= idx < len(options):
                    answer = options[idx]
            # Try to match by value (case-insensitive)
            matched = None
            for opt in options:
                if opt.lower() == answer.lower():
                    matched = opt
                    break
            if matched:
                answer = matched
            elif answer.lower() not in [o.lower() for o in options]:
                return False, f"Please select from: {', '.join(options)}", None
        
        # Custom validation
        if "validation" in question:
            if not question["validation"](answer):
                return False, question.get("error", "Invalid input."), None
        
        # Transform the value if needed
        value = answer
        if "transform" in question:
            value = question["transform"](answer)
        
        return True, None, value
    
    @classmethod
    def format_options_message(cls, options: List[str]) -> str:
        """Format options as a numbered list."""
        return "\n".join([f"  {i+1}. {opt}" for i, opt in enumerate(options)])
    
    @classmethod
    def get_resource_type_prompt(cls) -> str:
        """Get the prompt for resource type selection."""
        options = [
            "**Compute & Networking:**",
            "  1. Virtual Machine (VM)",
            "  2. Virtual Network (VNet)",
            "  3. AKS Cluster (Kubernetes)",
            "",
            "**Storage:**",
            "  4. Storage Account",
            "",
            "**Databases:**",
            "  5. PostgreSQL Database",
            "  6. MySQL Database", 
            "  7. Azure SQL Database",
            "  8. Cosmos DB (NoSQL)"
        ]
        return "What type of Azure resource would you like to create?\n\n" + "\n".join(options)
    
    @classmethod
    def build_config_from_answers(
        cls,
        resource_type: ResourceType,
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the final configuration object from collected answers."""
        if resource_type == ResourceType.VIRTUAL_MACHINE:
            return {
                "name": answers.get("name"),
                "size": answers.get("size", "Standard_B2s"),
                "os_image": answers.get("os_image", "Ubuntu2204"),
                "os_disk_type": answers.get("os_disk_type", "Standard_LRS"),
                "admin_username": answers.get("admin_username", "azureuser"),
                "create_public_ip": answers.get("create_public_ip", True),
                "generate_ssh_key": True
            }
        
        elif resource_type == ResourceType.VIRTUAL_NETWORK:
            return {
                "name": answers.get("name"),
                "address_space": answers.get("address_space", "10.0.0.0/16"),
                "subnets": [
                    {
                        "name": answers.get("subnet_name", "default"),
                        "address_prefix": answers.get("subnet_prefix", "10.0.0.0/24")
                    }
                ]
            }
        
        elif resource_type == ResourceType.STORAGE_ACCOUNT:
            return {
                "name": answers.get("name"),
                "sku": answers.get("sku", "Standard_LRS"),
                "kind": answers.get("kind", "StorageV2"),
                "access_tier": answers.get("access_tier", "Hot"),
                "enable_https_only": True
            }
        
        elif resource_type == ResourceType.AKS_CLUSTER:
            return {
                "name": answers.get("name"),
                "dns_prefix": answers.get("dns_prefix", answers.get("name")),
                "kubernetes_version": answers.get("kubernetes_version", "1.28"),
                "node_count": answers.get("node_count", 3),
                "node_vm_size": answers.get("node_vm_size", "Standard_D2s_v3"),
                "network_plugin": answers.get("network_plugin", "azure"),
                "enable_rbac": True
            }
        
        elif resource_type == ResourceType.POSTGRESQL:
            return {
                "name": answers.get("name"),
                "version": answers.get("version", "15"),
                "sku": answers.get("sku", "Standard_B1ms"),
                "storage_gb": answers.get("storage_gb", 32),
                "admin_username": answers.get("admin_username", "pgadmin")
            }
        
        elif resource_type == ResourceType.MYSQL:
            return {
                "name": answers.get("name"),
                "version": answers.get("version", "8.0.21"),
                "sku": answers.get("sku", "Standard_B1ms"),
                "storage_gb": answers.get("storage_gb", 32),
                "admin_username": answers.get("admin_username", "mysqladmin")
            }
        
        elif resource_type == ResourceType.SQL_DATABASE:
            return {
                "name": answers.get("name"),
                "server_name": answers.get("server_name"),
                "tier": answers.get("tier", "Basic"),
                "admin_username": answers.get("admin_username", "sqladmin")
            }
        
        elif resource_type == ResourceType.COSMOSDB:
            return {
                "name": answers.get("name"),
                "api_type": answers.get("api_type", "SQL"),
                "consistency_level": answers.get("consistency_level", "Session"),
                "enable_free_tier": answers.get("enable_free_tier", False)
            }
        
        return answers

