# Azure Provisioning Chatbot 🤖☁️

An intelligent chatbot application that creates Azure resources through a conversational interface. Simply tell the bot what you want to create, and it will guide you through the configuration and create the resources automatically.

![Azure Chatbot](https://img.shields.io/badge/Azure-Provisioning-0078D4?style=for-the-badge&logo=microsoft-azure&logoColor=white)
![Python](https://img.shields.io/badge/Python-FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)

## ✨ Features

- **Conversational Interface**: Create Azure resources through natural chat interactions
- **Multiple Resource Types**: Support for VMs, Virtual Networks, Storage Accounts, and AKS Clusters
- **Cost Estimation**: Get estimated monthly costs before creating resources
- **Terraform Generation**: Option to generate Terraform code instead of direct creation
- **Confirmation Step**: Review configuration and costs before proceeding
- **Beautiful UI**: Modern, responsive chatbot interface with dark theme

## 🏗️ Supported Azure Resources

| Resource | Description |
|----------|-------------|
| **Virtual Machine** | Create Linux/Windows VMs with configurable sizes, OS images, and networking |
| **Virtual Network** | Create VNets with custom address spaces and subnets |
| **Storage Account** | Create storage accounts with various redundancy options |
| **AKS Cluster** | Deploy Kubernetes clusters with configurable node pools |
| **PostgreSQL Database** | Deploy PostgreSQL Flexible Servers with configurable compute and storage |
| **MySQL Database** | Deploy MySQL Flexible Servers with configurable compute and storage |
| **Azure SQL Database** | Create Azure SQL Database with SQL Server |
| **Cosmos DB** | Create Cosmos DB accounts (SQL, MongoDB, Cassandra, Table, Gremlin APIs) |

## 📁 Project Structure

```
Azure-Integration-App/
├── backend/                      # FastAPI Backend
│   ├── app/
│   │   ├── auth/                 # Azure authentication
│   │   │   └── azure_auth.py     # Service Principal auth
│   │   ├── chat/                 # Conversation management
│   │   │   ├── conversation.py   # Session state management
│   │   │   └── flows.py          # Resource creation flows
│   │   ├── models/               # Pydantic schemas
│   │   │   └── schemas.py        # Request/response models
│   │   ├── services/             # Azure resource services
│   │   │   ├── vm_service.py     # Virtual Machine operations
│   │   │   ├── vnet_service.py   # Virtual Network operations
│   │   │   ├── storage_service.py# Storage Account operations
│   │   │   ├── aks_service.py    # AKS Cluster operations
│   │   │   └── pricing_service.py# Cost estimation
│   │   ├── terraform/            # Terraform generation
│   │   │   └── generator.py      # HCL code generator
│   │   └── main.py               # FastAPI application
│   ├── requirements.txt          # Python dependencies
│   └── env.example               # Environment variables template
├── frontend/                     # React Frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── ChatMessage.jsx   # Chat message bubble
│   │   │   ├── ChatInput.jsx     # Message input field
│   │   │   ├── Header.jsx        # App header
│   │   │   └── ResourceSummary.jsx# Resource/cost summary card
│   │   ├── App.jsx               # Main application
│   │   ├── main.jsx              # Entry point
│   │   └── index.css             # Global styles
│   ├── package.json              # Node dependencies
│   └── vite.config.js            # Vite configuration
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Azure subscription with Service Principal credentials

### 1. Azure Service Principal Setup

Create a Service Principal with Contributor access:

```bash
# Login to Azure
az login

# Create Service Principal
az ad sp create-for-rbac --name "azure-chatbot-sp" --role Contributor \
    --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID>
```

Save the output - you'll need:
- `appId` → `AZURE_CLIENT_ID`
- `password` → `AZURE_CLIENT_SECRET`
- `tenant` → `AZURE_TENANT_ID`

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
copy env.example .env    # Windows
# cp env.example .env    # Linux/Mac

# Edit .env with your Azure credentials
```

Configure your `.env` file:

```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
FRONTEND_URL=http://localhost:5173
```

Start the backend:

```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application

Open your browser and navigate to: **http://localhost:5173**

## 💬 Usage Guide

### Creating a Virtual Machine

1. Start a conversation and select "Virtual Machine"
2. Enter your Azure Subscription ID (or type `default` to use configured one)
3. Enter a Resource Group name (prefix with `new:` to create new)
4. Select an Azure region
5. Configure VM options:
   - Name
   - Size (e.g., Standard_B2s)
   - OS Image (Ubuntu, Windows Server, RHEL, etc.)
   - Disk type
   - Admin username
   - Public IP option
6. Review the cost estimate
7. Choose:
   - `yes` - Create via Azure SDK
   - `terraform` - Generate Terraform code
   - `no` - Cancel
   - `edit` - Modify configuration

### Creating a Storage Account

1. Select "Storage Account"
2. Enter Subscription and Resource Group
3. Select region
4. Configure:
   - Name (3-24 chars, lowercase alphanumeric)
   - SKU (Standard_LRS, Premium_LRS, etc.)
   - Kind (StorageV2, BlobStorage, etc.)
   - Access tier (Hot/Cool)
5. Review and confirm

### Creating an AKS Cluster

1. Select "AKS Cluster"
2. Enter Subscription and Resource Group
3. Select region
4. Configure:
   - Cluster name
   - DNS prefix
   - Kubernetes version
   - Node count
   - Node VM size
   - Network plugin
5. Review cost estimate and confirm

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/session` | POST | Create new chat session |
| `/api/chat` | POST | Send chat message |
| `/api/session/{id}` | DELETE | Delete session |
| `/api/health` | GET | Health check |

### Chat Request

```json
{
  "session_id": "uuid-string",
  "message": "I want to create a VM"
}
```

### Chat Response

```json
{
  "session_id": "uuid-string",
  "message": "What size VM would you like?",
  "state": "resource_config",
  "options": ["Standard_B2s", "Standard_D2s_v3"],
  "cost_estimate": {...},
  "resource_summary": {...}
}
```

## 🏷️ Terraform Output

When you choose the Terraform option, you get ready-to-use HCL code:

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "my-resource-group"
  location = "eastus"
}

resource "azurerm_virtual_machine" "vm" {
  # ... full VM configuration
}
```

## 💰 Cost Estimation

The chatbot provides estimated monthly costs including:

- **VM**: Compute, OS disk, Public IP
- **Storage**: Per-GB storage, operations estimate
- **VNet**: Free (data transfer costs apply)
- **AKS**: Management tier, node VMs, load balancer, OS disks

*Note: Estimates are approximate and may vary based on actual usage.*

## 🔒 Security Best Practices

- ✅ Azure credentials stored in environment variables
- ✅ Service Principal with minimal required permissions
- ✅ No credentials exposed to frontend
- ✅ HTTPS recommended for production
- ✅ Session-based conversation state
- ✅ Input validation on all user inputs

## 🛠️ Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# The built files will be in frontend/dist/
```

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_TENANT_ID` | Yes | Azure AD Tenant ID |
| `AZURE_CLIENT_ID` | Yes | Service Principal App ID |
| `AZURE_CLIENT_SECRET` | Yes | Service Principal Secret |
| `AZURE_SUBSCRIPTION_ID` | Yes | Default Azure Subscription |
| `FRONTEND_URL` | No | Frontend URL for CORS (default: http://localhost:5173) |
| `HOST` | No | Backend host (default: 0.0.0.0) |
| `PORT` | No | Backend port (default: 8000) |
| `DEBUG` | No | Enable debug mode (default: false) |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)

---

Built with ❤️ for Azure Cloud Engineers

