"""Azure Kubernetes Service (AKS) provisioning service."""
from typing import Optional, Dict, Any, List
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.containerservice.models import (
    ManagedCluster,
    ManagedClusterAgentPoolProfile,
    ManagedClusterIdentity,
    ContainerServiceNetworkProfile,
    ManagedClusterServicePrincipalProfile,
)
from ..auth.azure_auth import get_auth_manager
from ..models.schemas import AKSConfig, ResourceCreationResponse


# AKS Node VM sizes
AKS_VM_SIZES = [
    "Standard_D2s_v3",
    "Standard_D4s_v3",
    "Standard_D8s_v3",
    "Standard_D2s_v4",
    "Standard_D4s_v4",
    "Standard_E2s_v3",
    "Standard_E4s_v3",
    "Standard_B2s",
    "Standard_B4ms",
    "Standard_F4s_v2",
]

# Supported Kubernetes versions
K8S_VERSIONS = [
    "1.28",
    "1.27",
    "1.26",
]

# Network plugins
NETWORK_PLUGINS = [
    "azure",
    "kubenet",
]


class AKSService:
    """Service for Azure Kubernetes Service operations."""
    
    def __init__(self):
        """Initialize AKS service with Azure auth manager."""
        self.auth_manager = get_auth_manager()
    
    def get_container_client(self, subscription_id: str) -> ContainerServiceClient:
        """Get container service client."""
        return self.auth_manager.get_container_client(subscription_id)
    
    @staticmethod
    def get_available_vm_sizes() -> List[str]:
        """Get list of available VM sizes for AKS nodes."""
        return AKS_VM_SIZES
    
    @staticmethod
    def get_available_k8s_versions() -> List[str]:
        """Get list of available Kubernetes versions."""
        return K8S_VERSIONS
    
    @staticmethod
    def get_available_network_plugins() -> List[str]:
        """Get list of available network plugins."""
        return NETWORK_PLUGINS
    
    async def create_aks_cluster(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: AKSConfig
    ) -> ResourceCreationResponse:
        """Create an AKS cluster."""
        try:
            container_client = self.get_container_client(subscription_id)
            
            # Agent pool profile
            agent_pool = ManagedClusterAgentPoolProfile(
                name="nodepool1",
                count=config.node_count,
                vm_size=config.node_vm_size,
                os_type="Linux",
                mode="System",
                type="VirtualMachineScaleSets",
                enable_auto_scaling=False,
            )
            
            # Network profile
            network_profile = ContainerServiceNetworkProfile(
                network_plugin=config.network_plugin,
                load_balancer_sku="standard",
            )
            
            # Managed cluster parameters
            cluster_params = ManagedCluster(
                location=region,
                dns_prefix=config.dns_prefix,
                kubernetes_version=config.kubernetes_version,
                agent_pool_profiles=[agent_pool],
                network_profile=network_profile,
                enable_rbac=config.enable_rbac,
                identity=ManagedClusterIdentity(type="SystemAssigned"),
            )
            
            # Create AKS cluster
            poller = container_client.managed_clusters.begin_create_or_update(
                resource_group,
                config.name,
                cluster_params
            )
            
            result = poller.result()
            
            # Get kubeconfig
            kubeconfig = self.get_kubeconfig(
                subscription_id,
                resource_group,
                config.name
            )
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.ContainerService/managedClusters",
                region=region,
                details={
                    "kubernetes_version": result.kubernetes_version,
                    "dns_prefix": result.dns_prefix,
                    "fqdn": result.fqdn,
                    "node_count": config.node_count,
                    "node_vm_size": config.node_vm_size,
                    "network_plugin": config.network_plugin,
                    "enable_rbac": config.enable_rbac,
                    "provisioning_state": result.provisioning_state,
                    "kubeconfig_note": "Use 'az aks get-credentials' to get kubeconfig"
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    def get_kubeconfig(
        self,
        subscription_id: str,
        resource_group: str,
        cluster_name: str
    ) -> Optional[str]:
        """Get kubeconfig for AKS cluster."""
        try:
            container_client = self.get_container_client(subscription_id)
            credentials = container_client.managed_clusters.list_cluster_admin_credentials(
                resource_group,
                cluster_name
            )
            
            if credentials.kubeconfigs:
                return credentials.kubeconfigs[0].value.decode('utf-8')
            return None
            
        except Exception:
            return None
    
    async def delete_aks_cluster(
        self,
        subscription_id: str,
        resource_group: str,
        cluster_name: str
    ) -> bool:
        """Delete an AKS cluster."""
        try:
            container_client = self.get_container_client(subscription_id)
            poller = container_client.managed_clusters.begin_delete(
                resource_group,
                cluster_name
            )
            poller.result()
            return True
        except Exception:
            return False
    
    def get_aks_cluster(
        self,
        subscription_id: str,
        resource_group: str,
        cluster_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get AKS cluster details."""
        try:
            container_client = self.get_container_client(subscription_id)
            cluster = container_client.managed_clusters.get(
                resource_group,
                cluster_name
            )
            return {
                "name": cluster.name,
                "id": cluster.id,
                "location": cluster.location,
                "kubernetes_version": cluster.kubernetes_version,
                "fqdn": cluster.fqdn,
                "provisioning_state": cluster.provisioning_state,
                "agent_pools": [
                    {
                        "name": pool.name,
                        "count": pool.count,
                        "vm_size": pool.vm_size
                    }
                    for pool in cluster.agent_pool_profiles
                ] if cluster.agent_pool_profiles else []
            }
        except Exception:
            return None
    
    def list_aks_clusters(
        self,
        subscription_id: str,
        resource_group: str
    ) -> List[Dict[str, Any]]:
        """List AKS clusters in a resource group."""
        try:
            container_client = self.get_container_client(subscription_id)
            clusters = container_client.managed_clusters.list_by_resource_group(resource_group)
            return [
                {
                    "name": cluster.name,
                    "location": cluster.location,
                    "kubernetes_version": cluster.kubernetes_version,
                    "provisioning_state": cluster.provisioning_state
                }
                for cluster in clusters
            ]
        except Exception:
            return []
    
    async def scale_node_pool(
        self,
        subscription_id: str,
        resource_group: str,
        cluster_name: str,
        node_pool_name: str,
        node_count: int
    ) -> bool:
        """Scale an AKS node pool."""
        try:
            container_client = self.get_container_client(subscription_id)
            
            # Get current agent pool
            agent_pool = container_client.agent_pools.get(
                resource_group,
                cluster_name,
                node_pool_name
            )
            
            # Update count
            agent_pool.count = node_count
            
            poller = container_client.agent_pools.begin_create_or_update(
                resource_group,
                cluster_name,
                node_pool_name,
                agent_pool
            )
            poller.result()
            return True
            
        except Exception:
            return False

