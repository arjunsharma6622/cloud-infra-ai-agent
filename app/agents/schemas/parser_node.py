from typing import List, Optional, Literal

from pydantic import BaseModel, Field

# ------------------------------------------------------------------
# Resource Models
# ------------------------------------------------------------------


class CloudResource(BaseModel):
    name: str = Field(
        description="Logical name of the cloud resource."
    )

    resource_type: str = Field(
        description="Exact cloud service name (Azure App Service, Azure SQL Database, Azure Key Vault, etc.)"
    )

    sku: Optional[str] = Field(
        default=None,
        description="SKU, pricing tier, VM size, or service plan if specified or inferred."
    )

    specifications: str = Field(
        description="Configuration details such as OS, storage size, runtime, replication, version, scaling, etc."
    )

    reasoning: str = Field(
        description="Why this resource is required."
    )

    source: Literal["explicit", "inferred"] = Field(
        description="Whether the resource was explicitly requested by the user or inferred as a cloud best practice."
    )


# ------------------------------------------------------------------
# Networking
# ------------------------------------------------------------------


class NetworkSpec(BaseModel):
    topology: str = Field(
        description="Network topology (Hub and Spoke, Single VNet, Multi VPC, etc.)"
    )

    subnets: List[str] = Field(
        description="Logical subnet names."
    )

    security_rules: List[str] = Field(
        description="High-level security rules."
    )


# ------------------------------------------------------------------
# Deployment Preferences
# ------------------------------------------------------------------


class DeploymentPreferences(BaseModel):

    environment: Optional[str] = Field(
        default=None,
        description="Environment such as dev, test, staging, or production."
    )

    naming_convention: Optional[str] = Field(
        default=None,
        description="Naming convention requested by the user."
    )

    managed_identity: Optional[bool] = None

    private_endpoints: Optional[bool] = None

    https_only: Optional[bool] = None

    diagnostic_logging: Optional[bool] = None


# ------------------------------------------------------------------
# Project Spec
# ------------------------------------------------------------------


class ProjectSpec(BaseModel):

    cloud_provider: str = Field(
        description="AWS, Azure, GCP, etc."
    )

    region: str = Field(
        description="Deployment region."
    )

    networking: NetworkSpec

    compute: List[CloudResource] = Field(default_factory=list)

    databases: List[CloudResource] = Field(default_factory=list)

    storage: List[CloudResource] = Field(default_factory=list)

    security: List[CloudResource] = Field(
        default_factory=list,
        description="Security resources such as Key Vault, WAF, Firewall, NSGs."
    )

    monitoring: List[CloudResource] = Field(
        default_factory=list,
        description="Monitoring resources such as Log Analytics, Application Insights, Azure Monitor."
    )

    integration: List[CloudResource] = Field(
        default_factory=list,
        description="Integration resources such as Logic Apps, Service Bus, Event Grid, API Management."
    )

    deployment_preferences: Optional[DeploymentPreferences] = None

    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made while interpreting the user's request."
    )

    additional_info: List[str] = Field(
        default_factory=list,
        description="Other relevant user preferences or constraints."
    )

    missing_critical_requirements: List[str] = Field(
        default_factory=list,
        description="Questions that must be answered before infrastructure generation."
    )


# ------------------------------------------------------------------
# Parser Output
# ------------------------------------------------------------------


class IntentParserResult(BaseModel):

    needs_clarification: bool = Field(
        description="Whether clarification is required."
    )

    clarification_questions: List[str] = Field(
        default_factory=list,
        description="Questions for the user."
    )

    project_spec: Optional[ProjectSpec] = Field(
        default=None,
        description="Null if clarification is required."
    )

