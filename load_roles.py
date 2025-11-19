# Timestamp: 2025-10-27 04:40:38 UTC
# Hash: 505f7db691fb01d5fd8525ab3ed9226d794df0198af6054c6a6271c155f469cd
"""
AxProtocol Role Loader - Multi-Domain Support with Intelligent Fallback
Loads role definitions based on domain and build type with smart domain mapping
"""

import os
from pathlib import Path
from typing import Dict, Optional, List
from difflib import get_close_matches  # Code quality improvement: Fuzzy matching


# ============================================================================
# DOMAIN MAPPING CONFIGURATION
# ============================================================================

DOMAIN_MAPPING = {
    # Financial/Business domains
    "finance": "strategy",
    "financial": "strategy",
    "accounting": "ops",
    "business": "strategy",
    "sales": "marketing",
    "fundraising": "strategy",
    "investment": "strategy",
    "banking": "strategy",
    "insurance": "strategy",

    # Educational/Academic domains
    "academic": "education",
    "training": "education",
    "learning": "education",
    "curriculum": "education",
    "teaching": "education",
    "university": "education",
    "school": "education",
    "course": "education",

    # Legal/Compliance domains
    "legal": "ops",
    "compliance": "ops",
    "regulatory": "ops",
    "governance": "strategy",
    "policy": "strategy",

    # Healthcare/Medical domains
    "healthcare": "research",
    "medical": "research",
    "clinical": "research",
    "health": "research",
    "pharma": "research",
    "pharmaceutical": "research",
    "biotech": "research",

    # Technology domains (variations)
    "tech": "technical",
    "technology": "technical",
    "engineering": "technical",
    "development": "technical",
    "software": "technical",
    "data": "technical",
    "ai": "technical",
    "ml": "technical",
    "cloud": "technical",
    "cybersecurity": "technical",
    "security": "technical",

    # HR/People domains
    "hr": "ops",
    "human resources": "ops",
    "people": "ops",
    "recruitment": "ops",
    "talent": "ops",
    "hiring": "ops",

    # Design/Creative domains (variations)
    "design": "creative",
    "art": "creative",
    "content": "creative",
    "media": "creative",
    "brand": "marketing",
    "branding": "marketing",
    "advertising": "marketing",
    "copywriting": "creative",

    # Operations domains (variations)
    "operations": "ops",
    "logistics": "ops",
    "supply chain": "ops",
    "manufacturing": "ops",
    "quality": "ops",

    # Research domains (variations)
    "science": "research",
    "analysis": "research",
    "analytics": "research",
    "data science": "research",
    "statistics": "research",

    # Product domains (variations)
    "product management": "product",
    "pm": "product",
    "ux": "product",
    "ui": "creative",
    "user experience": "product",

    # Marketing domains (variations)
    "digital marketing": "marketing",
    "growth": "marketing",
    "seo": "marketing",
    "social media": "marketing",
    "pr": "marketing",
    "public relations": "marketing",
    "communications": "marketing",

    # Strategic domains
    "consulting": "strategy",
    "advisory": "strategy",
    "planning": "strategy",
    "transformation": "strategy",
}

# Default fallback order (most versatile domains first)
DEFAULT_FALLBACK_ORDER = ["strategy", "research", "ops"]


# ============================================================================
# INTELLIGENT DOMAIN RESOLUTION
# ============================================================================

def get_domain_directory(domain: str, verbose: bool = True) -> tuple[Path, str, str]:
    """
    Get the appropriate roles directory for a domain with intelligent mapping.

    Args:
        domain: Requested domain name
        verbose: Whether to print mapping information

    Returns:
        Tuple of (Path to directory, actual domain used, reason/message)
    """
    base_roles = Path(__file__).parent / "roles"
    domain_lower = domain.lower().strip()

    # Try exact match first
    exact_dir = base_roles / domain_lower
    if exact_dir.exists():
        return (exact_dir, domain_lower, "exact_match")

    # Try case-insensitive match with actual directories
    if base_roles.exists():
        for existing_dir in base_roles.iterdir():
            if existing_dir.is_dir() and existing_dir.name.lower() == domain_lower:
                if verbose:
                    print(f"ℹ️  Found case-insensitive match: '{existing_dir.name}'")
                return (existing_dir, existing_dir.name, "case_match")

    # Try direct mapping from configuration
    if domain_lower in DOMAIN_MAPPING:
        mapped_domain = DOMAIN_MAPPING[domain_lower]
        mapped_dir = base_roles / mapped_domain
        if mapped_dir.exists():
            if verbose:
                print(f"ℹ️  Domain '{domain}' → '{mapped_domain}' (direct mapping)")
            return (mapped_dir, mapped_domain, f"mapped_from_{domain}")

    # Try partial keyword matching (e.g., "financial planning" contains "financial")
    for keyword, target_domain in DOMAIN_MAPPING.items():
        # Check if keyword is in domain or domain is in keyword
        if keyword in domain_lower or domain_lower in keyword:
            target_dir = base_roles / target_domain
            if target_dir.exists():
                if verbose:
                    print(f"ℹ️  Domain '{domain}' matched keyword '{keyword}' → '{target_domain}'")
                return (target_dir, target_domain, f"keyword_match_{keyword}")

    # Code quality improvement: Fuzzy matching for user-input domains
    if base_roles.exists():
        available_domains = [d.name for d in base_roles.iterdir() if d.is_dir() and not d.name.startswith('.')]
        fuzzy_matches = get_close_matches(domain_lower, available_domains, n=1, cutoff=0.6)
        if fuzzy_matches:
            fuzzy_domain = fuzzy_matches[0]
            fuzzy_dir = base_roles / fuzzy_domain
            if fuzzy_dir.exists():
                if verbose:
                    print(f"ℹ️  Domain '{domain}' → '{fuzzy_domain}' (fuzzy match, similarity ≥60%)")
                return (fuzzy_dir, fuzzy_domain, f"fuzzy_match_from_{domain_lower}")

    # Final fallback to strategy (most versatile)
    fallback_domain = "strategy"
    fallback_dir = base_roles / fallback_domain

    if fallback_dir.exists():
        if verbose:
            print(f"⚠️  Domain '{domain}' not recognized → using '{fallback_domain}' (general purpose)")
        return (fallback_dir, fallback_domain, "fallback_strategy")

    # Last resort: use first available domain
    if base_roles.exists():
        for existing_dir in base_roles.iterdir():
            if existing_dir.is_dir() and not existing_dir.name.startswith('_'):
                if verbose:
                    print(f"⚠️  Using available domain: '{existing_dir.name}'")
                return (existing_dir, existing_dir.name, "last_resort")

    # Absolute last resort: return non-existent marketing path
    marketing_dir = base_roles / "marketing"
    if verbose:
        print(f"❌ No domain directories found, returning marketing path (may not exist)")
    return (marketing_dir, "marketing", "absolute_fallback")


def get_fallback_domains_for(domain: str) -> List[str]:
    """
    Get ordered list of fallback domains for a given domain.

    Args:
        domain: Domain name

    Returns:
        List of domain names to try in order
    """
    domain_lower = domain.lower().strip()

    # Custom fallback priorities for specific domain types
    domain_priorities = {
        # Financial domains should try strategy first
        "finance": ["strategy", "ops", "research"],
        "financial": ["strategy", "ops", "research"],
        "accounting": ["ops", "strategy", "research"],

        # Educational domains
        "education": ["education", "research", "strategy"],
        "academic": ["education", "research", "strategy"],
        "training": ["education", "ops", "strategy"],

        # Healthcare domains
        "healthcare": ["research", "education", "ops"],
        "medical": ["research", "education", "strategy"],
        "clinical": ["research", "ops", "education"],

        # Legal domains
        "legal": ["ops", "strategy", "research"],
        "compliance": ["ops", "strategy", "research"],

        # Sales/Marketing domains
        "sales": ["marketing", "strategy", "ops"],
        "marketing": ["marketing", "creative", "strategy"],

        # Technical domains
        "tech": ["technical", "product", "research"],
        "technical": ["technical", "product", "research"],
        "engineering": ["technical", "product", "ops"],

        # Creative domains
        "creative": ["creative", "marketing", "product"],
        "design": ["creative", "product", "marketing"],
        "content": ["creative", "marketing", "education"],
    }

    # Try to find specific priorities
    for keyword, priorities in domain_priorities.items():
        if keyword in domain_lower or domain_lower in keyword:
            return priorities

    # Check if domain maps to something
    if domain_lower in DOMAIN_MAPPING:
        mapped = DOMAIN_MAPPING[domain_lower]
        return [mapped] + DEFAULT_FALLBACK_ORDER

    # Default fallback order
    return DEFAULT_FALLBACK_ORDER


# ============================================================================
# ROLE LOADING FUNCTIONS
# ============================================================================

def load_roles_by_pattern(build_type: str = "stable", domain: str = "creative") -> Dict[str, Dict[str, str]]:
    """
    Load role definitions for a specific domain and build type with intelligent fallback.

    Args:
        build_type: "stable", "experimental", or "dev"
        domain: Domain name (marketing, ops, technical, creative, education, product, strategy, research, or any other)

    Returns:
        Dictionary with role names as keys and role config as values:
        {
            "strategist": {"name": "strategist", "content": "Role definition...", "domain": "marketing", ...},
            "analyst": {"name": "analyst", "content": "Role definition...", "domain": "marketing", ...},
            ...
        }

    Directory structure:
        roles/
        ├── marketing/
        │   ├── strategist_stable.txt
        │   ├── analyst_stable.txt
        │   └── ...
        ├── ops/
        │   └── ...
        └── technical/
            └── ...
    """

    # Get the appropriate domain directory with intelligent mapping
    base_dir, actual_domain, mapping_reason = get_domain_directory(domain, verbose=True)

    # Role names to load (Phase 2: Added Caller as Role 0)
    role_names = ["caller", "strategist", "analyst", "producer", "courier", "critic"]

    # Build suffix based on build type
    suffix = f"_{build_type}.txt"

    # Load each role
    roles = {}
    for role_name in role_names:
        role_path = base_dir / f"{role_name}{suffix}"

        # Try stable version if specified version doesn't exist
        if not role_path.exists() and build_type != "stable":
            role_path = base_dir / f"{role_name}_stable.txt"

        # Try without suffix
        if not role_path.exists():
            role_path = base_dir / f"{role_name}.txt"

        # Load role content
        if role_path.exists():
            with open(role_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # Append collaboration contract (non-destructive) to encourage
            # complementary artifacts and cross-role traceability across domains.
            collab_contract = (
                "\n\nCollaboration Contract (Non-Redundancy & Traceability)\n"
                "- Build on prior roles; do not restate their sections.\n"
                "- Introduce new artifacts and assign stable IDs (S-1, A-1, P-1, C-1).\n"
                "- Cross-reference upstream IDs wherever applicable.\n"
                "- Prefer depth and specificity over general prose.\n"
            )
            role_notes = {
                "caller":     "- Caller: Analyze objective and triage (terminate/proceed/suggest optimization).",
                "strategist": "- Strategist: Assign S-IDs and include an S-ID Index.",
                "analyst":    "- Analyst: Assign A-IDs and include an A-ID Map referencing S-IDs.",
                "producer":   "- Producer: Assign P-IDs and reference A-IDs used.",
                "courier":    "- Courier: Reference P-IDs for each scheduled item; optionally assign C-IDs.",
                "critic":     "- Critic: Reference S/A/P/C IDs in Issue->Fix entries."
            }
            note = role_notes.get(role_name, "")
            augmented = content + collab_contract + ("\n" + note if note else "")

            roles[role_name] = {
                "name": role_name,
                "content": augmented,
                "path": str(role_path),
                "domain": actual_domain,
                "requested_domain": domain,
                "build_type": build_type,
                "mapping_reason": mapping_reason
            }
        else:
            print(f"⚠️  Role file not found: {role_path}")
            # Provide fallback inline definition
            roles[role_name] = {
                "name": role_name,
                "content": _get_fallback_role(role_name, actual_domain),
                "path": "inline_fallback",
                "domain": actual_domain,
                "requested_domain": domain,
                "build_type": build_type,
                "mapping_reason": "inline_fallback"
            }

    return roles


def _get_fallback_role(role_name: str, domain: str) -> str:
    """
    Get fallback role definition if file not found.

    Args:
        role_name: Name of the role
        domain: Domain context

    Returns:
        Role definition string
    """

    domain_contexts = {
        "marketing": "campaign assets and lead generation",
        "ops": "process documentation and workflow design",
        "technical": "system architecture and implementation",
        "creative": "original content and brand development",
        "education": "curriculum and learning materials",
        "product": "product specs and user stories",
        "strategy": "strategic plans and business analysis",
        "research": "research design and data analysis"
    }

    context = domain_contexts.get(domain, "deliverables")

    fallbacks = {
        "strategist": f"Role: Strategist. Define high-level strategy for {context}. Be decisive and ground all choices in the objective. Include clear success criteria.",

        "analyst": f"Role: Analyst. Validate assumptions and identify risks for {context}. Provide measurable metrics and A/B alternatives. Prioritize practical solutions.",

        "producer": f"Role: Producer. Create high-quality {context}. Focus on clarity, completeness, and professional execution. Include concrete deliverables.",

        "courier": f"Role: Courier. Design implementation plan for {context}. Include timeline, dependencies, and contingencies. Define clear handoffs.",

        "critic": f"Role: Critic. Audit {context} for quality, completeness, and alignment. Identify issues and provide specific fixes. Rate overall readiness."
    }

    return fallbacks.get(role_name, f"Role: {role_name.capitalize()}. Execute your responsibilities for {context}.")


def get_available_domains() -> list:
    """
    Get list of available domain directories.

    Returns:
        List of domain names that have role directories
    """
    roles_dir = Path(__file__).parent / "roles"

    if not roles_dir.exists():
        return ["strategy"]  # Changed from "marketing" to more versatile fallback

    domains = []
    for item in roles_dir.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            domains.append(item.name)

    return sorted(domains) if domains else ["strategy"]


def get_all_mapped_domains() -> Dict[str, str]:
    """
    Get all domain mappings (both existing and mapped).

    Returns:
        Dictionary of {domain_name: target_directory}
    """
    available = get_available_domains()
    result = {domain: domain for domain in available}

    # Add all mappings
    for source, target in DOMAIN_MAPPING.items():
        if target in available:
            result[source] = target

    return result


def validate_roles(domain: str, build_type: str = "stable") -> bool:
    """
    Validate that all required roles exist for a domain (with intelligent mapping).

    Args:
        domain: Domain name
        build_type: Build type

    Returns:
        True if all roles found, False otherwise
    """
    base_dir, actual_domain, _ = get_domain_directory(domain, verbose=False)
    role_names = ["strategist", "analyst", "producer", "courier", "critic"]

    missing = []
    for role_name in role_names:
        role_path = base_dir / f"{role_name}_{build_type}.txt"
        if not role_path.exists():
            # Try stable fallback
            role_path = base_dir / f"{role_name}_stable.txt"
        if not role_path.exists():
            missing.append(role_name)

    if missing:
        print(f"⚠️  Missing roles for {domain} (using {actual_domain}): {', '.join(missing)}")
        return False

    return True


# ============================================================================
# TESTING AND UTILITIES
# ============================================================================

if __name__ == "__main__":
    # Test the loader
    print("=" * 70)
    print("Testing AxProtocol Role Loader with Intelligent Domain Mapping")
    print("=" * 70)

    print("\n📁 Available domain directories:", get_available_domains())

    print("\n🗺️  Sample domain mappings:")
    test_domains = ["finance", "healthcare", "legal", "tech", "design", "education", "unknown_domain"]
    for test_domain in test_domains:
        _, actual, reason = get_domain_directory(test_domain, verbose=False)
        print(f"  '{test_domain}' → '{actual}' ({reason})")

    print("\n" + "=" * 70)
    print("Testing role loading...")
    print("=" * 70)

    # Test loading marketing roles
    print("\n✅ Loading marketing roles:")
    roles = load_roles_by_pattern("stable", "marketing")
    for role_name, role_data in roles.items():
        print(f"  ✓ {role_name}: {len(role_data['content'])} chars (domain: {role_data['domain']})")

    # Test loading with domain mapping
    print("\n✅ Loading finance roles (should map to strategy):")
    roles = load_roles_by_pattern("stable", "finance")
    for role_name, role_data in roles.items():
        print(f"  ✓ {role_name}: domain={role_data['domain']}, reason={role_data['mapping_reason']}")

    # Test loading unknown domain
    print("\n✅ Loading completely unknown domain:")
    roles = load_roles_by_pattern("stable", "quantum_physics")
    for role_name, role_data in roles.items():
        print(f"  ✓ {role_name}: domain={role_data['domain']}, reason={role_data['mapping_reason']}")

    # Test validation
    print("\n" + "=" * 70)
    print("Validating all available domains...")
    print("=" * 70)
    for domain in get_available_domains():
        valid = validate_roles(domain, "stable")
        status = "✅" if valid else "⚠️"
        print(f"  {status} {domain}")

    print("\n" + "=" * 70)
    print("All mapped domains:")
    print("=" * 70)
    all_mappings = get_all_mapped_domains()
    for source, target in sorted(all_mappings.items()):
        marker = "→" if source != target else "•"
        print(f"  {marker} {source:30} {target}")
