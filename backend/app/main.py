"""Main FastAPI application for Azure Chatbot."""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationState,
    ResourceType,
    CostEstimate,
    VMConfig,
    VNetConfig,
    StorageConfig,
    AKSConfig,
    PublicIPConfig,
    NetworkInterfaceConfig,
    PostgreSQLConfig,
    MySQLConfig,
    SQLDatabaseConfig,
    CosmosDBConfig
)
from .chat.conversation import get_conversation_manager
from .chat.flows import ResourceFlows
from .services.vm_service import VMService
from .services.vnet_service import VNetService
from .services.storage_service import StorageService
from .services.aks_service import AKSService
from .services.pricing_service import PricingService
from .services.database_service import DatabaseService
from .terraform.generator import TerraformGenerator
from .auth.azure_auth import get_auth_manager
from .auth.routes import router as auth_router
from .auth.security import get_current_user, get_current_user_optional, TokenData
from .auth.user_store import get_user_store

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Azure Provisioning Chatbot",
    description="An intelligent chatbot that creates Azure resources through conversation",
    version="1.0.0"
)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
allowed_origins = [
    frontend_url,
    "http://localhost:3000",
    "http://localhost:5173",
    "http://application.com",
    "http://application.com:5173",
    "http://application.com:80",
    "https://application.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
conversation_manager = get_conversation_manager()
pricing_service = PricingService()
terraform_generator = TerraformGenerator()

# Include auth routes
app.include_router(auth_router)

# Initialize user store (creates default admin)
user_store = get_user_store()


class SessionResponse(BaseModel):
    """Response for session creation."""
    session_id: str
    message: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Azure Provisioning Chatbot"}


@app.post("/api/session", response_model=SessionResponse)
async def create_session(
    current_user: Optional[TokenData] = Depends(get_current_user_optional)
):
    """Create a new chat session. Authentication optional but recommended."""
    session_id = conversation_manager.create_session()
    
    # Store user info in session if authenticated
    if current_user:
        session = conversation_manager.get_session(session_id)
        session.collected_params["_user_id"] = current_user.user_id
        session.collected_params["_username"] = current_user.username
    
    return SessionResponse(
        session_id=session_id,
        message="Session created. How can I help you create Azure resources today?"
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return response."""
    session = conversation_manager.get_or_create_session(request.session_id)
    user_message = request.message.strip()
    
    # Add user message to history
    conversation_manager.add_message(
        request.session_id,
        "user",
        user_message
    )
    
    # Process based on current state
    response = await process_message(request.session_id, user_message, session.state)
    
    # Add assistant response to history
    conversation_manager.add_message(
        request.session_id,
        "assistant",
        response.message
    )
    
    return response


async def process_message(
    session_id: str,
    user_message: str,
    current_state: ConversationState
) -> ChatResponse:
    """Process user message based on current conversation state."""
    session = conversation_manager.get_session(session_id)
    
    # Handle restart/reset commands
    if user_message.lower() in ["restart", "reset", "start over", "new"]:
        conversation_manager.reset_session(session_id)
        return ChatResponse(
            session_id=session_id,
            message="Session reset. " + ResourceFlows.get_resource_type_prompt(),
            state=ConversationState.RESOURCE_SELECTION,
            options=["Virtual Machine", "Virtual Network", "Storage Account", "AKS Cluster"]
        )
    
    # State machine
    if current_state == ConversationState.INITIAL:
        return handle_initial_state(session_id)
    
    elif current_state == ConversationState.RESOURCE_SELECTION:
        return handle_resource_selection(session_id, user_message)
    
    elif current_state == ConversationState.SUBSCRIPTION:
        return handle_subscription(session_id, user_message)
    
    elif current_state == ConversationState.RESOURCE_GROUP:
        return handle_resource_group(session_id, user_message)
    
    elif current_state == ConversationState.REGION:
        return handle_region(session_id, user_message)
    
    elif current_state == ConversationState.RESOURCE_CONFIG:
        return await handle_resource_config(session_id, user_message)
    
    elif current_state == ConversationState.CONFIRMATION:
        return handle_confirmation(session_id, user_message)
    
    elif current_state == ConversationState.EXECUTION_METHOD:
        return await handle_execution_method(session_id, user_message)
    
    elif current_state == ConversationState.COMPLETED:
        return handle_completed_state(session_id, user_message)
    
    else:
        return ChatResponse(
            session_id=session_id,
            message="I'm not sure how to proceed. Type 'restart' to begin again.",
            state=current_state
        )


def handle_initial_state(session_id: str) -> ChatResponse:
    """Handle initial state - welcome user and ask for resource type."""
    conversation_manager.set_state(session_id, ConversationState.RESOURCE_SELECTION)
    
    welcome = (
        "👋 Welcome to the Azure Provisioning Assistant!\n\n"
        "I can help you create Azure resources through a simple conversation.\n\n"
        + ResourceFlows.get_resource_type_prompt()
    )
    
    return ChatResponse(
        session_id=session_id,
        message=welcome,
        state=ConversationState.RESOURCE_SELECTION,
        options=["Virtual Machine", "Virtual Network", "Storage Account", "AKS Cluster"]
    )


def handle_resource_selection(session_id: str, user_message: str) -> ChatResponse:
    """Handle resource type selection."""
    resource_type = ResourceFlows.parse_resource_selection(user_message)
    
    if not resource_type:
        return ChatResponse(
            session_id=session_id,
            message="I didn't understand that. Please select a resource type:\n\n" + 
                    ResourceFlows.get_resource_type_prompt(),
            state=ConversationState.RESOURCE_SELECTION,
            options=["Virtual Machine", "Virtual Network", "Storage Account", "AKS Cluster", "PostgreSQL", "MySQL", "SQL Database", "Cosmos DB"]
        )
    
    conversation_manager.set_resource_type(session_id, resource_type)
    conversation_manager.set_state(session_id, ConversationState.SUBSCRIPTION)
    
    resource_name = {
        ResourceType.VIRTUAL_MACHINE: "Virtual Machine",
        ResourceType.VIRTUAL_NETWORK: "Virtual Network",
        ResourceType.STORAGE_ACCOUNT: "Storage Account",
        ResourceType.AKS_CLUSTER: "AKS Cluster",
        ResourceType.POSTGRESQL: "PostgreSQL Database",
        ResourceType.MYSQL: "MySQL Database",
        ResourceType.SQL_DATABASE: "Azure SQL Database",
        ResourceType.COSMOSDB: "Cosmos DB"
    }.get(resource_type, "resource")
    
    return ChatResponse(
        session_id=session_id,
        message=f"Great! Let's create a {resource_name}.\n\n"
                f"Please enter your Azure Subscription ID:\n"
                f"(You can find this in the Azure Portal under Subscriptions)",
        state=ConversationState.SUBSCRIPTION
    )


def handle_subscription(session_id: str, user_message: str) -> ChatResponse:
    """Handle subscription ID input."""
    # Basic validation - subscription IDs are GUIDs
    sub_id = user_message.strip()
    
    # Accept 'default' to use environment variable
    if sub_id.lower() == "default":
        sub_id = os.getenv("AZURE_SUBSCRIPTION_ID", "")
        if not sub_id:
            return ChatResponse(
                session_id=session_id,
                message="No default subscription configured. Please enter your Subscription ID:",
                state=ConversationState.SUBSCRIPTION
            )
    
    if len(sub_id) < 32:
        return ChatResponse(
            session_id=session_id,
            message="That doesn't look like a valid Subscription ID. "
                    "Please enter a valid Azure Subscription ID (GUID format) or type 'default' to use the configured subscription:",
            state=ConversationState.SUBSCRIPTION
        )
    
    conversation_manager.set_subscription(session_id, sub_id)
    conversation_manager.set_state(session_id, ConversationState.RESOURCE_GROUP)
    
    return ChatResponse(
        session_id=session_id,
        message="Enter a Resource Group name.\n\n"
                "• To use an existing Resource Group, enter its name\n"
                "• To create a new one, enter: new:<resource-group-name>\n\n"
                "Example: new:my-chatbot-rg",
        state=ConversationState.RESOURCE_GROUP
    )


def handle_resource_group(session_id: str, user_message: str) -> ChatResponse:
    """Handle resource group selection/creation."""
    rg_input = user_message.strip()
    create_new = False
    
    if rg_input.lower().startswith("new:"):
        create_new = True
        rg_name = rg_input[4:].strip()
    else:
        rg_name = rg_input
    
    if not rg_name or len(rg_name) < 1:
        return ChatResponse(
            session_id=session_id,
            message="Please enter a valid Resource Group name:",
            state=ConversationState.RESOURCE_GROUP
        )
    
    conversation_manager.set_resource_group(session_id, rg_name, create_new)
    conversation_manager.set_state(session_id, ConversationState.REGION)
    
    # Show popular regions
    popular_regions = ["eastus", "westus2", "westeurope", "northeurope", "southeastasia", "australiaeast"]
    
    return ChatResponse(
        session_id=session_id,
        message=f"{'Will create new' if create_new else 'Using'} Resource Group: **{rg_name}**\n\n"
                f"Select an Azure region:\n\n" +
                ResourceFlows.format_options_message(popular_regions) +
                "\n\nOr enter any valid Azure region name:",
        state=ConversationState.REGION,
        options=popular_regions
    )


def handle_region(session_id: str, user_message: str) -> ChatResponse:
    """Handle region selection."""
    region = user_message.strip().lower()
    
    available_regions = ResourceFlows.get_available_regions()
    
    # Try to match by index
    if region.isdigit():
        popular_regions = ["eastus", "westus2", "westeurope", "northeurope", "southeastasia", "australiaeast"]
        idx = int(region) - 1
        if 0 <= idx < len(popular_regions):
            region = popular_regions[idx]
    
    if region not in available_regions:
        return ChatResponse(
            session_id=session_id,
            message=f"'{region}' is not a recognized Azure region. "
                    f"Please select from the list or enter a valid region name:",
            state=ConversationState.REGION,
            options=["eastus", "westus2", "westeurope", "northeurope", "southeastasia", "australiaeast"]
        )
    
    conversation_manager.set_region(session_id, region)
    conversation_manager.set_state(session_id, ConversationState.RESOURCE_CONFIG)
    
    # Initialize config question tracking
    session = conversation_manager.get_session(session_id)
    session.collected_params["_question_index"] = 0
    
    # Get first resource-specific question
    return get_next_config_question(session_id)


def get_next_config_question(session_id: str) -> ChatResponse:
    """Get the next configuration question for the resource."""
    session = conversation_manager.get_session(session_id)
    questions = ResourceFlows.get_questions_for_resource(session.resource_type)
    current_index = session.collected_params.get("_question_index", 0)
    
    if current_index >= len(questions):
        # All questions answered, move to confirmation
        return move_to_confirmation(session_id)
    
    question = questions[current_index]
    
    message = question["question"]
    options = question.get("options")
    
    if question.get("default"):
        message += f"\n(Default: {question['default']})"
    
    if options:
        message += "\n\n" + ResourceFlows.format_options_message(options)
    
    return ChatResponse(
        session_id=session_id,
        message=message,
        state=ConversationState.RESOURCE_CONFIG,
        options=options
    )


async def handle_resource_config(session_id: str, user_message: str) -> ChatResponse:
    """Handle resource configuration questions."""
    session = conversation_manager.get_session(session_id)
    questions = ResourceFlows.get_questions_for_resource(session.resource_type)
    current_index = session.collected_params.get("_question_index", 0)
    
    if current_index >= len(questions):
        return move_to_confirmation(session_id)
    
    question = questions[current_index]
    
    # Handle empty input with default
    if not user_message.strip() and question.get("default") is not None:
        user_message = str(question["default"])
    
    # Validate the answer
    is_valid, error, value = ResourceFlows.validate_answer(question, user_message)
    
    if not is_valid:
        return ChatResponse(
            session_id=session_id,
            message=f"❌ {error}\n\nPlease try again:\n\n{question['question']}",
            state=ConversationState.RESOURCE_CONFIG,
            options=question.get("options")
        )
    
    # Store the answer
    session.collected_params[question["key"]] = value
    session.collected_params["_question_index"] = current_index + 1
    
    # Get next question or move to confirmation
    return get_next_config_question(session_id)


def move_to_confirmation(session_id: str) -> ChatResponse:
    """Move to confirmation state with resource summary and cost estimate."""
    session = conversation_manager.get_session(session_id)
    
    # Build config from collected parameters
    config = ResourceFlows.build_config_from_answers(
        session.resource_type,
        session.collected_params
    )
    conversation_manager.set_config(session_id, config)
    conversation_manager.set_state(session_id, ConversationState.CONFIRMATION)
    
    # Get cost estimate
    cost_estimate = pricing_service.estimate_resource_cost(
        session.resource_type,
        config
    )
    
    # Build summary
    summary = conversation_manager.get_resource_summary(session_id)
    
    resource_name = {
        ResourceType.VIRTUAL_MACHINE: "Virtual Machine",
        ResourceType.VIRTUAL_NETWORK: "Virtual Network",
        ResourceType.STORAGE_ACCOUNT: "Storage Account",
        ResourceType.AKS_CLUSTER: "AKS Cluster",
        ResourceType.POSTGRESQL: "PostgreSQL Database",
        ResourceType.MYSQL: "MySQL Database",
        ResourceType.SQL_DATABASE: "Azure SQL Database",
        ResourceType.COSMOSDB: "Cosmos DB"
    }.get(session.resource_type, "Resource")
    
    # Format summary message
    message = f"📋 **{resource_name} Configuration Summary**\n\n"
    message += f"**Subscription:** {session.subscription_id[:8]}...{session.subscription_id[-4:]}\n"
    message += f"**Resource Group:** {session.resource_group}"
    message += " (new)" if session.create_new_rg else ""
    message += f"\n**Region:** {session.region}\n\n"
    
    message += "**Configuration:**\n"
    for key, value in config.items():
        if not key.startswith("_") and key not in ["generate_ssh_key"]:
            display_key = key.replace("_", " ").title()
            if isinstance(value, list):
                message += f"• {display_key}:\n"
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            message += f"  - {k}: {v}\n"
                    else:
                        message += f"  - {item}\n"
            else:
                message += f"• {display_key}: {value}\n"
    
    message += f"\n💰 **Estimated Monthly Cost:** ${cost_estimate.estimated_monthly_cost:.2f}\n"
    
    if cost_estimate.breakdown:
        message += "\nCost Breakdown:\n"
        for item in cost_estimate.breakdown:
            message += f"  • {item['component']}: ${item['monthly_cost']:.2f}\n"
    
    message += f"\n⚠️ {cost_estimate.disclaimer}\n\n"
    message += "**Proceed with resource creation?**\n"
    message += "• Type 'yes' to create via Azure SDK\n"
    message += "• Type 'terraform' to generate Terraform code\n"
    message += "• Type 'no' to cancel\n"
    message += "• Type 'edit' to modify configuration"
    
    return ChatResponse(
        session_id=session_id,
        message=message,
        state=ConversationState.CONFIRMATION,
        options=["yes", "terraform", "no", "edit"],
        resource_summary=summary,
        cost_estimate=cost_estimate.model_dump()
    )


def handle_confirmation(session_id: str, user_message: str) -> ChatResponse:
    """Handle user confirmation of resource creation."""
    choice = user_message.strip().lower()
    
    if choice in ["yes", "y", "create", "proceed"]:
        conversation_manager.set_execution_method(session_id, "azure_sdk")
        conversation_manager.set_state(session_id, ConversationState.EXECUTION_METHOD)
        return ChatResponse(
            session_id=session_id,
            message="Creating resource via Azure SDK...\n\nThis may take a few minutes. Please wait.",
            state=ConversationState.CREATING
        )
    
    elif choice in ["terraform", "tf"]:
        session = conversation_manager.get_session(session_id)
        terraform_code = terraform_generator.generate_terraform(
            session.resource_type,
            session.resource_group,
            session.region,
            session.config,
            session.create_new_rg
        )
        
        conversation_manager.set_state(session_id, ConversationState.COMPLETED)
        
        return ChatResponse(
            session_id=session_id,
            message="Here's your Terraform configuration:\n\n"
                    "```hcl\n" + terraform_code + "\n```\n\n"
                    "**To use this Terraform code:**\n"
                    "1. Save it to a file named `main.tf`\n"
                    "2. Set environment variables: ARM_CLIENT_ID, ARM_CLIENT_SECRET, ARM_TENANT_ID, ARM_SUBSCRIPTION_ID\n"
                    "3. Run `terraform init`\n"
                    "4. Run `terraform plan`\n"
                    "5. Run `terraform apply`\n\n"
                    "Type 'restart' to create another resource.",
            state=ConversationState.COMPLETED,
            terraform_code=terraform_code
        )
    
    elif choice in ["no", "n", "cancel"]:
        conversation_manager.reset_session(session_id)
        return ChatResponse(
            session_id=session_id,
            message="Resource creation cancelled.\n\n" + ResourceFlows.get_resource_type_prompt(),
            state=ConversationState.RESOURCE_SELECTION,
            options=["Virtual Machine", "Virtual Network", "Storage Account", "AKS Cluster"]
        )
    
    elif choice in ["edit", "modify", "change"]:
        # Reset to start of config
        session = conversation_manager.get_session(session_id)
        session.collected_params = {"_question_index": 0}
        conversation_manager.set_state(session_id, ConversationState.RESOURCE_CONFIG)
        return get_next_config_question(session_id)
    
    else:
        return ChatResponse(
            session_id=session_id,
            message="Please respond with:\n"
                    "• 'yes' to create via Azure SDK\n"
                    "• 'terraform' to generate Terraform code\n"
                    "• 'no' to cancel\n"
                    "• 'edit' to modify configuration",
            state=ConversationState.CONFIRMATION,
            options=["yes", "terraform", "no", "edit"]
        )


async def handle_execution_method(session_id: str, user_message: str) -> ChatResponse:
    """Execute resource creation via Azure SDK."""
    session = conversation_manager.get_session(session_id)
    
    try:
        # Create resource group if needed
        if session.create_new_rg:
            auth_manager = get_auth_manager()
            auth_manager.create_resource_group(
                session.resource_group,
                session.region,
                session.subscription_id
            )
        
        # Create the resource based on type
        result = await create_azure_resource(session)
        
        if result.success:
            conversation_manager.set_state(session_id, ConversationState.COMPLETED)
            
            message = f"✅ **Resource Created Successfully!**\n\n"
            message += f"**Resource ID:** {result.resource_id}\n"
            message += f"**Name:** {result.resource_name}\n"
            message += f"**Type:** {result.resource_type}\n"
            message += f"**Region:** {result.region}\n\n"
            
            if result.details:
                message += "**Details:**\n"
                for key, value in result.details.items():
                    if key not in ["private_key", "connection_string"]:
                        display_key = key.replace("_", " ").title()
                        if isinstance(value, dict):
                            message += f"• {display_key}:\n"
                            for k, v in value.items():
                                message += f"  - {k}: {v}\n"
                        else:
                            message += f"• {display_key}: {value}\n"
                
                # Handle sensitive data
                if "private_key" in result.details:
                    message += "\n⚠️ **SSH Private Key generated.** Save it securely - it won't be shown again.\n"
                if "connection_string" in result.details:
                    message += "\n⚠️ **Connection string generated.** Store it securely.\n"
            
            message += "\nType 'restart' to create another resource."
            
            return ChatResponse(
                session_id=session_id,
                message=message,
                state=ConversationState.COMPLETED,
                created_resource=result.model_dump()
            )
        else:
            conversation_manager.set_state(session_id, ConversationState.ERROR)
            return ChatResponse(
                session_id=session_id,
                message=f"❌ **Resource Creation Failed**\n\nError: {result.error}\n\n"
                        f"Type 'restart' to try again or 'terraform' to get Terraform code instead.",
                state=ConversationState.ERROR,
                error=result.error
            )
    
    except Exception as e:
        conversation_manager.set_state(session_id, ConversationState.ERROR)
        return ChatResponse(
            session_id=session_id,
            message=f"❌ **An error occurred**\n\nError: {str(e)}\n\n"
                    f"Type 'restart' to try again.",
            state=ConversationState.ERROR,
            error=str(e)
        )


async def create_azure_resource(session):
    """Create Azure resource based on session configuration."""
    if session.resource_type == ResourceType.VIRTUAL_MACHINE:
        return await create_vm(session)
    elif session.resource_type == ResourceType.VIRTUAL_NETWORK:
        return await create_vnet(session)
    elif session.resource_type == ResourceType.STORAGE_ACCOUNT:
        return await create_storage(session)
    elif session.resource_type == ResourceType.AKS_CLUSTER:
        return await create_aks(session)
    elif session.resource_type == ResourceType.POSTGRESQL:
        return await create_postgresql(session)
    elif session.resource_type == ResourceType.MYSQL:
        return await create_mysql(session)
    elif session.resource_type == ResourceType.SQL_DATABASE:
        return await create_sql_database(session)
    elif session.resource_type == ResourceType.COSMOSDB:
        return await create_cosmosdb(session)
    else:
        from .models.schemas import ResourceCreationResponse
        return ResourceCreationResponse(
            success=False,
            error="Unsupported resource type"
        )


async def create_vm(session):
    """Create a Virtual Machine with all required networking."""
    from .models.schemas import ResourceCreationResponse
    
    vnet_service = VNetService()
    vm_service = VMService()
    
    config = session.config
    vm_name = config["name"]
    
    try:
        # Create VNet
        vnet_config = VNetConfig(
            name=f"{vm_name}-vnet",
            address_space="10.0.0.0/16",
            subnets=[{"name": "default", "address_prefix": "10.0.1.0/24"}]
        )
        vnet_result = await vnet_service.create_vnet(
            session.subscription_id,
            session.resource_group,
            session.region,
            vnet_config
        )
        
        if not vnet_result.success:
            return vnet_result
        
        # Create Public IP if requested
        pip_name = None
        if config.get("create_public_ip", True):
            pip_config = PublicIPConfig(name=f"{vm_name}-pip")
            pip_result = await vnet_service.create_public_ip(
                session.subscription_id,
                session.resource_group,
                session.region,
                pip_config
            )
            if pip_result.success:
                pip_name = pip_config.name
        
        # Create Network Interface
        nic_config = NetworkInterfaceConfig(
            name=f"{vm_name}-nic",
            vnet_name=vnet_config.name,
            subnet_name="default",
            public_ip_name=pip_name
        )
        nic_result = await vnet_service.create_network_interface(
            session.subscription_id,
            session.resource_group,
            session.region,
            nic_config
        )
        
        if not nic_result.success:
            return nic_result
        
        # Create VM
        vm_config = VMConfig(**config)
        vm_result = await vm_service.create_vm(
            session.subscription_id,
            session.resource_group,
            session.region,
            vm_config,
            nic_result.resource_id
        )
        
        return vm_result
        
    except Exception as e:
        return ResourceCreationResponse(
            success=False,
            error=str(e)
        )


async def create_vnet(session):
    """Create a Virtual Network."""
    vnet_service = VNetService()
    config = session.config
    
    vnet_config = VNetConfig(**config)
    return await vnet_service.create_vnet(
        session.subscription_id,
        session.resource_group,
        session.region,
        vnet_config
    )


async def create_storage(session):
    """Create a Storage Account."""
    storage_service = StorageService()
    config = session.config
    
    storage_config = StorageConfig(**config)
    return await storage_service.create_storage_account(
        session.subscription_id,
        session.resource_group,
        session.region,
        storage_config
    )


async def create_aks(session):
    """Create an AKS Cluster."""
    aks_service = AKSService()
    config = session.config
    
    aks_config = AKSConfig(**config)
    return await aks_service.create_aks_cluster(
        session.subscription_id,
        session.resource_group,
        session.region,
        aks_config
    )


async def create_postgresql(session):
    """Create a PostgreSQL Flexible Server."""
    db_service = DatabaseService()
    return await db_service.create_postgresql(
        session.subscription_id,
        session.resource_group,
        session.region,
        session.config
    )


async def create_mysql(session):
    """Create a MySQL Flexible Server."""
    db_service = DatabaseService()
    return await db_service.create_mysql(
        session.subscription_id,
        session.resource_group,
        session.region,
        session.config
    )


async def create_sql_database(session):
    """Create an Azure SQL Database."""
    db_service = DatabaseService()
    return await db_service.create_sql_database(
        session.subscription_id,
        session.resource_group,
        session.region,
        session.config
    )


async def create_cosmosdb(session):
    """Create a Cosmos DB account."""
    db_service = DatabaseService()
    return await db_service.create_cosmosdb(
        session.subscription_id,
        session.resource_group,
        session.region,
        session.config
    )


def handle_completed_state(session_id: str, user_message: str) -> ChatResponse:
    """Handle messages after resource creation is complete."""
    if user_message.lower() in ["restart", "new", "another", "reset"]:
        conversation_manager.reset_session(session_id)
        return ChatResponse(
            session_id=session_id,
            message="Let's create another resource!\n\n" + ResourceFlows.get_resource_type_prompt(),
            state=ConversationState.RESOURCE_SELECTION,
            options=["Virtual Machine", "Virtual Network", "Storage Account", "AKS Cluster"]
        )
    
    return ChatResponse(
        session_id=session_id,
        message="Resource creation complete! Type 'restart' to create another resource.",
        state=ConversationState.COMPLETED
    )


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    if conversation_manager.delete_session(session_id):
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Try to validate Azure credentials
        auth_manager = get_auth_manager()
        credentials_valid = auth_manager.validate_credentials()
    except Exception:
        credentials_valid = False
    
    return {
        "status": "healthy",
        "azure_credentials": "configured" if credentials_valid else "not configured or invalid"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run("app.main:app", host=host, port=port, reload=debug)

