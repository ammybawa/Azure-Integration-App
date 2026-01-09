"""Azure Pricing Service for cost estimation."""
import httpx
from typing import Dict, Any, List, Optional
from ..models.schemas import CostEstimate, ResourceType


# Approximate pricing data (USD per month)
# These are estimates and should be updated with actual Azure Retail Prices API
PRICING_DATA = {
    "vm_sizes": {
        "Standard_B1s": {"hourly": 0.0104, "monthly": 7.59},
        "Standard_B2s": {"hourly": 0.0416, "monthly": 30.37},
        "Standard_B2ms": {"hourly": 0.0832, "monthly": 60.74},
        "Standard_D2s_v3": {"hourly": 0.096, "monthly": 70.08},
        "Standard_D4s_v3": {"hourly": 0.192, "monthly": 140.16},
        "Standard_D8s_v3": {"hourly": 0.384, "monthly": 280.32},
        "Standard_E2s_v3": {"hourly": 0.126, "monthly": 91.98},
        "Standard_E4s_v3": {"hourly": 0.252, "monthly": 183.96},
        "Standard_F2s_v2": {"hourly": 0.085, "monthly": 62.05},
        "Standard_F4s_v2": {"hourly": 0.169, "monthly": 123.37},
    },
    "storage_skus": {
        "Standard_LRS": {"per_gb": 0.018},
        "Standard_GRS": {"per_gb": 0.036},
        "Standard_RAGRS": {"per_gb": 0.043},
        "Standard_ZRS": {"per_gb": 0.023},
        "Premium_LRS": {"per_gb": 0.15},
        "Premium_ZRS": {"per_gb": 0.188},
    },
    "disk_types": {
        "Standard_LRS": {"per_gb": 0.04},
        "StandardSSD_LRS": {"per_gb": 0.075},
        "Premium_LRS": {"per_gb": 0.132},
    },
    "public_ip": {
        "Standard": {"hourly": 0.005, "monthly": 3.65},
        "Basic": {"hourly": 0.004, "monthly": 2.92},
    },
    "aks_management": {
        "free_tier": 0,
        "standard_tier": 73.0,  # Per cluster per month
    },
    # Database pricing (approximate monthly costs)
    "postgresql_skus": {
        "Standard_B1ms": {"monthly": 12.41, "vcores": 1},
        "Standard_B2s": {"monthly": 24.82, "vcores": 2},
        "Standard_D2s_v3": {"monthly": 98.55, "vcores": 2},
        "Standard_D4s_v3": {"monthly": 197.10, "vcores": 4},
        "Standard_E2s_v3": {"monthly": 130.34, "vcores": 2},
    },
    "mysql_skus": {
        "Standard_B1ms": {"monthly": 12.41, "vcores": 1},
        "Standard_B2s": {"monthly": 24.82, "vcores": 2},
        "Standard_D2ds_v4": {"monthly": 98.55, "vcores": 2},
        "Standard_D4ds_v4": {"monthly": 197.10, "vcores": 4},
        "Standard_E2ds_v4": {"monthly": 130.34, "vcores": 2},
    },
    "sql_tiers": {
        "Basic": {"monthly": 4.99, "dtu": 5},
        "Standard": {"monthly": 14.72, "dtu": 10},
        "Premium": {"monthly": 465.00, "dtu": 125},
        "GeneralPurpose": {"monthly": 330.91, "vcores": 2},
        "BusinessCritical": {"monthly": 661.82, "vcores": 2},
    },
    "cosmosdb": {
        "request_units_per_100": 0.008,  # Per 100 RU/s per hour
        "storage_per_gb": 0.25,  # Per GB per month
    },
    "db_storage_per_gb": 0.115,  # Per GB per month for flexible servers
}

# Hours in a month (730)
HOURS_PER_MONTH = 730


class PricingService:
    """Service for Azure pricing and cost estimation."""
    
    def __init__(self):
        """Initialize pricing service."""
        self.retail_api_url = "https://prices.azure.com/api/retail/prices"
    
    async def get_retail_price(
        self,
        service_name: str,
        arm_region_name: str,
        sku_name: str
    ) -> Optional[float]:
        """
        Get retail price from Azure Retail Prices API.
        This is a best-effort call - returns None if API fails.
        """
        try:
            filter_query = (
                f"serviceName eq '{service_name}' and "
                f"armRegionName eq '{arm_region_name}' and "
                f"skuName eq '{sku_name}' and "
                f"priceType eq 'Consumption'"
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.retail_api_url,
                    params={"$filter": filter_query},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("Items"):
                        return data["Items"][0].get("unitPrice")
            
            return None
            
        except Exception:
            return None
    
    def estimate_vm_cost(
        self,
        vm_size: str,
        os_disk_type: str = "Standard_LRS",
        os_disk_size_gb: int = 30,
        has_public_ip: bool = True
    ) -> CostEstimate:
        """Estimate monthly cost for a Virtual Machine."""
        breakdown = []
        total_cost = 0.0
        
        # VM compute cost
        vm_pricing = PRICING_DATA["vm_sizes"].get(vm_size, {"monthly": 50.0})
        vm_cost = vm_pricing["monthly"]
        breakdown.append({
            "component": "VM Compute",
            "details": vm_size,
            "monthly_cost": vm_cost
        })
        total_cost += vm_cost
        
        # OS Disk cost
        disk_pricing = PRICING_DATA["disk_types"].get(os_disk_type, {"per_gb": 0.04})
        disk_cost = disk_pricing["per_gb"] * os_disk_size_gb
        breakdown.append({
            "component": "OS Disk",
            "details": f"{os_disk_size_gb} GB ({os_disk_type})",
            "monthly_cost": round(disk_cost, 2)
        })
        total_cost += disk_cost
        
        # Public IP cost
        if has_public_ip:
            pip_cost = PRICING_DATA["public_ip"]["Standard"]["monthly"]
            breakdown.append({
                "component": "Public IP",
                "details": "Standard SKU",
                "monthly_cost": pip_cost
            })
            total_cost += pip_cost
        
        return CostEstimate(
            resource_type="Virtual Machine",
            estimated_monthly_cost=round(total_cost, 2),
            breakdown=breakdown
        )
    
    def estimate_storage_cost(
        self,
        sku: str,
        estimated_storage_gb: int = 100
    ) -> CostEstimate:
        """Estimate monthly cost for a Storage Account."""
        breakdown = []
        
        # Storage cost
        storage_pricing = PRICING_DATA["storage_skus"].get(sku, {"per_gb": 0.02})
        storage_cost = storage_pricing["per_gb"] * estimated_storage_gb
        
        breakdown.append({
            "component": "Blob Storage",
            "details": f"{estimated_storage_gb} GB ({sku})",
            "monthly_cost": round(storage_cost, 2)
        })
        
        # Note: Actual costs include operations, bandwidth, etc.
        breakdown.append({
            "component": "Operations & Bandwidth",
            "details": "Usage-based (estimate)",
            "monthly_cost": round(estimated_storage_gb * 0.001, 2)
        })
        
        total_cost = storage_cost + (estimated_storage_gb * 0.001)
        
        return CostEstimate(
            resource_type="Storage Account",
            estimated_monthly_cost=round(total_cost, 2),
            breakdown=breakdown,
            disclaimer="Storage costs vary based on actual usage, operations, and data transfer."
        )
    
    def estimate_vnet_cost(self) -> CostEstimate:
        """Estimate monthly cost for a Virtual Network."""
        # VNets themselves are free, but associated resources have costs
        breakdown = [
            {
                "component": "Virtual Network",
                "details": "No charge for VNet itself",
                "monthly_cost": 0.0
            },
            {
                "component": "VNet Peering (if used)",
                "details": "~$0.01/GB data transfer",
                "monthly_cost": 0.0
            }
        ]
        
        return CostEstimate(
            resource_type="Virtual Network",
            estimated_monthly_cost=0.0,
            breakdown=breakdown,
            disclaimer="VNets are free. Costs apply for peering, VPN gateways, and data transfer."
        )
    
    def estimate_aks_cost(
        self,
        node_count: int,
        node_vm_size: str,
        use_standard_tier: bool = False
    ) -> CostEstimate:
        """Estimate monthly cost for an AKS cluster."""
        breakdown = []
        total_cost = 0.0
        
        # AKS management tier
        if use_standard_tier:
            mgmt_cost = PRICING_DATA["aks_management"]["standard_tier"]
            breakdown.append({
                "component": "AKS Management (Standard)",
                "details": "Uptime SLA included",
                "monthly_cost": mgmt_cost
            })
            total_cost += mgmt_cost
        else:
            breakdown.append({
                "component": "AKS Management (Free)",
                "details": "No uptime SLA",
                "monthly_cost": 0.0
            })
        
        # Node pool VMs
        vm_pricing = PRICING_DATA["vm_sizes"].get(node_vm_size, {"monthly": 70.0})
        nodes_cost = vm_pricing["monthly"] * node_count
        breakdown.append({
            "component": "Node Pool VMs",
            "details": f"{node_count}x {node_vm_size}",
            "monthly_cost": round(nodes_cost, 2)
        })
        total_cost += nodes_cost
        
        # Load Balancer (standard)
        lb_cost = 18.25  # Standard LB base cost
        breakdown.append({
            "component": "Load Balancer",
            "details": "Standard SKU (estimated)",
            "monthly_cost": lb_cost
        })
        total_cost += lb_cost
        
        # OS Disks for nodes
        disk_cost = 0.04 * 128 * node_count  # 128GB per node estimate
        breakdown.append({
            "component": "Node OS Disks",
            "details": f"{node_count}x 128GB Standard",
            "monthly_cost": round(disk_cost, 2)
        })
        total_cost += disk_cost
        
        return CostEstimate(
            resource_type="AKS Cluster",
            estimated_monthly_cost=round(total_cost, 2),
            breakdown=breakdown,
            disclaimer="AKS costs vary based on node scaling, storage, and network usage."
        )
    
    def estimate_postgresql_cost(
        self,
        sku: str = "Standard_B1ms",
        storage_gb: int = 32
    ) -> CostEstimate:
        """Estimate monthly cost for PostgreSQL Flexible Server."""
        breakdown = []
        total_cost = 0.0
        
        # Compute cost
        sku_pricing = PRICING_DATA["postgresql_skus"].get(sku, {"monthly": 12.41})
        compute_cost = sku_pricing["monthly"]
        breakdown.append({
            "component": "Compute",
            "details": sku,
            "monthly_cost": compute_cost
        })
        total_cost += compute_cost
        
        # Storage cost
        storage_cost = PRICING_DATA["db_storage_per_gb"] * storage_gb
        breakdown.append({
            "component": "Storage",
            "details": f"{storage_gb} GB",
            "monthly_cost": round(storage_cost, 2)
        })
        total_cost += storage_cost
        
        # Backup storage (estimate)
        backup_cost = storage_gb * 0.095
        breakdown.append({
            "component": "Backup Storage",
            "details": "Estimated",
            "monthly_cost": round(backup_cost, 2)
        })
        total_cost += backup_cost
        
        return CostEstimate(
            resource_type="PostgreSQL Database",
            estimated_monthly_cost=round(total_cost, 2),
            breakdown=breakdown,
            disclaimer="Costs may vary based on actual compute usage and data transfer."
        )
    
    def estimate_mysql_cost(
        self,
        sku: str = "Standard_B1ms",
        storage_gb: int = 32
    ) -> CostEstimate:
        """Estimate monthly cost for MySQL Flexible Server."""
        breakdown = []
        total_cost = 0.0
        
        # Compute cost
        sku_pricing = PRICING_DATA["mysql_skus"].get(sku, {"monthly": 12.41})
        compute_cost = sku_pricing["monthly"]
        breakdown.append({
            "component": "Compute",
            "details": sku,
            "monthly_cost": compute_cost
        })
        total_cost += compute_cost
        
        # Storage cost
        storage_cost = PRICING_DATA["db_storage_per_gb"] * storage_gb
        breakdown.append({
            "component": "Storage",
            "details": f"{storage_gb} GB",
            "monthly_cost": round(storage_cost, 2)
        })
        total_cost += storage_cost
        
        return CostEstimate(
            resource_type="MySQL Database",
            estimated_monthly_cost=round(total_cost, 2),
            breakdown=breakdown,
            disclaimer="Costs may vary based on actual compute usage and data transfer."
        )
    
    def estimate_sql_database_cost(
        self,
        tier: str = "Basic"
    ) -> CostEstimate:
        """Estimate monthly cost for Azure SQL Database."""
        breakdown = []
        
        tier_pricing = PRICING_DATA["sql_tiers"].get(tier, {"monthly": 4.99})
        db_cost = tier_pricing["monthly"]
        
        breakdown.append({
            "component": "SQL Database",
            "details": f"{tier} tier",
            "monthly_cost": db_cost
        })
        
        return CostEstimate(
            resource_type="Azure SQL Database",
            estimated_monthly_cost=round(db_cost, 2),
            breakdown=breakdown,
            disclaimer="Costs may vary based on DTU/vCore usage and data storage."
        )
    
    def estimate_cosmosdb_cost(
        self,
        enable_free_tier: bool = False,
        estimated_ru_s: int = 400,
        estimated_storage_gb: int = 5
    ) -> CostEstimate:
        """Estimate monthly cost for Cosmos DB."""
        breakdown = []
        total_cost = 0.0
        
        if enable_free_tier:
            breakdown.append({
                "component": "Free Tier Discount",
                "details": "First 400 RU/s + 5 GB free",
                "monthly_cost": 0.0
            })
            # Free tier covers 400 RU/s and 5GB
            ru_cost = max(0, (estimated_ru_s - 400)) * PRICING_DATA["cosmosdb"]["request_units_per_100"] / 100 * 730
            storage_cost = max(0, (estimated_storage_gb - 5)) * PRICING_DATA["cosmosdb"]["storage_per_gb"]
        else:
            ru_cost = estimated_ru_s * PRICING_DATA["cosmosdb"]["request_units_per_100"] / 100 * 730
            storage_cost = estimated_storage_gb * PRICING_DATA["cosmosdb"]["storage_per_gb"]
        
        breakdown.append({
            "component": "Request Units",
            "details": f"{estimated_ru_s} RU/s",
            "monthly_cost": round(ru_cost, 2)
        })
        total_cost += ru_cost
        
        breakdown.append({
            "component": "Storage",
            "details": f"{estimated_storage_gb} GB",
            "monthly_cost": round(storage_cost, 2)
        })
        total_cost += storage_cost
        
        return CostEstimate(
            resource_type="Cosmos DB",
            estimated_monthly_cost=round(total_cost, 2),
            breakdown=breakdown,
            disclaimer="Costs scale with request units and storage. Free tier limited to one account per subscription."
        )
    
    def estimate_resource_cost(
        self,
        resource_type: ResourceType,
        config: Dict[str, Any]
    ) -> CostEstimate:
        """
        Estimate cost for any supported resource type.
        Returns CostEstimate based on resource type and configuration.
        """
        if resource_type == ResourceType.VIRTUAL_MACHINE:
            return self.estimate_vm_cost(
                vm_size=config.get("size", "Standard_B2s"),
                os_disk_type=config.get("os_disk_type", "Standard_LRS"),
                has_public_ip=config.get("create_public_ip", True)
            )
        
        elif resource_type == ResourceType.STORAGE_ACCOUNT:
            return self.estimate_storage_cost(
                sku=config.get("sku", "Standard_LRS"),
                estimated_storage_gb=config.get("estimated_storage_gb", 100)
            )
        
        elif resource_type == ResourceType.VIRTUAL_NETWORK:
            return self.estimate_vnet_cost()
        
        elif resource_type == ResourceType.AKS_CLUSTER:
            return self.estimate_aks_cost(
                node_count=config.get("node_count", 3),
                node_vm_size=config.get("node_vm_size", "Standard_D2s_v3")
            )
        
        elif resource_type == ResourceType.POSTGRESQL:
            return self.estimate_postgresql_cost(
                sku=config.get("sku", "Standard_B1ms"),
                storage_gb=config.get("storage_gb", 32)
            )
        
        elif resource_type == ResourceType.MYSQL:
            return self.estimate_mysql_cost(
                sku=config.get("sku", "Standard_B1ms"),
                storage_gb=config.get("storage_gb", 32)
            )
        
        elif resource_type == ResourceType.SQL_DATABASE:
            return self.estimate_sql_database_cost(
                tier=config.get("tier", "Basic")
            )
        
        elif resource_type == ResourceType.COSMOSDB:
            return self.estimate_cosmosdb_cost(
                enable_free_tier=config.get("enable_free_tier", False)
            )
        
        else:
            return CostEstimate(
                resource_type=resource_type.value,
                estimated_monthly_cost=0.0,
                breakdown=[],
                disclaimer="Cost estimation not available for this resource type."
            )

