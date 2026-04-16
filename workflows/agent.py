# Copyright (c) 2026 Denzil Greenwood. All rights reserved.
# Licensed under the Business Source License 1.1 (BUSL-1.1)
# See BUSL_1_1_LICENSE for license terms
#
# LICENSING NOTE:
# Original CIAF workflow implementations integrated with Google ADK (Apache 2.0).
# CIAF control plane logic is BUSL-1.1; ADK framework integration is Apache 2.0.

"""
CIAF Workflows as ADK Agents

Exports all 6 workflow agents for ADK web UI discovery.
Choose which agent to interact with from the web interface.
"""

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.plugins import ContextFilterPlugin

# Import all agent exports
from .healthcare_claims import root_agent as healthcare_claims_agent
from .financial_approvals import root_agent as financial_approvals_agent
from .production_changes import root_agent as production_changes_agent
from .customer_communications import root_agent as customer_communications_agent
from .data_access_export import root_agent as data_access_agent
from .web_search import root_agent as web_search_agent

# Create a main router agent that helps users choose which workflow to use
router_agent = Agent(
    name="ciaf_workflow_router",
    model="gemini-2.5-flash",
    instruction="""
You are the CIAF Workflows Router.

Available workflows:
1. **Healthcare Claims** - Process medical claims with compliance controls
2. **Financial Approvals** - Route payments through approval chains
3. **Production Changes** - Manage infrastructure changes with risk assessment
4. **Customer Communications** - Enforce policies on customer-facing messages
5. **Data Access** - Control data access with classification and tenant isolation
6. **Web Search** - Search the internet with content governance

When a user arrives, help them understand what each workflow does and guide them
to the appropriate one for their needs. Explain the CIAF governance controls
(Identity, Policy, Privilege, Execution, Evidence) that protect each workflow.

Ask clarifying questions to understand their use case, then recommend the best workflow.
Be helpful in explaining how governance protects the organization.
""",
    description="Router to guide users to the appropriate CIAF workflow agent",
)

# Create App with all agents for ADK discovery
root_agent = App(
    name="ciaf_workflows",
    description="Six CIAF workflow agents demonstrating governance in different domains",
    root_agent=router_agent,
    plugins=[
        ContextFilterPlugin(num_invocations_to_keep=5),
    ],
)

__all__ = [
    "root_agent",
    "healthcare_claims_agent",
    "financial_approvals_agent",
    "production_changes_agent",
    "customer_communications_agent",
    "data_access_agent",
    "web_search_agent",
]
