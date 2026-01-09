"""Terraform code generator for Azure resources."""
from typing import Dict, Any
from ..models.schemas import ResourceType


class TerraformGenerator:
    """Generates Terraform configuration files for Azure resources."""
    
    def __init__(self):
        """Initialize Terraform generator."""
        self.provider_block = '''terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  
  # Authentication using Service Principal
  # Set these via environment variables:
  # ARM_CLIENT_ID, ARM_CLIENT_SECRET, ARM_TENANT_ID, ARM_SUBSCRIPTION_ID
}
'''
    
    def generate_resource_group(
        self,
        name: str,
        region: str
    ) -> str:
        """Generate Terraform for resource group."""
        return f'''
resource "azurerm_resource_group" "rg" {{
  name     = "{name}"
  location = "{region}"

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}
'''
    
    def generate_vm(
        self,
        config: Dict[str, Any],
        resource_group_ref: str = "azurerm_resource_group.rg.name",
        region_ref: str = "azurerm_resource_group.rg.location"
    ) -> str:
        """Generate Terraform for Virtual Machine with networking."""
        name = config.get("name", "myvm")
        size = config.get("size", "Standard_B2s")
        os_image = config.get("os_image", "Ubuntu2204")
        admin_username = config.get("admin_username", "azureuser")
        os_disk_type = config.get("os_disk_type", "Standard_LRS")
        create_public_ip = config.get("create_public_ip", True)
        
        # Map OS image to Terraform format
        os_images = {
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
            "RHEL8": {
                "publisher": "RedHat",
                "offer": "RHEL",
                "sku": "8-lvm-gen2",
                "version": "latest"
            }
        }
        
        image = os_images.get(os_image, os_images["Ubuntu2204"])
        is_linux = "Windows" not in os_image
        
        terraform = f'''
# Virtual Network for VM
resource "azurerm_virtual_network" "vnet_{name}" {{
  name                = "{name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = {region_ref}
  resource_group_name = {resource_group_ref}
}}

# Subnet
resource "azurerm_subnet" "subnet_{name}" {{
  name                 = "default"
  resource_group_name  = {resource_group_ref}
  virtual_network_name = azurerm_virtual_network.vnet_{name}.name
  address_prefixes     = ["10.0.1.0/24"]
}}
'''
        
        if create_public_ip:
            terraform += f'''
# Public IP
resource "azurerm_public_ip" "pip_{name}" {{
  name                = "{name}-pip"
  location            = {region_ref}
  resource_group_name = {resource_group_ref}
  allocation_method   = "Static"
  sku                 = "Standard"
}}
'''
        
        # Network Security Group
        terraform += f'''
# Network Security Group
resource "azurerm_network_security_group" "nsg_{name}" {{
  name                = "{name}-nsg"
  location            = {region_ref}
  resource_group_name = {resource_group_ref}

  security_rule {{
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "{"22" if is_linux else "3389"}"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }}
}}
'''
        
        # Network Interface
        pip_config = f'''
    public_ip_address_id = azurerm_public_ip.pip_{name}.id''' if create_public_ip else ""
        
        terraform += f'''
# Network Interface
resource "azurerm_network_interface" "nic_{name}" {{
  name                = "{name}-nic"
  location            = {region_ref}
  resource_group_name = {resource_group_ref}

  ip_configuration {{
    name                          = "internal"
    subnet_id                     = azurerm_subnet.subnet_{name}.id
    private_ip_address_allocation = "Dynamic"{pip_config}
  }}
}}

# NIC-NSG Association
resource "azurerm_network_interface_security_group_association" "nsg_assoc_{name}" {{
  network_interface_id      = azurerm_network_interface.nic_{name}.id
  network_security_group_id = azurerm_network_security_group.nsg_{name}.id
}}
'''
        
        # Generate SSH key resource for Linux
        if is_linux:
            terraform += f'''
# SSH Key
resource "tls_private_key" "ssh_{name}" {{
  algorithm = "RSA"
  rsa_bits  = 4096
}}

# Virtual Machine
resource "azurerm_linux_virtual_machine" "vm_{name}" {{
  name                = "{name}"
  resource_group_name = {resource_group_ref}
  location            = {region_ref}
  size                = "{size}"
  admin_username      = "{admin_username}"
  
  network_interface_ids = [
    azurerm_network_interface.nic_{name}.id,
  ]

  admin_ssh_key {{
    username   = "{admin_username}"
    public_key = tls_private_key.ssh_{name}.public_key_openssh
  }}

  os_disk {{
    caching              = "ReadWrite"
    storage_account_type = "{os_disk_type}"
    name                 = "{name}-osdisk"
  }}

  source_image_reference {{
    publisher = "{image["publisher"]}"
    offer     = "{image["offer"]}"
    sku       = "{image["sku"]}"
    version   = "{image["version"]}"
  }}

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}

# Output the private key (save securely!)
output "private_key_{name}" {{
  value     = tls_private_key.ssh_{name}.private_key_pem
  sensitive = true
}}
'''
        else:
            terraform += f'''
# Windows Virtual Machine
resource "azurerm_windows_virtual_machine" "vm_{name}" {{
  name                = "{name}"
  resource_group_name = {resource_group_ref}
  location            = {region_ref}
  size                = "{size}"
  admin_username      = "{admin_username}"
  admin_password      = "ChangeMe123!" # Change this!
  
  network_interface_ids = [
    azurerm_network_interface.nic_{name}.id,
  ]

  os_disk {{
    caching              = "ReadWrite"
    storage_account_type = "{os_disk_type}"
    name                 = "{name}-osdisk"
  }}

  source_image_reference {{
    publisher = "{image["publisher"]}"
    offer     = "{image["offer"]}"
    sku       = "{image["sku"]}"
    version   = "{image["version"]}"
  }}

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}
'''
        
        if create_public_ip:
            terraform += f'''
output "public_ip_{name}" {{
  value = azurerm_public_ip.pip_{name}.ip_address
}}
'''
        
        return terraform
    
    def generate_vnet(
        self,
        config: Dict[str, Any],
        resource_group_ref: str = "azurerm_resource_group.rg.name",
        region_ref: str = "azurerm_resource_group.rg.location"
    ) -> str:
        """Generate Terraform for Virtual Network."""
        name = config.get("name", "myvnet")
        address_space = config.get("address_space", "10.0.0.0/16")
        subnets = config.get("subnets", [{"name": "default", "address_prefix": "10.0.0.0/24"}])
        
        terraform = f'''
# Virtual Network
resource "azurerm_virtual_network" "vnet" {{
  name                = "{name}"
  address_space       = ["{address_space}"]
  location            = {region_ref}
  resource_group_name = {resource_group_ref}

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}
'''
        
        for i, subnet in enumerate(subnets):
            subnet_name = subnet.get("name", f"subnet{i}")
            subnet_prefix = subnet.get("address_prefix", f"10.0.{i}.0/24")
            terraform += f'''
resource "azurerm_subnet" "subnet_{subnet_name}" {{
  name                 = "{subnet_name}"
  resource_group_name  = {resource_group_ref}
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["{subnet_prefix}"]
}}
'''
        
        terraform += f'''
output "vnet_id" {{
  value = azurerm_virtual_network.vnet.id
}}
'''
        
        return terraform
    
    def generate_storage(
        self,
        config: Dict[str, Any],
        resource_group_ref: str = "azurerm_resource_group.rg.name",
        region_ref: str = "azurerm_resource_group.rg.location"
    ) -> str:
        """Generate Terraform for Storage Account."""
        name = config.get("name", "mystorageaccount")
        sku = config.get("sku", "Standard_LRS")
        kind = config.get("kind", "StorageV2")
        access_tier = config.get("access_tier", "Hot")
        
        # Map SKU names
        sku_mapping = {
            "Standard_LRS": "Standard",
            "Standard_GRS": "Standard",
            "Standard_RAGRS": "Standard",
            "Standard_ZRS": "Standard",
            "Premium_LRS": "Premium",
            "Premium_ZRS": "Premium"
        }
        
        replication_mapping = {
            "Standard_LRS": "LRS",
            "Standard_GRS": "GRS",
            "Standard_RAGRS": "RAGRS",
            "Standard_ZRS": "ZRS",
            "Premium_LRS": "LRS",
            "Premium_ZRS": "ZRS"
        }
        
        account_tier = sku_mapping.get(sku, "Standard")
        replication = replication_mapping.get(sku, "LRS")
        
        return f'''
# Storage Account
resource "azurerm_storage_account" "storage" {{
  name                     = "{name}"
  resource_group_name      = {resource_group_ref}
  location                 = {region_ref}
  account_tier             = "{account_tier}"
  account_replication_type = "{replication}"
  account_kind             = "{kind}"
  access_tier              = "{access_tier}"

  enable_https_traffic_only = true
  min_tls_version          = "TLS1_2"

  blob_properties {{
    versioning_enabled = true
  }}

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}

output "storage_account_name" {{
  value = azurerm_storage_account.storage.name
}}

output "storage_account_primary_connection_string" {{
  value     = azurerm_storage_account.storage.primary_connection_string
  sensitive = true
}}

output "storage_account_primary_blob_endpoint" {{
  value = azurerm_storage_account.storage.primary_blob_endpoint
}}
'''
    
    def generate_aks(
        self,
        config: Dict[str, Any],
        resource_group_ref: str = "azurerm_resource_group.rg.name",
        region_ref: str = "azurerm_resource_group.rg.location"
    ) -> str:
        """Generate Terraform for AKS Cluster."""
        name = config.get("name", "myakscluster")
        dns_prefix = config.get("dns_prefix", name)
        node_count = config.get("node_count", 3)
        node_vm_size = config.get("node_vm_size", "Standard_D2s_v3")
        kubernetes_version = config.get("kubernetes_version", "1.28")
        network_plugin = config.get("network_plugin", "azure")
        enable_rbac = config.get("enable_rbac", True)
        
        return f'''
# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {{
  name                = "{name}"
  location            = {region_ref}
  resource_group_name = {resource_group_ref}
  dns_prefix          = "{dns_prefix}"
  kubernetes_version  = "{kubernetes_version}"

  default_node_pool {{
    name                = "nodepool1"
    node_count          = {node_count}
    vm_size             = "{node_vm_size}"
    os_disk_size_gb     = 128
    type                = "VirtualMachineScaleSets"
    enable_auto_scaling = false
  }}

  identity {{
    type = "SystemAssigned"
  }}

  network_profile {{
    network_plugin    = "{network_plugin}"
    load_balancer_sku = "standard"
  }}

  role_based_access_control_enabled = {str(enable_rbac).lower()}

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}

output "aks_cluster_name" {{
  value = azurerm_kubernetes_cluster.aks.name
}}

output "aks_cluster_id" {{
  value = azurerm_kubernetes_cluster.aks.id
}}

output "kube_config" {{
  value     = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive = true
}}

output "aks_fqdn" {{
  value = azurerm_kubernetes_cluster.aks.fqdn
}}
'''
    
    def generate_postgresql(
        self,
        config: Dict[str, Any],
        resource_group_ref: str = "azurerm_resource_group.rg.name",
        region_ref: str = "azurerm_resource_group.rg.location"
    ) -> str:
        """Generate Terraform for PostgreSQL Flexible Server."""
        name = config.get("name")
        version = config.get("version", "15")
        sku = config.get("sku", "Standard_B1ms")
        storage_gb = config.get("storage_gb", 32)
        admin_username = config.get("admin_username", "pgadmin")
        
        tier = "Burstable" if "B" in sku else "GeneralPurpose"
        
        return f'''
# Random password for PostgreSQL
resource "random_password" "pg_password" {{
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]:?"
}}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "postgres" {{
  name                   = "{name}"
  resource_group_name    = {resource_group_ref}
  location               = {region_ref}
  version                = "{version}"
  administrator_login    = "{admin_username}"
  administrator_password = random_password.pg_password.result
  zone                   = "1"

  storage_mb = {storage_gb * 1024}

  sku_name = "{sku}"

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}

# Firewall rule to allow Azure services
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {{
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.postgres.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}}

output "postgresql_fqdn" {{
  value = azurerm_postgresql_flexible_server.postgres.fqdn
}}

output "postgresql_admin_username" {{
  value = azurerm_postgresql_flexible_server.postgres.administrator_login
}}

output "postgresql_admin_password" {{
  value     = random_password.pg_password.result
  sensitive = true
}}
'''

    def generate_mysql(
        self,
        config: Dict[str, Any],
        resource_group_ref: str = "azurerm_resource_group.rg.name",
        region_ref: str = "azurerm_resource_group.rg.location"
    ) -> str:
        """Generate Terraform for MySQL Flexible Server."""
        name = config.get("name")
        version = config.get("version", "8.0.21")
        sku = config.get("sku", "Standard_B1ms")
        storage_gb = config.get("storage_gb", 32)
        admin_username = config.get("admin_username", "mysqladmin")
        
        tier = "Burstable" if "B" in sku else "GeneralPurpose"
        
        return f'''
# Random password for MySQL
resource "random_password" "mysql_password" {{
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]:?"
}}

# MySQL Flexible Server
resource "azurerm_mysql_flexible_server" "mysql" {{
  name                   = "{name}"
  resource_group_name    = {resource_group_ref}
  location               = {region_ref}
  version                = "{version}"
  administrator_login    = "{admin_username}"
  administrator_password = random_password.mysql_password.result
  zone                   = "1"

  storage {{
    size_gb = {storage_gb}
  }}

  sku_name = "{sku}"

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}

# Firewall rule to allow Azure services
resource "azurerm_mysql_flexible_server_firewall_rule" "allow_azure" {{
  name                = "AllowAzureServices"
  resource_group_name = {resource_group_ref}
  server_name         = azurerm_mysql_flexible_server.mysql.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
}}

output "mysql_fqdn" {{
  value = azurerm_mysql_flexible_server.mysql.fqdn
}}

output "mysql_admin_username" {{
  value = azurerm_mysql_flexible_server.mysql.administrator_login
}}

output "mysql_admin_password" {{
  value     = random_password.mysql_password.result
  sensitive = true
}}
'''

    def generate_sql_database(
        self,
        config: Dict[str, Any],
        resource_group_ref: str = "azurerm_resource_group.rg.name",
        region_ref: str = "azurerm_resource_group.rg.location"
    ) -> str:
        """Generate Terraform for Azure SQL Database."""
        database_name = config.get("name")
        server_name = config.get("server_name", f"{database_name}-server")
        tier = config.get("tier", "Basic")
        admin_username = config.get("admin_username", "sqladmin")
        
        return f'''
# Random password for SQL Server
resource "random_password" "sql_password" {{
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]:?"
}}

# Azure SQL Server
resource "azurerm_mssql_server" "sql_server" {{
  name                         = "{server_name}"
  resource_group_name          = {resource_group_ref}
  location                     = {region_ref}
  version                      = "12.0"
  administrator_login          = "{admin_username}"
  administrator_login_password = random_password.sql_password.result

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}

# Firewall rule to allow Azure services
resource "azurerm_mssql_firewall_rule" "allow_azure" {{
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.sql_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}}

# Azure SQL Database
resource "azurerm_mssql_database" "db" {{
  name         = "{database_name}"
  server_id    = azurerm_mssql_server.sql_server.id
  collation    = "SQL_Latin1_General_CP1_CI_AS"
  license_type = "LicenseIncluded"
  sku_name     = "{tier}"

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}

output "sql_server_fqdn" {{
  value = azurerm_mssql_server.sql_server.fully_qualified_domain_name
}}

output "sql_database_name" {{
  value = azurerm_mssql_database.db.name
}}

output "sql_admin_username" {{
  value = azurerm_mssql_server.sql_server.administrator_login
}}

output "sql_admin_password" {{
  value     = random_password.sql_password.result
  sensitive = true
}}
'''

    def generate_cosmosdb(
        self,
        config: Dict[str, Any],
        resource_group_ref: str = "azurerm_resource_group.rg.name",
        region_ref: str = "azurerm_resource_group.rg.location"
    ) -> str:
        """Generate Terraform for Cosmos DB."""
        name = config.get("name")
        api_type = config.get("api_type", "SQL")
        consistency_level = config.get("consistency_level", "Session")
        enable_free_tier = config.get("enable_free_tier", False)
        
        # Map API type to capabilities
        capabilities = ""
        if api_type == "MongoDB":
            capabilities = '''
  capabilities {
    name = "EnableMongo"
  }'''
        elif api_type == "Cassandra":
            capabilities = '''
  capabilities {
    name = "EnableCassandra"
  }'''
        elif api_type == "Table":
            capabilities = '''
  capabilities {
    name = "EnableTable"
  }'''
        elif api_type == "Gremlin":
            capabilities = '''
  capabilities {
    name = "EnableGremlin"
  }'''
        
        return f'''
# Cosmos DB Account
resource "azurerm_cosmosdb_account" "cosmos" {{
  name                = "{name}"
  location            = {region_ref}
  resource_group_name = {resource_group_ref}
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  enable_free_tier    = {str(enable_free_tier).lower()}

  consistency_policy {{
    consistency_level = "{consistency_level}"
  }}

  geo_location {{
    location          = {region_ref}
    failover_priority = 0
  }}
{capabilities}

  tags = {{
    Environment = "Production"
    ManagedBy   = "Terraform"
  }}
}}

output "cosmosdb_endpoint" {{
  value = azurerm_cosmosdb_account.cosmos.endpoint
}}

output "cosmosdb_primary_key" {{
  value     = azurerm_cosmosdb_account.cosmos.primary_key
  sensitive = true
}}

output "cosmosdb_connection_string" {{
  value     = azurerm_cosmosdb_account.cosmos.primary_sql_connection_string
  sensitive = true
}}
'''

    def generate_terraform(
        self,
        resource_type: ResourceType,
        resource_group: str,
        region: str,
        config: Dict[str, Any],
        create_new_rg: bool = True
    ) -> str:
        """Generate complete Terraform configuration for a resource."""
        terraform = self.provider_block
        
        # Add TLS provider if VM (for SSH key generation)
        if resource_type == ResourceType.VIRTUAL_MACHINE:
            terraform = terraform.replace(
                'required_providers {',
                '''required_providers {
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }'''
            )
        
        # Add random provider for database passwords
        if resource_type in [ResourceType.POSTGRESQL, ResourceType.MYSQL, ResourceType.SQL_DATABASE]:
            terraform = terraform.replace(
                'required_providers {',
                '''required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }'''
            )
        
        if create_new_rg:
            terraform += self.generate_resource_group(resource_group, region)
            rg_ref = "azurerm_resource_group.rg.name"
            location_ref = "azurerm_resource_group.rg.location"
        else:
            terraform += f'''
# Using existing resource group
data "azurerm_resource_group" "rg" {{
  name = "{resource_group}"
}}
'''
            rg_ref = "data.azurerm_resource_group.rg.name"
            location_ref = "data.azurerm_resource_group.rg.location"
        
        # Generate resource-specific Terraform
        if resource_type == ResourceType.VIRTUAL_MACHINE:
            terraform += self.generate_vm(config, rg_ref, location_ref)
        elif resource_type == ResourceType.VIRTUAL_NETWORK:
            terraform += self.generate_vnet(config, rg_ref, location_ref)
        elif resource_type == ResourceType.STORAGE_ACCOUNT:
            terraform += self.generate_storage(config, rg_ref, location_ref)
        elif resource_type == ResourceType.AKS_CLUSTER:
            terraform += self.generate_aks(config, rg_ref, location_ref)
        elif resource_type == ResourceType.POSTGRESQL:
            terraform += self.generate_postgresql(config, rg_ref, location_ref)
        elif resource_type == ResourceType.MYSQL:
            terraform += self.generate_mysql(config, rg_ref, location_ref)
        elif resource_type == ResourceType.SQL_DATABASE:
            terraform += self.generate_sql_database(config, rg_ref, location_ref)
        elif resource_type == ResourceType.COSMOSDB:
            terraform += self.generate_cosmosdb(config, rg_ref, location_ref)
        
        return terraform

