"""Azure Database provisioning service."""
from typing import Optional, Dict, Any, List
import secrets
from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient
from azure.mgmt.rdbms.mysql_flexibleservers import MySQLManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from ..auth.azure_auth import get_auth_manager
from ..models.schemas import ResourceCreationResponse


# PostgreSQL SKUs
POSTGRESQL_SKUS = [
    "Standard_B1ms",
    "Standard_B2s",
    "Standard_D2s_v3",
    "Standard_D4s_v3",
    "Standard_E2s_v3",
]

# PostgreSQL versions
POSTGRESQL_VERSIONS = ["16", "15", "14", "13", "12"]

# MySQL SKUs  
MYSQL_SKUS = [
    "Standard_B1ms",
    "Standard_B2s", 
    "Standard_D2ds_v4",
    "Standard_D4ds_v4",
    "Standard_E2ds_v4",
]

# MySQL versions
MYSQL_VERSIONS = ["8.0.21", "5.7"]

# Azure SQL tiers
SQL_TIERS = [
    "Basic",
    "Standard",
    "Premium",
    "GeneralPurpose",
    "BusinessCritical",
]

# Cosmos DB consistency levels
COSMOS_CONSISTENCY_LEVELS = [
    "Eventual",
    "ConsistentPrefix", 
    "Session",
    "BoundedStaleness",
    "Strong",
]


class DatabaseService:
    """Service for Azure Database operations."""
    
    def __init__(self):
        """Initialize Database service with Azure auth manager."""
        self.auth_manager = get_auth_manager()
    
    def get_postgresql_client(self, subscription_id: str) -> PostgreSQLManagementClient:
        """Get PostgreSQL Flexible Server management client."""
        return PostgreSQLManagementClient(
            self.auth_manager.credential, 
            subscription_id
        )
    
    def get_mysql_client(self, subscription_id: str) -> MySQLManagementClient:
        """Get MySQL Flexible Server management client."""
        return MySQLManagementClient(
            self.auth_manager.credential,
            subscription_id
        )
    
    def get_sql_client(self, subscription_id: str) -> SqlManagementClient:
        """Get Azure SQL management client."""
        return SqlManagementClient(
            self.auth_manager.credential,
            subscription_id
        )
    
    def get_cosmosdb_client(self, subscription_id: str) -> CosmosDBManagementClient:
        """Get Cosmos DB management client."""
        return CosmosDBManagementClient(
            self.auth_manager.credential,
            subscription_id
        )
    
    @staticmethod
    def get_postgresql_skus() -> List[str]:
        """Get available PostgreSQL SKUs."""
        return POSTGRESQL_SKUS
    
    @staticmethod
    def get_postgresql_versions() -> List[str]:
        """Get available PostgreSQL versions."""
        return POSTGRESQL_VERSIONS
    
    @staticmethod
    def get_mysql_skus() -> List[str]:
        """Get available MySQL SKUs."""
        return MYSQL_SKUS
    
    @staticmethod
    def get_mysql_versions() -> List[str]:
        """Get available MySQL versions."""
        return MYSQL_VERSIONS
    
    @staticmethod
    def get_sql_tiers() -> List[str]:
        """Get available Azure SQL tiers."""
        return SQL_TIERS
    
    @staticmethod
    def generate_password() -> str:
        """Generate a secure random password."""
        return secrets.token_urlsafe(16) + "Aa1!"
    
    async def create_postgresql(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: Dict[str, Any]
    ) -> ResourceCreationResponse:
        """Create a PostgreSQL Flexible Server."""
        try:
            client = self.get_postgresql_client(subscription_id)
            
            server_name = config.get("name")
            admin_user = config.get("admin_username", "pgadmin")
            admin_password = config.get("admin_password") or self.generate_password()
            sku = config.get("sku", "Standard_B1ms")
            version = config.get("version", "15")
            storage_gb = config.get("storage_gb", 32)
            
            server_params = {
                "location": region,
                "sku": {
                    "name": sku,
                    "tier": "Burstable" if "B" in sku else "GeneralPurpose"
                },
                "administrator_login": admin_user,
                "administrator_login_password": admin_password,
                "version": version,
                "storage": {
                    "storage_size_gb": storage_gb
                },
                "backup": {
                    "backup_retention_days": 7,
                    "geo_redundant_backup": "Disabled"
                },
                "high_availability": {
                    "mode": "Disabled"
                }
            }
            
            poller = client.servers.begin_create(
                resource_group,
                server_name,
                server_params
            )
            
            result = poller.result()
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.DBforPostgreSQL/flexibleServers",
                region=region,
                details={
                    "fqdn": result.fully_qualified_domain_name,
                    "version": version,
                    "sku": sku,
                    "storage_gb": storage_gb,
                    "admin_username": admin_user,
                    "admin_password": admin_password,
                    "connection_string": f"postgresql://{admin_user}:{admin_password}@{result.fully_qualified_domain_name}:5432/postgres?sslmode=require",
                    "note": "⚠️ Save credentials securely. Password won't be shown again."
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    async def create_mysql(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: Dict[str, Any]
    ) -> ResourceCreationResponse:
        """Create a MySQL Flexible Server."""
        try:
            client = self.get_mysql_client(subscription_id)
            
            server_name = config.get("name")
            admin_user = config.get("admin_username", "mysqladmin")
            admin_password = config.get("admin_password") or self.generate_password()
            sku = config.get("sku", "Standard_B1ms")
            version = config.get("version", "8.0.21")
            storage_gb = config.get("storage_gb", 32)
            
            server_params = {
                "location": region,
                "sku": {
                    "name": sku,
                    "tier": "Burstable" if "B" in sku else "GeneralPurpose"
                },
                "administrator_login": admin_user,
                "administrator_login_password": admin_password,
                "version": version,
                "storage": {
                    "storage_size_gb": storage_gb,
                    "auto_grow": "Enabled"
                },
                "backup": {
                    "backup_retention_days": 7,
                    "geo_redundant_backup": "Disabled"
                }
            }
            
            poller = client.servers.begin_create(
                resource_group,
                server_name,
                server_params
            )
            
            result = poller.result()
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.DBforMySQL/flexibleServers",
                region=region,
                details={
                    "fqdn": result.fully_qualified_domain_name,
                    "version": version,
                    "sku": sku,
                    "storage_gb": storage_gb,
                    "admin_username": admin_user,
                    "admin_password": admin_password,
                    "connection_string": f"mysql://{admin_user}:{admin_password}@{result.fully_qualified_domain_name}:3306",
                    "note": "⚠️ Save credentials securely. Password won't be shown again."
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    async def create_sql_database(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: Dict[str, Any]
    ) -> ResourceCreationResponse:
        """Create an Azure SQL Database with server."""
        try:
            client = self.get_sql_client(subscription_id)
            
            server_name = config.get("server_name", config.get("name") + "-server")
            database_name = config.get("name")
            admin_user = config.get("admin_username", "sqladmin")
            admin_password = config.get("admin_password") or self.generate_password()
            tier = config.get("tier", "Basic")
            
            # Create SQL Server first
            server_params = {
                "location": region,
                "administrator_login": admin_user,
                "administrator_login_password": admin_password,
                "version": "12.0",
                "public_network_access": "Enabled"
            }
            
            server_poller = client.servers.begin_create_or_update(
                resource_group,
                server_name,
                server_params
            )
            
            server_result = server_poller.result()
            
            # Create firewall rule to allow Azure services
            client.firewall_rules.create_or_update(
                resource_group,
                server_name,
                "AllowAzureServices",
                {
                    "start_ip_address": "0.0.0.0",
                    "end_ip_address": "0.0.0.0"
                }
            )
            
            # Create Database
            sku_map = {
                "Basic": {"name": "Basic", "tier": "Basic", "capacity": 5},
                "Standard": {"name": "S0", "tier": "Standard", "capacity": 10},
                "Premium": {"name": "P1", "tier": "Premium", "capacity": 125},
                "GeneralPurpose": {"name": "GP_Gen5_2", "tier": "GeneralPurpose", "family": "Gen5", "capacity": 2},
                "BusinessCritical": {"name": "BC_Gen5_2", "tier": "BusinessCritical", "family": "Gen5", "capacity": 2},
            }
            
            db_sku = sku_map.get(tier, sku_map["Basic"])
            
            db_params = {
                "location": region,
                "sku": db_sku,
                "collation": "SQL_Latin1_General_CP1_CI_AS",
                "max_size_bytes": 2147483648  # 2GB
            }
            
            db_poller = client.databases.begin_create_or_update(
                resource_group,
                server_name,
                database_name,
                db_params
            )
            
            db_result = db_poller.result()
            
            return ResourceCreationResponse(
                success=True,
                resource_id=db_result.id,
                resource_name=db_result.name,
                resource_type="Microsoft.Sql/servers/databases",
                region=region,
                details={
                    "server_name": server_name,
                    "server_fqdn": server_result.fully_qualified_domain_name,
                    "database_name": database_name,
                    "tier": tier,
                    "admin_username": admin_user,
                    "admin_password": admin_password,
                    "connection_string": f"Server=tcp:{server_result.fully_qualified_domain_name},1433;Database={database_name};User ID={admin_user};Password={admin_password};Encrypt=true;Connection Timeout=30;",
                    "note": "⚠️ Save credentials securely. Password won't be shown again."
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    async def create_cosmosdb(
        self,
        subscription_id: str,
        resource_group: str,
        region: str,
        config: Dict[str, Any]
    ) -> ResourceCreationResponse:
        """Create a Cosmos DB account."""
        try:
            client = self.get_cosmosdb_client(subscription_id)
            
            account_name = config.get("name")
            consistency_level = config.get("consistency_level", "Session")
            api_type = config.get("api_type", "SQL")  # SQL, MongoDB, Cassandra, Table, Gremlin
            enable_free_tier = config.get("enable_free_tier", False)
            
            # Build capabilities based on API type
            capabilities = []
            if api_type == "MongoDB":
                capabilities.append({"name": "EnableMongo"})
            elif api_type == "Cassandra":
                capabilities.append({"name": "EnableCassandra"})
            elif api_type == "Table":
                capabilities.append({"name": "EnableTable"})
            elif api_type == "Gremlin":
                capabilities.append({"name": "EnableGremlin"})
            
            account_params = {
                "location": region,
                "locations": [
                    {
                        "location_name": region,
                        "failover_priority": 0,
                        "is_zone_redundant": False
                    }
                ],
                "database_account_offer_type": "Standard",
                "consistency_policy": {
                    "default_consistency_level": consistency_level
                },
                "capabilities": capabilities,
                "enable_free_tier": enable_free_tier
            }
            
            poller = client.database_accounts.begin_create_or_update(
                resource_group,
                account_name,
                account_params
            )
            
            result = poller.result()
            
            # Get connection keys
            keys = client.database_accounts.list_keys(
                resource_group,
                account_name
            )
            
            return ResourceCreationResponse(
                success=True,
                resource_id=result.id,
                resource_name=result.name,
                resource_type="Microsoft.DocumentDB/databaseAccounts",
                region=region,
                details={
                    "document_endpoint": result.document_endpoint,
                    "api_type": api_type,
                    "consistency_level": consistency_level,
                    "primary_key": keys.primary_master_key,
                    "connection_string": f"AccountEndpoint={result.document_endpoint};AccountKey={keys.primary_master_key}",
                    "note": "⚠️ Save the keys securely. They provide full access to your data."
                }
            )
            
        except Exception as e:
            return ResourceCreationResponse(
                success=False,
                error=str(e)
            )
    
    def get_cosmosdb(
        self,
        subscription_id: str,
        resource_group: str,
        account_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get Cosmos DB account details."""
        try:
            client = self.get_cosmosdb_client(subscription_id)
            account = client.database_accounts.get(
                resource_group,
                account_name
            )
            return {
                "name": account.name,
                "id": account.id,
                "location": account.location,
                "document_endpoint": account.document_endpoint,
                "provisioning_state": account.provisioning_state
            }
        except Exception:
            return None

