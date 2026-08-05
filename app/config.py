import os
from enum import Enum

class LLMProvider(str, Enum):
    GEMINI = "gemini"
    # OPENAI = "openai"
    # ANTHROPIC = "anthropic"

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.1-flash-lite")

MODEL_CONFIG = {
    "parser": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("PARSER_MODEL", DEFAULT_MODEL),
    },
    "srs": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("SRS_MODEL", DEFAULT_MODEL),
    },
    "architecture": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("ARCHITECTURE_MODEL", DEFAULT_MODEL),
    },
    "generator": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("GENERATOR_MODEL", DEFAULT_MODEL),
    },
    "validator": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("VALIDATOR_MODEL", DEFAULT_MODEL),
    },
}

class AgentType(str, Enum):
    PARSER = "parser"
    SRS = "srs"
    ARCHITECTURE = "architecture"
    GENERATOR = "generator"
    VALIDATOR = "validator"

VALIDATION_MAX_RETRIES = 5


archi = """
Production Architecture: Secure Isolated Environment (Azure)
This architecture provides a "Zero Trust" isolated environment in the Central India region. By blocking all internet traffic, we rely on Private Link and internal routing to facilitate communication between the application and the database.

1. Architectural Components
Resource	Logic/Role
Virtual Network (VNet)	Foundation for internal connectivity.
app-subnet / db-subnet	Network segmentation for security boundary.
NSG (nsg-app)	Enforcement point for "Deny All" ingress/egress policies.
app-vm	Compute node, hardened with Managed Identity and no Public IP.
app-pg-db	PostgreSQL Flexible Server, isolated via Private Link.
Key Vault (kv-secrets)	Centralized secret management, integrated with the VM's identity.
Log Analytics	Centralized observability for audit and troubleshooting.
2. Deployment Phases
Phase 1: Foundational Infrastructure
Resource Group: Container for all resources.
Log Analytics Workspace: Deployed early to capture diagnostic logs for subsequent resources.
Virtual Network: Deploy VNet and subnets.
Network Security Group (NSG): Deploy with default "Deny All" rules applied to subnets.
Phase 2: Data & Secrets
Key Vault: Provisioned with soft-delete enabled.
PostgreSQL Flexible Server: Provisioned with Private Link integration into the db-subnet.
Phase 3: Compute & Connectivity
Virtual Machine: Provisioned with System-Assigned Managed Identity.
Private Endpoints: Link the Database and Key Vault to the VNet to ensure they are accessible without public internet.
3. Terraform Module Boundaries
modules/network: VNet, Subnets, and NSG definitions.
modules/compute: VM provisioning, identity assignment, and diagnostics settings.
modules/data: PostgreSQL Flexible Server and Private Link configurations.
modules/security: Key Vault and access policies.
modules/monitoring: Log Analytics Workspace configuration.
4. Security & Networking Implementation
Traffic Lockdown: The NSG will be configured with:
DenyInbound: Priority 4096 (Deny All).
DenyOutbound: Priority 4096 (Deny All).
Note: To allow communication between the VM and DB, explicit "Allow" rules (priority 100-200) will be added to the NSG subnets restricted to the specific internal IP ranges of the application and the database Private Link interface.
Identity: The VM uses Managed Identity to authenticate with Key Vault and the PostgreSQL database. No secrets (passwords) will be stored in source code.
Access: Access to the environment is provided via Azure Bastion (optional recommendation) or private VPN/ExpressRoute, as standard internet access is prohibited.
5. Dependency-Aware Deployment Order
Resource Group
Log Analytics Workspace
VNet & Subnets
Network Security Group (Associate with subnets)
Key Vault
PostgreSQL Flexible Server (Requires VNet/Subnet)
Private Endpoints (Requires VNet, Key Vault, and Postgres)
Virtual Machine (Requires VNet, Key Vault for secret resolution)
6. Architectural Note: Connectivity
Since all inbound and outbound traffic is blocked, please be aware that the VM will be unable to reach public repositories (e.g., apt-get updates) or Azure APIs without Private Link configured for those specific services (Key Vault, Azure Monitor, etc.). Ensure your VNet is configured for Azure Private DNS Zones to resolve these internal endpoints."""


# TEMP: validation test generated files contnet
generated_files = {
    "main.tf": """resource "azurerm_resource_group" "main" {
  name     = "rg-webapp-prod"
  location = "eastus"
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-analytics-prod"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "main" {
  name                = "appi-webapp-prod"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
}

resource "azurerm_mssql_server" "main" {
  name                         = "sql-server-prod"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = "adminuser"
  administrator_login_password = var.sql_admin_password
  minimum_tls_version          = "1.2"
}

resource "azurerm_mssql_database" "main" {
  name           = "sql-db-prod"
  server_id      = azurerm_mssql_server.main.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  sku_name       = "S0"
}

resource "azurerm_service_plan" "main" {
  name                = "asp-webapp-prod"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "P1v2"
}

resource "azurerm_linux_web_app" "main" {
  name                = "app-svc-python-prod"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id
  https_only          = true

  site_config {
    application_stack {
      python_version = "3.9"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.main.instrumentation_key
  }
}""",

    "variables.tf" : """variable "sql_admin_password" {
  description = "Admin password for the SQL server"
  type        = string
  sensitive   = true
}""",

    "outputs.tf": """output "app_service_identity" {
  description = "The principal ID of the App Service managed identity"
  value       = azurerm_linux_web_app.main.identity[0].principal_id
}

output "sql_server_fqdn" {
  description = "The FQDN of the SQL server"
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}"""
}