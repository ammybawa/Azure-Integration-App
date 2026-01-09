"""Storage Account provisioning service."""
import re
from typing import Optional, Dict, Any, List
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import (
    StorageAccountCreateParameters,
    Sku,
    Kind,
    StorageAccountCheckNameAvailabilityParameters,
)
from ..auth.azure_auth import get_auth_manager
from ..models.schemas import StorageConfig, ResourceCreationResponse


# Storage SKUs
STORAGE_SKUS = [
    "Standard_LRS",      # Locally redundant storage
    "Standard_GRS",      # Geo-redundant storage
    "Standard_RAGRS",    # Read-access geo-redundant storage
    "Standard_ZRS",      # Zone-redundant storage
    "Premium_LRS",       # Premium locally redundant storage
    "Premium_ZRS",       # Premium zone-redundant storage
]

# Storage kinds
STORAGE_KINDS = [
    "StorageV2",         # General purpose v2 (recommended)
    "Storage",           # General purpose v1
    "BlobStorage",       # Blob storage
    "BlockBlobStorage",  # Block blob storage
    "FileStorage",       # File storage
]

# Access tiers
ACCESS_TIERS = ["Hot", "Cool"]


class StorageService:
    """Service for Storage Account operations."""
    
    def __init__(self):
        """Initialize Storage service with Azure auth manager."""
        self.auth_manager = get_auth_manager()
    
    def get_storage_client(self, subscription_id: str) -> StorageManagementClient:
        """Get storage management client."""
        return self.auth_manager.get_storage_client(subscription_id)
    
    @staticmethod
    def get_available_skus() -> List[str]:
        """Get list of available storage SKUs."""
        return STORAGE_SKUS
    
    @staticmethod
    def get_available_kinds() -> List[str]:
        """Get list of available storage kinds."""
        return STORAGE_KINDS
    
    @staticmethod
    def get_available_access_tiers() -> List[str]:
        """Get list of available access tiers."""
        return ACCESS_TIERS
    
    @staticmethod
    def validate_storage_name(name: str) -> tuple:
        """
        Validate storage account name.
        Returns (is_valid, error_message)
        """
        if len(name) < 3 or len(name) > 24:
            return False, "Storage account name must be between 3 and 24 characters."
        
        if not re.match(r'^[a-z0-9]+$', name):
            return False, "Storage account name can only contain lowercase letters and numbers."
        
        return True, None
    
    def check_name_availability(
        self,
        subscription_id: str,
        name: str
    ) -> tuple:
        """
        Check if storage account name is available.
        Returns (is_available, message)
        """
        # First validate the name format
        is_valid, error = self.validate_storage_name(name)
        if not is_valid:
            return False, error
        
        try:
            storage_client = self.get_storage_client(subscription_id)
            result = storage_client.storage_accounts.check_name_availability(
                StorageAccountCheckNameAvailabilityParameters(name=name)
            )
            
            if result.name_available:
                return True, "Name is available"
            else:
                return False, result.message or "Name is not available"
                
        except Exception as e:
            return False, str(e)
    
    async def create_storage_account(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: StorageConfig
    ) -> ResourceCreationResponse:
        """Create a Storage Account."""
        try:
            # Validate name first
            is_valid, error = self.validate_storage_name(config.name)
            if not is_valid:
                return ResourceCreationResponse(
                    success=False,
                    error=error
                )
            
            storage_client = self.get_storage_client(subscription_id)
            
            # Check name availability
            is_available, message = self.check_name_availability(subscription_id, config.name)
            if not is_available:
                return ResourceCreationResponse(
                    success=False,
                    error=f"Storage account name validation failed: {message}"
                )
            
            # Storage account parameters
            storage_params = StorageAccountCreateParameters(
                sku=Sku(name=config.sku),
                kind=Kind(config.kind),
                location=region,
                enable_https_traffic_only=config.enable_https_only,
                access_tier=config.access_tier if config.kind != "BlobStorage" else None
            )
            
            # Create storage account
            poller = storage_client.storage_accounts.begin_create(
                resource_group,
                config.name,
                storage_params
            )
            
            result = poller.result()
            
            # Get connection string
            keys = storage_client.storage_accounts.list_keys(
                resource_group,
                config.name
            )
            
            primary_key = keys.keys[0].value if keys.keys else None
            connection_string = None
            
            if primary_key:
                connection_string = (
                    f"DefaultEndpointsProtocol=https;"
                    f"AccountName={config.name};"
                    f"AccountKey={primary_key};"
                    f"EndpointSuffix=core.windows.net"
                )
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.Storage/storageAccounts",
                region=region,
                details={
                    "sku": config.sku,
                    "kind": config.kind,
                    "access_tier": config.access_tier,
                    "primary_endpoints": {
                        "blob": result.primary_endpoints.blob,
                        "file": result.primary_endpoints.file,
                        "queue": result.primary_endpoints.queue,
                        "table": result.primary_endpoints.table
                    },
                    "connection_string": connection_string,
                    "note": "Store the connection string securely."
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    async def delete_storage_account(
        self,
        subscription_id: str,
        resource_group: str,
        account_name: str
    ) -> bool:
        """Delete a Storage Account."""
        try:
            storage_client = self.get_storage_client(subscription_id)
            storage_client.storage_accounts.delete(
                resource_group,
                account_name
            )
            return True
        except Exception:
            return False
    
    def get_storage_account(
        self,
        subscription_id: str,
        resource_group: str,
        account_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get storage account details."""
        try:
            storage_client = self.get_storage_client(subscription_id)
            account = storage_client.storage_accounts.get_properties(
                resource_group,
                account_name
            )
            return {
                "name": account.name,
                "id": account.id,
                "location": account.location,
                "sku": account.sku.name,
                "kind": account.kind,
                "provisioning_state": account.provisioning_state
            }
        except Exception:
            return None
    
    def list_storage_accounts(
        self,
        subscription_id: str,
        resource_group: str
    ) -> List[Dict[str, Any]]:
        """List storage accounts in a resource group."""
        try:
            storage_client = self.get_storage_client(subscription_id)
            accounts = storage_client.storage_accounts.list_by_resource_group(resource_group)
            return [
                {
                    "name": account.name,
                    "location": account.location,
                    "sku": account.sku.name
                }
                for account in accounts
            ]
        except Exception:
            return []

