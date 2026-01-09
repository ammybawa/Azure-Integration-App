"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum


class ResourceType(str, Enum):
    """Supported Azure resource types."""
    VIRTUAL_MACHINE = "vm"
    VIRTUAL_NETWORK = "vnet"
    STORAGE_ACCOUNT = "storage"
    AKS_CLUSTER = "aks"
    NETWORK_INTERFACE = "nic"
    PUBLIC_IP = "publicip"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQL_DATABASE = "sqldb"
    COSMOSDB = "cosmosdb"


class ConversationState(str, Enum):
    """States of the conversation flow."""
    INITIAL = "initial"
    RESOURCE_SELECTION = "resource_selection"
    SUBSCRIPTION = "subscription"
    RESOURCE_GROUP = "resource_group"
    REGION = "region"
    RESOURCE_CONFIG = "resource_config"
    CONFIRMATION = "confirmation"
    EXECUTION_METHOD = "execution_method"
    CREATING = "creating"
    COMPLETED = "completed"
    ERROR = "error"


class ChatMessage(BaseModel):
    """Chat message model."""
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    session_id: str
    message: str
    state: ConversationState
    options: Optional[List[str]] = None
    resource_summary: Optional[Dict[str, Any]] = None
    cost_estimate: Optional[Dict[str, Any]] = None
    terraform_code: Optional[str] = None
    created_resource: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class VMConfig(BaseModel):
    """Virtual Machine configuration."""
    name: str
    size: str = "Standard_B2s"
    os_image: str = "Ubuntu2204"
    os_disk_type: str = "Standard_LRS"
    admin_username: str = "azureuser"
    generate_ssh_key: bool = True
    vnet_name: Optional[str] = None
    subnet_name: Optional[str] = None
    create_public_ip: bool = True


class VNetConfig(BaseModel):
    """Virtual Network configuration."""
    name: str
    address_space: str = "10.0.0.0/16"
    subnets: List[Dict[str, str]] = Field(
        default_factory=lambda: [{"name": "default", "address_prefix": "10.0.0.0/24"}]
    )


class StorageConfig(BaseModel):
    """Storage Account configuration."""
    name: str
    sku: str = "Standard_LRS"
    kind: str = "StorageV2"
    access_tier: str = "Hot"
    enable_https_only: bool = True


class AKSConfig(BaseModel):
    """AKS Cluster configuration."""
    name: str
    dns_prefix: str
    node_count: int = 3
    node_vm_size: str = "Standard_D2s_v3"
    kubernetes_version: str = "1.28"
    enable_rbac: bool = True
    network_plugin: str = "azure"


class PublicIPConfig(BaseModel):
    """Public IP configuration."""
    name: str
    sku: str = "Standard"
    allocation_method: str = "Static"


class NetworkInterfaceConfig(BaseModel):
    """Network Interface configuration."""
    name: str
    vnet_name: str
    subnet_name: str
    public_ip_name: Optional[str] = None


class PostgreSQLConfig(BaseModel):
    """PostgreSQL Flexible Server configuration."""
    name: str
    admin_username: str = "pgadmin"
    admin_password: Optional[str] = None
    sku: str = "Standard_B1ms"
    version: str = "15"
    storage_gb: int = 32


class MySQLConfig(BaseModel):
    """MySQL Flexible Server configuration."""
    name: str
    admin_username: str = "mysqladmin"
    admin_password: Optional[str] = None
    sku: str = "Standard_B1ms"
    version: str = "8.0.21"
    storage_gb: int = 32


class SQLDatabaseConfig(BaseModel):
    """Azure SQL Database configuration."""
    name: str
    server_name: Optional[str] = None
    admin_username: str = "sqladmin"
    admin_password: Optional[str] = None
    tier: str = "Basic"


class CosmosDBConfig(BaseModel):
    """Cosmos DB configuration."""
    name: str
    api_type: str = "SQL"
    consistency_level: str = "Session"
    enable_free_tier: bool = False


class ResourceCreationRequest(BaseModel):
    """Request for resource creation."""
    resource_type: ResourceType
    subscription_id: str
    resource_group: str
    region: str
    config: Dict[str, Any]
    create_new_rg: bool = False


class ResourceCreationResponse(BaseModel):
    """Response after resource creation."""
    success: bool
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    resource_type: Optional[str] = None
    region: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CostEstimate(BaseModel):
    """Cost estimation response."""
    resource_type: str
    estimated_monthly_cost: float
    currency: str = "USD"
    breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    disclaimer: str = "Estimates are approximate and may vary based on actual usage."


class ConversationSession(BaseModel):
    """Conversation session state."""
    session_id: str
    state: ConversationState = ConversationState.INITIAL
    resource_type: Optional[ResourceType] = None
    subscription_id: Optional[str] = None
    resource_group: Optional[str] = None
    create_new_rg: bool = False
    region: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    execution_method: Optional[Literal["azure_sdk", "terraform"]] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    current_question: Optional[str] = None
    collected_params: Dict[str, Any] = Field(default_factory=dict)

