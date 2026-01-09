"""Azure Authentication Manager using Service Principal."""
import os
from typing import Optional
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from dotenv import load_dotenv

load_dotenv()


class AzureAuthManager:
    """Manages Azure authentication and client creation."""
    
    _instance: Optional["AzureAuthManager"] = None
    
    def __init__(self):
        """Initialize Azure credentials from environment variables."""
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError(
                "Missing Azure credentials. Please set AZURE_TENANT_ID, "
                "AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET environment variables."
            )
        
        self._credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
    
    @classmethod
    def get_instance(cls) -> "AzureAuthManager":
        """Get singleton instance of AzureAuthManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def credential(self) -> ClientSecretCredential:
        """Get Azure credential object."""
        return self._credential
    
    def get_resource_client(self, subscription_id: Optional[str] = None) -> ResourceManagementClient:
        """Get Resource Management client."""
        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            raise ValueError("Subscription ID is required")
        return ResourceManagementClient(self._credential, sub_id)
    
    def get_compute_client(self, subscription_id: Optional[str] = None) -> ComputeManagementClient:
        """Get Compute Management client."""
        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            raise ValueError("Subscription ID is required")
        return ComputeManagementClient(self._credential, sub_id)
    
    def get_network_client(self, subscription_id: Optional[str] = None) -> NetworkManagementClient:
        """Get Network Management client."""
        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            raise ValueError("Subscription ID is required")
        return NetworkManagementClient(self._credential, sub_id)
    
    def get_storage_client(self, subscription_id: Optional[str] = None) -> StorageManagementClient:
        """Get Storage Management client."""
        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            raise ValueError("Subscription ID is required")
        return StorageManagementClient(self._credential, sub_id)
    
    def get_container_client(self, subscription_id: Optional[str] = None) -> ContainerServiceClient:
        """Get Container Service client for AKS."""
        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            raise ValueError("Subscription ID is required")
        return ContainerServiceClient(self._credential, sub_id)
    
    def create_resource_group(
        self, 
        resource_group_name: str, 
        region: str,
        subscription_id: Optional[str] = None
    ) -> dict:
        """Create a resource group if it doesn't exist."""
        resource_client = self.get_resource_client(subscription_id)
        
        rg_result = resource_client.resource_groups.create_or_update(
            resource_group_name,
            {"location": region}
        )
        
        return {
            "name": rg_result.name,
            "location": rg_result.location,
            "id": rg_result.id
        }
    
    def list_resource_groups(self, subscription_id: Optional[str] = None) -> list:
        """List all resource groups in the subscription."""
        resource_client = self.get_resource_client(subscription_id)
        return [rg.name for rg in resource_client.resource_groups.list()]
    
    def validate_credentials(self) -> bool:
        """Validate that Azure credentials are working."""
        try:
            resource_client = self.get_resource_client()
            # Try to list resource groups to validate credentials
            list(resource_client.resource_groups.list())
            return True
        except Exception:
            return False


def get_auth_manager() -> AzureAuthManager:
    """Get the Azure auth manager instance."""
    return AzureAuthManager.get_instance()

