# Copyright (c) 2026 Denzil Greenwood. All rights reserved.
# Licensed under the Business Source License 1.1 (BUSL-1.1)
# See BUSL_1_1_LICENSE for license terms
#
# LICENSING NOTE:
# Original CIAF workflow implementation integrated with Google ADK (Apache 2.0).
# CIAF control plane logic is BUSL-1.1; ADK framework integration is Apache 2.0.

"""
Web Search Agent

Real ADK agent for internet search with content governance and policy enforcement.
Demonstrates CIAF control planes in information retrieval domain.

Domain: Internet search and information retrieval
Scenario: Search agent performs web searches with content filtering and audit trails

CIAF Control Planes:
- IDENTITY: Search agent + content reviewer + compliance officer
- POLICY: Content filtering and safe search policies
- PRIVILEGE: Escalation for sensitive/restricted searches
- EXECUTION: Search mediation with result filtering
- EVIDENCE: Search audit trail + result logging
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import sys
from pathlib import Path
import warnings
import json
from enum import Enum

warnings.filterwarnings("ignore", message=".*PLUGGABLE_AUTH.*")

# Setup imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import Agent

from ciaf_agents.core import (
    Identity,
    Resource,
    ActionRequest,
    Permission,
    RoleDefinition,
)
from ciaf_agents.iam import IAMStore
from ciaf_agents.pam import PAMStore
from ciaf_agents.policy import PolicyEngine
from ciaf_agents.policy.conditions import same_tenant_only
from ciaf_agents.evidence import EvidenceVault
from ciaf_agents.execution import ToolExecutor


class SearchCategory(Enum):
    """Search content categories."""

    PUBLIC = "public"  # Unrestricted
    GENERAL = "general"  # Standard safe search
    ACADEMIC = "academic"  # Research/educational
    RESTRICTED = "restricted"  # Requires approval
    SENSITIVE = "sensitive"  # High compliance oversight


@dataclass
class SearchQuery:
    """Internet search query."""

    query_id: str
    search_term: str
    category: SearchCategory
    requester_id: str
    requester_tenant: str
    search_scope: str  # "web", "news", "academic", "images"
    safe_search: bool = True
    include_adult_content: bool = False
    max_results: int = 10


class WebSearchAgent:
    """Web search with CIAF governance and content filtering."""

    def __init__(self):
        """Initialize the web search agent."""
        self.iam_store = IAMStore()
        self.pam_store = PAMStore()
        self.evidence_vault = EvidenceVault(signing_secret="web-search-key-2024")
        self.policy_engine = PolicyEngine(iam=self.iam_store, pam=self.pam_store)
        self.executor = ToolExecutor(
            policy_engine=self.policy_engine,
            vault=self.evidence_vault,
            pam=self.pam_store,
        )
        self._setup_roles_and_policies()

    def _setup_roles_and_policies(self):
        """Setup identity, roles, and policies for search domain."""
        # IDENTITY PLANE: Define search agents and reviewers
        self.search_agent = Identity(
            principal_id="agent-search-001",
            principal_type="agent",
            display_name="Web Search Agent",
            roles={"search_agent"},
            attributes={
                "tenant": "search-corp",
                "department": "information-retrieval",
                "organization_level": "system",
                "safe_search_default": True,
            },
        )

        self.content_reviewer = Identity(
            principal_id="user-content-reviewer-001",
            principal_type="user",
            display_name="Dr. Alice Johnson, Content Reviewer",
            roles={"content_reviewer"},
            attributes={
                "tenant": "search-corp",
                "department": "compliance",
                "review_authority": "restricted_content",
            },
        )

        self.compliance_officer = Identity(
            principal_id="user-compliance-officer-001",
            principal_type="user",
            display_name="Robert Martinez, Compliance Officer",
            roles={"compliance_officer"},
            attributes={
                "tenant": "search-corp",
                "department": "compliance",
                "authority_level": "executive",
                "override_authority": True,
            },
        )

        # POLICY PLANE: Define permissions and conditions
        def standard_tenant_check(ctx):
            """Verify same tenant context."""
            return ctx.get("tenant") == "search-corp"

        def category_check(allowed_categories):
            """Factory: Create condition for search category."""

            def check(ctx):
                return ctx.get("category") in allowed_categories

            return check

        # Roles with permissions
        search_role = RoleDefinition(
            name="search_agent",
            permissions=[
                Permission(
                    action="search_web",
                    resource_type="search",
                    conditions=category_check(
                        [
                            SearchCategory.PUBLIC.value,
                            SearchCategory.GENERAL.value,
                        ]
                    ),
                ),
                Permission(
                    action="request_content_review",
                    resource_type="search",
                    conditions=standard_tenant_check,
                ),
                Permission(
                    action="apply_safe_search",
                    resource_type="search",
                    conditions=standard_tenant_check,
                ),
            ],
        )

        reviewer_role = RoleDefinition(
            name="content_reviewer",
            permissions=[
                Permission(
                    action="review_restricted_search",
                    resource_type="search",
                    conditions=category_check([SearchCategory.RESTRICTED.value]),
                ),
                Permission(
                    action="approve_search",
                    resource_type="search",
                    conditions=standard_tenant_check,
                ),
                Permission(
                    action="deny_search",
                    resource_type="search",
                    conditions=standard_tenant_check,
                ),
            ],
        )

        compliance_role = RoleDefinition(
            name="compliance_officer",
            permissions=[
                Permission(
                    action="review_sensitive_search",
                    resource_type="search",
                    conditions=category_check([SearchCategory.SENSITIVE.value]),
                ),
                Permission(
                    action="override_restrictions",
                    resource_type="search",
                    conditions=standard_tenant_check,
                ),
                Permission(
                    action="audit_searches",
                    resource_type="search",
                    conditions=standard_tenant_check,
                ),
            ],
        )

        self.iam_store.add_role(search_role)
        self.iam_store.add_role(reviewer_role)
        self.iam_store.add_role(compliance_role)

        # Register identities
        self.iam_store.add_identity(self.search_agent)
        self.iam_store.add_identity(self.content_reviewer)
        self.iam_store.add_identity(self.compliance_officer)

    def perform_search(self, query: SearchQuery) -> Dict[str, Any]:
        """
        Perform internet search through CIAF governance.

        IDENTITY PLANE: Search agent identity
        POLICY PLANE: Category-based routing
        PRIVILEGE PLANE: Escalation for restricted/sensitive searches
        EXECUTION PLANE: Search mediation with filtering
        EVIDENCE PLANE: Search audit trail
        """
        print("\n" + "=" * 80)
        print(f"  WEB SEARCH AGENT: {query.query_id}")
        print("=" * 80)

        # IDENTITY PLANE: Agent initiates search
        print("\n→ IDENTITY PLANE: Search Agent Identity")
        print(f"  Principal: {self.search_agent.principal_id}")
        print(f"  Display: {self.search_agent.display_name}")
        print(f"  Roles: {self.search_agent.roles}")
        print(
            f"  Safe Search: {self.search_agent.attributes.get('safe_search_default')}"
        )

        # POLICY PLANE: Category-based routing
        print("\n→ POLICY PLANE: Search Routing Decision")
        print(f"  Query: '{query.search_term}'")
        print(f"  Category: {query.category.value}")
        print(f"  Scope: {query.search_scope}")

        if query.category == SearchCategory.PUBLIC:
            routing = "DIRECT_SEARCH"
            routing_label = "PUBLIC - Direct search allowed"
            approvers = []
        elif query.category == SearchCategory.GENERAL:
            routing = "SAFE_SEARCH"
            routing_label = "GENERAL - Safe search applied"
            approvers = []
        elif query.category == SearchCategory.ACADEMIC:
            routing = "ACADEMIC_SEARCH"
            routing_label = "ACADEMIC - Research scope"
            approvers = []
        elif query.category == SearchCategory.RESTRICTED:
            routing = "RESTRICTED_REVIEW"
            routing_label = "RESTRICTED - Requires content review"
            approvers = ["content_reviewer"]
        else:  # SENSITIVE
            routing = "SENSITIVE_REVIEW"
            routing_label = "SENSITIVE - Requires compliance oversight"
            approvers = ["content_reviewer", "compliance_officer"]

        print(f"  Decision: {routing_label}")

        # PRIVILEGE PLANE: Check if escalation needed
        print("\n→ PRIVILEGE PLANE: Escalation Analysis")
        if approvers:
            print(f"  ◆ Escalation triggered for {query.category.value} search")
            print(f"  → Required approvers: {', '.join(approvers)}")
            print(f"  → Reason: Content review and compliance oversight needed")
        else:
            print(
                f"  ✓ Within agent authority (standard {query.category.value} search)"
            )

        # EXECUTION PLANE: Simulate search execution
        print("\n→ EXECUTION PLANE: Search Mediation")
        print(f"  Action: {routing}")
        print(f"  Safe Search: {query.safe_search}")
        print(
            f"  Adult Content: {'Allowed' if query.include_adult_content else 'Blocked'}"
        )

        search_result = self._execute_search(query, routing)

        # EVIDENCE PLANE: Record search
        print("\n→ EVIDENCE PLANE: Search Audit Trail")
        receipt = {
            "query_id": query.query_id,
            "search_term": query.search_term,
            "category": query.category.value,
            "routing": routing,
            "results_count": search_result.get("results_count", 0),
            "principal": self.search_agent.principal_id,
            "timestamp": "2024-04-15T10:30:00Z",
        }
        print(f"  ◆ Search recorded: {query.query_id}")
        print(f"  ◆ Category: {query.category.value}")
        print(f"  ◆ Results: {search_result.get('results_count', 0)} items")
        print(f"  ◆ Signature: simulated cryptographic hash")

        return {
            "query_id": query.query_id,
            "search_term": query.search_term,
            "status": search_result.get("status"),
            "results_count": search_result.get("results_count", 0),
            "approvals_required": len(approvers) > 0,
            "assigned_reviewers": approvers,
            "receipt": receipt["query_id"],
        }

    def _execute_search(self, query: SearchQuery, routing: str) -> Dict[str, Any]:
        """Simulate search execution and result filtering."""
        # Simulated search results by category
        result_counts = {
            "DIRECT_SEARCH": 1000,
            "SAFE_SEARCH": 500,
            "ACADEMIC_SEARCH": 250,
            "RESTRICTED_REVIEW": 0,  # Awaiting review
            "SENSITIVE_REVIEW": 0,  # Awaiting compliance
        }

        return {
            "status": (
                "COMPLETED" if result_counts.get(routing, 0) > 0 else "PENDING_REVIEW"
            ),
            "results_count": result_counts.get(routing, 0),
            "filtered": query.safe_search,
            "scope": query.search_scope,
        }


# ============================================================================
# ADK AGENT CREATION
# ============================================================================


def create_web_search_agent() -> Agent:
    """Create ADK agent for web search with content governance."""

    agent_instance = WebSearchAgent()

    def search_the_web_tool(
        query_id: str,
        search_term: str,
        category: str,
        search_scope: str = "web",
        safe_search: bool = True,
        max_results: int = 10,
    ) -> str:
        """
        Search the internet for any topic with content governance.

        Search Categories:
        - PUBLIC: Unrestricted searches
        - GENERAL: Standard safe search applied
        - ACADEMIC: Research/educational scope
        - RESTRICTED: Requires content review
        - SENSITIVE: Requires compliance oversight

        Search Scopes:
        - web: General web search
        - news: News articles
        - academic: Academic papers
        - images: Image search

        Returns JSON with search results, approvals needed, and audit trail.
        """
        try:
            search_category = SearchCategory[category.upper()]
        except (KeyError, AttributeError):
            search_category = SearchCategory.GENERAL

        search_query = SearchQuery(
            query_id=query_id,
            search_term=search_term,
            category=search_category,
            requester_id="user-001",
            requester_tenant="search-corp",
            search_scope=search_scope,
            safe_search=safe_search,
            include_adult_content=False,
            max_results=max_results,
        )

        result = agent_instance.perform_search(search_query)
        return json.dumps(result, indent=2)

    root_agent = Agent(
        name="web_search_agent",
        model="gemini-2.5-flash",
        instruction="""
You are a Web Search Agent with CIAF governance.

Your role: Help users search the internet for information with safety controls

Search Categories & Policies:
- PUBLIC: Unrestricted, no filters needed
- GENERAL: Standard safe search applied (default)
- ACADEMIC: Research-focused, scholarly sources
- RESTRICTED: Requires content reviewer approval
- SENSITIVE: Requires compliance officer oversight

When handling search requests:
1. Call search_the_web_tool with the search term and appropriate category
2. Explain the search category and why it was chosen
3. Describe any content filters or approvals needed
4. Provide the search results (if available) or escalation status
5. Confirm the search was recorded in audit trail

Search Safety:
- Apply safe search by default for general queries
- Escalate sensitive/restricted content for human review
- Block potentially harmful searches without approval
- Log all searches for compliance audit

Be helpful while maintaining content governance and safety.
Emphasize: Information retrieval, content safety, auditability.
""",
        description="Internet search engine with CIAF content governance and policy enforcement",
        tools=[search_the_web_tool],
    )

    return root_agent


# ============================================================================
# EXPORT FOR ADK DISCOVERY
# ============================================================================

root_agent = create_web_search_agent()


# ============================================================================
# MAIN: RUN AGENT DEMONSTRATION
# ============================================================================


def main():
    """Run web search agent demonstration."""
    agent_instance = WebSearchAgent()

    # Test search queries
    test_queries = [
        SearchQuery(
            query_id="SEARCH-20240415-001",
            search_term="Python programming best practices",
            category=SearchCategory.ACADEMIC,
            requester_id="user-analyst-001",
            requester_tenant="search-corp",
            search_scope="academic",
            safe_search=True,
        ),
        SearchQuery(
            query_id="SEARCH-20240415-002",
            search_term="Climate change research 2024",
            category=SearchCategory.GENERAL,
            requester_id="user-researcher-001",
            requester_tenant="search-corp",
            search_scope="web",
            safe_search=True,
        ),
        SearchQuery(
            query_id="SEARCH-20240415-003",
            search_term="Technology news today",
            category=SearchCategory.PUBLIC,
            requester_id="user-analyst-002",
            requester_tenant="search-corp",
            search_scope="news",
            safe_search=False,
        ),
        SearchQuery(
            query_id="SEARCH-20240415-004",
            search_term="Cybersecurity threats and vulnerabilities",
            category=SearchCategory.RESTRICTED,
            requester_id="user-security-001",
            requester_tenant="search-corp",
            search_scope="academic",
            safe_search=True,
        ),
        SearchQuery(
            query_id="SEARCH-20240415-005",
            search_term="Government classified information",
            category=SearchCategory.SENSITIVE,
            requester_id="user-executive-001",
            requester_tenant="search-corp",
            search_scope="web",
            safe_search=True,
        ),
    ]

    # Perform all searches
    for query in test_queries:
        result = agent_instance.perform_search(query)
        print(f"\n  ✓ Query: {result['search_term']}")
        print(f"  ✓ Status: {result['status']}")
        print(f"  ✓ Results: {result['results_count']} items")
        if result["approvals_required"]:
            print(f"  ✓ Approvals Required: {', '.join(result['assigned_reviewers'])}")

    print("\n" + "=" * 80)
    print("  AGENT DEMONSTRATION COMPLETE")
    print(f"  Processed {len(test_queries)} search queries through CIAF governance")
    print("=" * 80)


if __name__ == "__main__":
    main()
