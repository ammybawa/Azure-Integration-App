"""Virtual Machine provisioning service."""
import secrets
from typing import Optional, Dict, Any
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import (
    VirtualMachine,
    HardwareProfile,
    StorageProfile,
    OSDisk,
    ImageReference,
    OSProfile,
    LinuxConfiguration,
    SshConfiguration,
    SshPublicKey,
    NetworkProfile,
    NetworkInterfaceReference,
    DiskCreateOptionTypes,
    CachingTypes,
)
from ..auth.azure_auth import get_auth_manager
from ..models.schemas import VMConfig, ResourceCreationResponse


# OS Image mappings
OS_IMAGES = {
    "Ubuntu2204": {
        "publisher": "Canonical",
        "offer": "0001-com-ubuntu-server-jammy",
        "sku": "22_04-lts-gen2",
        "version": "latest"
    },
    "Ubuntu2004": {
        "publisher": "Canonical",
        "offer": "0001-com-ubuntu-server-focal",
        "sku": "20_04-lts-gen2",
        "version": "latest"
    },
    "WindowsServer2022": {
        "publisher": "MicrosoftWindowsServer",
        "offer": "WindowsServer",
        "sku": "2022-datacenter-g2",
        "version": "latest"
    },
    "WindowsServer2019": {
        "publisher": "MicrosoftWindowsServer",
        "offer": "WindowsServer",
        "sku": "2019-datacenter-g2",
        "version": "latest"
    },
    "RHEL8": {
        "publisher": "RedHat",
        "offer": "RHEL",
        "sku": "8-lvm-gen2",
        "version": "latest"
    },
    "Debian11": {
        "publisher": "Debian",
        "offer": "debian-11",
        "sku": "11-gen2",
        "version": "latest"
    }
}

# VM Sizes
VM_SIZES = [
    "Standard_B1s",
    "Standard_B2s",
    "Standard_B2ms",
    "Standard_D2s_v3",
    "Standard_D4s_v3",
    "Standard_D8s_v3",
    "Standard_E2s_v3",
    "Standard_E4s_v3",
    "Standard_F2s_v2",
    "Standard_F4s_v2"
]


class VMService:
    """Service for Virtual Machine operations."""
    
    def __init__(self):
        """Initialize VM service with Azure auth manager."""
        self.auth_manager = get_auth_manager()
    
    def get_compute_client(self, subscription_id: str) -> ComputeManagementClient:
        """Get compute management client."""
        return self.auth_manager.get_compute_client(subscription_id)
    
    @staticmethod
    def get_available_os_images() -> list:
        """Get list of available OS images."""
        return list(OS_IMAGES.keys())
    
    @staticmethod
    def get_available_vm_sizes() -> list:
        """Get list of available VM sizes."""
        return VM_SIZES
    
    def generate_ssh_key_pair(self) -> tuple:
        """Generate SSH key pair for VM access."""
        # In production, use cryptography library for proper key generation
        # This is a placeholder - actual implementation should use paramiko or cryptography
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        
        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=2048
        )
        
        private_key = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption()
        ).decode('utf-8')
        
        public_key = key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH
        ).decode('utf-8')
        
        return private_key, public_key
    
    async def create_vm(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: VMConfig,
        nic_id: str
    ) -> ResourceCreationResponse:
        """Create a Virtual Machine."""
        try:
            compute_client = self.get_compute_client(subscription_id)
            
            # Get OS image reference
            image_ref = OS_IMAGES.get(config.os_image, OS_IMAGES["Ubuntu2204"])
            
            # Build OS profile
            os_profile = OSProfile(
                computer_name=config.name,
                admin_username=config.admin_username,
            )
            
            ssh_config = None
            private_key = None
            
            if "Windows" not in config.os_image:
                # Linux configuration with SSH
                if config.generate_ssh_key:
                    private_key, public_key = self.generate_ssh_key_pair()
                    ssh_config = SshConfiguration(
                        public_keys=[
                            SshPublicKey(
                                path=f"/home/{config.admin_username}/.ssh/authorized_keys",
                                key_data=public_key
                            )
                        ]
                    )
                os_profile.linux_configuration = LinuxConfiguration(
                    disable_password_authentication=config.generate_ssh_key,
                    ssh=ssh_config
                )
            else:
                # Windows configuration
                os_profile.admin_password = secrets.token_urlsafe(16) + "Aa1!"
            
            # VM parameters
            vm_parameters = VirtualMachine(
                location=region,
                hardware_profile=HardwareProfile(vm_size=config.size),
                storage_profile=StorageProfile(
                    image_reference=ImageReference(
                        publisher=image_ref["publisher"],
                        offer=image_ref["offer"],
                        sku=image_ref["sku"],
                        version=image_ref["version"]
                    ),
                    os_disk=OSDisk(
                        name=f"{config.name}-osdisk",
                        caching=CachingTypes.READ_WRITE,
                        create_option=DiskCreateOptionTypes.FROM_IMAGE,
                        managed_disk={"storage_account_type": config.os_disk_type}
                    )
                ),
                os_profile=os_profile,
                network_profile=NetworkProfile(
                    network_interfaces=[
                        NetworkInterfaceReference(id=nic_id, primary=True)
                    ]
                )
            )
            
            # Create VM
            poller = compute_client.virtual_machines.begin_create_or_update(
                resource_group,
                config.name,
                vm_parameters
            )
            
            result = poller.result()
            
            response_details = {
                "vm_size": config.size,
                "os_image": config.os_image,
                "admin_username": config.admin_username,
            }
            
            if private_key:
                response_details["private_key"] = private_key
                response_details["note"] = "Save the private key securely. It won't be shown again."
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.Compute/virtualMachines",
                region=region,
                details=response_details
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    async def delete_vm(
        self,
        subscription_id: str,
        resource_group: str,
        vm_name: str
    ) -> bool:
        """Delete a Virtual Machine."""
        try:
            compute_client = self.get_compute_client(subscription_id)
            poller = compute_client.virtual_machines.begin_delete(
                resource_group,
                vm_name
            )
            poller.result()
            return True
        except Exception:
            return False
    
    def get_vm(
        self,
        subscription_id: str,
        resource_group: str,
        vm_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get VM details."""
        try:
            compute_client = self.get_compute_client(subscription_id)
            vm = compute_client.virtual_machines.get(
                resource_group,
                vm_name,
                expand="instanceView"
            )
            return {
                "name": vm.name,
                "id": vm.id,
                "location": vm.location,
                "vm_size": vm.hardware_profile.vm_size,
                "provisioning_state": vm.provisioning_state
            }
        except Exception:
            return None

