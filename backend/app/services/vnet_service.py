"""Virtual Network provisioning service."""
from typing import Optional, Dict, Any, List
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import (
    VirtualNetwork,
    AddressSpace,
    Subnet,
    PublicIPAddress,
    NetworkInterface,
    NetworkInterfaceIPConfiguration,
    PublicIPAddressSku,
)
from ..auth.azure_auth import get_auth_manager
from ..models.schemas import (
    VNetConfig,
    PublicIPConfig,
    NetworkInterfaceConfig,
    ResourceCreationResponse
)


# Common Azure regions
AZURE_REGIONS = [
    "eastus",
    "eastus2",
    "westus",
    "westus2",
    "westus3",
    "centralus",
    "northcentralus",
    "southcentralus",
    "westcentralus",
    "canadacentral",
    "canadaeast",
    "brazilsouth",
    "northeurope",
    "westeurope",
    "uksouth",
    "ukwest",
    "francecentral",
    "germanywestcentral",
    "norwayeast",
    "switzerlandnorth",
    "uaenorth",
    "southafricanorth",
    "australiaeast",
    "australiasoutheast",
    "centralindia",
    "southindia",
    "japaneast",
    "japanwest",
    "koreacentral",
    "southeastasia",
    "eastasia"
]


class VNetService:
    """Service for Virtual Network operations."""
    
    def __init__(self):
        """Initialize VNet service with Azure auth manager."""
        self.auth_manager = get_auth_manager()
    
    def get_network_client(self, subscription_id: str) -> NetworkManagementClient:
        """Get network management client."""
        return self.auth_manager.get_network_client(subscription_id)
    
    @staticmethod
    def get_available_regions() -> List[str]:
        """Get list of available Azure regions."""
        return AZURE_REGIONS
    
    async def create_vnet(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: VNetConfig
    ) -> ResourceCreationResponse:
        """Create a Virtual Network with subnets."""
        try:
            network_client = self.get_network_client(subscription_id)
            
            # Build subnet configurations
            subnet_configs = [
                Subnet(
                    name=subnet["name"],
                    address_prefix=subnet["address_prefix"]
                )
                for subnet in config.subnets
            ]
            
            # VNet parameters
            vnet_params = VirtualNetwork(
                location=region,
                address_space=AddressSpace(address_prefixes=[config.address_space]),
                subnets=subnet_configs
            )
            
            # Create VNet
            poller = network_client.virtual_networks.begin_create_or_update(
                resource_group,
                config.name,
                vnet_params
            )
            
            result = poller.result()
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.Network/virtualNetworks",
                region=region,
                details={
                    "address_space": config.address_space,
                    "subnets": [
                        {"name": s.name, "address_prefix": s.address_prefix}
                        for s in result.subnets
                    ]
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    async def create_public_ip(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: PublicIPConfig
    ) -> ResourceCreationResponse:
        """Create a Public IP address."""
        try:
            network_client = self.get_network_client(subscription_id)
            
            pip_params = PublicIPAddress(
                location=region,
                sku=PublicIPAddressSku(name=config.sku),
                public_ip_allocation_method=config.allocation_method
            )
            
            poller = network_client.public_ip_addresses.begin_create_or_update(
                resource_group,
                config.name,
                pip_params
            )
            
            result = poller.result()
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.Network/publicIPAddresses",
                region=region,
                details={
                    "ip_address": result.ip_address,
                    "allocation_method": config.allocation_method,
                    "sku": config.sku
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    async def create_network_interface(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: NetworkInterfaceConfig
    ) -> ResourceCreationResponse:
        """Create a Network Interface."""
        try:
            network_client = self.get_network_client(subscription_id)
            
            # Get subnet reference
            subnet = network_client.subnets.get(
                resource_group,
                config.vnet_name,
                config.subnet_name
            )
            
            # Build IP configuration
            ip_config = NetworkInterfaceIPConfiguration(
                name=f"{config.name}-ipconfig",
                subnet={"id": subnet.id},
                private_ip_allocation_method="Dynamic"
            )
            
            # Add public IP if specified
            if config.public_ip_name:
                public_ip = network_client.public_ip_addresses.get(
                    resource_group,
                    config.public_ip_name
                )
                ip_config.public_ip_address = {"id": public_ip.id}
            
            # NIC parameters
            nic_params = NetworkInterface(
                location=region,
                ip_configurations=[ip_config]
            )
            
            poller = network_client.network_interfaces.begin_create_or_update(
                resource_group,
                config.name,
                nic_params
            )
            
            result = poller.result()
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.Network/networkInterfaces",
                region=region,
                details={
                    "vnet": config.vnet_name,
                    "subnet": config.subnet_name,
                    "has_public_ip": config.public_ip_name is not None
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    def get_vnet(
        self,
        subscription_id: str,
        resource_group: str,
        vnet_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get VNet details."""
        try:
            network_client = self.get_network_client(subscription_id)
            vnet = network_client.virtual_networks.get(resource_group, vnet_name)
            return {
                "name": vnet.name,
                "id": vnet.id,
                "location": vnet.location,
                "address_space": vnet.address_space.address_prefixes,
                "subnets": [
                    {"name": s.name, "address_prefix": s.address_prefix}
                    for s in vnet.subnets
                ] if vnet.subnets else []
            }
        except Exception:
            return None
    
    def list_vnets(
        self,
        subscription_id: str,
        resource_group: str
    ) -> List[Dict[str, Any]]:
        """List VNets in a resource group."""
        try:
            network_client = self.get_network_client(subscription_id)
            vnets = network_client.virtual_networks.list(resource_group)
            return [
                {
                    "name": vnet.name,
                    "location": vnet.location,
                    "address_space": vnet.address_space.address_prefixes[0] if vnet.address_space.address_prefixes else None
                }
                for vnet in vnets
            ]
        except Exception:
            return []

