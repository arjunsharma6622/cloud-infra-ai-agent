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
Production Cloud Architecture: Python Web Application (Azure)
This architecture provides a secure, monitored environment for a Python web application hosted on Azure. It leverages managed identities to eliminate the need for hardcoded database connection strings, ensuring a production-grade security posture.

1. Architectural Components
Resource Name	Type	Reasoning
rg-webapp-prod	Resource Group	Logical container for all project assets.
appi-webapp-prod	Application Insights	Provides Application Performance Management (APM).
log-analytics-prod	Log Analytics Workspace	Centralized data sink for Application Insights and resource logs.
sql-server-prod*	Azure SQL Server	Logical server required to host the SQL database.
sql-db-prod	Azure SQL Database	Backend persistence layer.
asp-webapp-prod*	App Service Plan	Compute abstraction for hosting the App Service.
app-svc-python-prod	App Service (Linux)	Runtime host for the Python web application.
*Inferred infrastructure components required for successful deployment.

2. Deployment Phases and Dependency Order
Resources should be deployed in the following order to ensure dependencies (like logging destinations and compute plans) are available before the application and database are created.

Phase 1: Foundation & Monitoring
Resource Group: rg-webapp-prod
Log Analytics Workspace: log-analytics-prod
Application Insights: appi-webapp-prod (Linked to Workspace)
Phase 2: Data & Compute Infrastructure
Azure SQL Server: (Required parent for sql-db-prod)
Azure SQL Database: sql-db-prod
App Service Plan: asp-webapp-prod (SKU: P1v2)
Phase 3: Application Runtime
App Service: app-svc-python-prod
Configured with System Assigned Managed Identity.
Enabled for HTTPS Only.
Diagnostic logging forwarded to log-analytics-prod.
3. Security & Networking
Identity: The App Service will utilize a System-Assigned Managed Identity. Grant this identity db_datareader and db_datawriter roles within the Azure SQL Database to avoid credential management.
HTTPS: Force HTTPS-only traffic at the App Service level.
Database Access: Firewall rules on the SQL Server will be configured to allow Azure services and resources, with specific IP restrictions for administrative access.
Diagnostic Logging: All resources will push diagnostic logs to the log-analytics-prod workspace.
4. Terraform Module Recommendations
To maintain clean state management and modularity, split the infrastructure into the following blocks:

modules/monitoring: Handles Log Analytics and Application Insights creation.
modules/database: Manages the SQL Server, SQL Database, and firewall rules.
modules/compute: Manages the App Service Plan and App Service, including configuration of the Python runtime settings and Managed Identity association.
5. Architectural Considerations
Region: All resources reside in eastus to ensure low latency and compliance with the project specification.
Auto-scaling: Since the App Service Plan (P1v2) is configured, ensure that the Azure Monitor autoscale rules are defined in the infrastructure code to trigger scaling based on CPU or Memory metrics.
Naming Convention: All resources follow the provided naming pattern (e.g., app-svc-python-prod) to maintain parity with production operations standards.
Note: This architecture assumes the deployment pipeline handles the assignment of the Managed Identity as the SQL database principal, which is the recommended practice for "infrastructure as code" (IaC) deployments."""


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