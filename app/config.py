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

resource "azurerm_application_insightsx" "main" {
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