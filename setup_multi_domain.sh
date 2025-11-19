#!/bin/bash
# AxProtocol Multi-Domain Setup Script
# Creates directory structure and validates installation

echo "=========================================="
echo "AxProtocol Multi-Domain Setup"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo ""

# Create roles directory structure
echo "Creating roles directory structure..."
mkdir -p roles/marketing
mkdir -p roles/ops
mkdir -p roles/technical
mkdir -p roles/creative
mkdir -p roles/education
mkdir -p roles/product
mkdir -p roles/strategy
mkdir -p roles/research

echo "✅ Directories created"
echo ""

# Create placeholder files for domains not yet populated
echo "Creating placeholder files..."

# Product domain placeholders
for role in strategist analyst producer courier critic; do
    if [ ! -f "roles/product/${role}_stable.txt" ]; then
        echo "Role: ${role^} (Product Domain - Placeholder)" > "roles/product/${role}_stable.txt"
        echo "This is a placeholder. Product-specific role definition needed." >> "roles/product/${role}_stable.txt"
    fi
done

# Strategy domain placeholders
for role in strategist analyst producer courier critic; do
    if [ ! -f "roles/strategy/${role}_stable.txt" ]; then
        echo "Role: ${role^} (Strategy Domain - Placeholder)" > "roles/strategy/${role}_stable.txt"
        echo "This is a placeholder. Strategy-specific role definition needed." >> "roles/strategy/${role}_stable.txt"
    fi
done

# Research domain placeholders
for role in strategist analyst producer courier critic; do
    if [ ! -f "roles/research/${role}_stable.txt" ]; then
        echo "Role: ${role^} (Research Domain - Placeholder)" > "roles/research/${role}_stable.txt"
        echo "This is a placeholder. Research-specific role definition needed." >> "roles/research/${role}_stable.txt"
    fi
done

# Marketing domain placeholders (if files don't exist)
for role in strategist analyst producer courier critic; do
    if [ ! -f "roles/marketing/${role}_stable.txt" ]; then
        echo "Role: ${role^} (Marketing Domain - Placeholder)" > "roles/marketing/${role}_stable.txt"
        echo "This is a placeholder. Marketing-specific role definition needed." >> "roles/marketing/${role}_stable.txt"
    fi
done

echo "✅ Placeholder files created"
echo ""

# Validate required files
echo "Validating installation..."
echo ""

# Check for DomainConfig.json
if [ -f "DomainConfig.json" ]; then
    echo "✅ DomainConfig.json found"
else
    echo "❌ DomainConfig.json missing - CREATE THIS FILE"
fi

# Check for domain_detector.py
if [ -f "domain_detector.py" ]; then
    echo "✅ domain_detector.py found"
else
    echo "❌ domain_detector.py missing - CREATE THIS FILE"
fi

# Check for load_roles.py
if [ -f "load_roles.py" ]; then
    echo "✅ load_roles.py found"
else
    echo "❌ load_roles.py missing - CREATE THIS FILE"
fi

# Check for run.py
if [ -f "run.py" ]; then
    echo "✅ run.py found"
else
    echo "❌ run.py missing - CREATE THIS FILE"
fi

echo ""
echo "Checking role files..."
echo ""

# Count role files per domain
for domain in marketing ops technical creative education product strategy research; do
    count=$(find "roles/$domain" -name "*_stable.txt" 2>/dev/null | wc -l)
    if [ "$count" -eq 5 ]; then
        echo "✅ $domain: $count/5 roles"
    else
        echo "⚠️  $domain: $count/5 roles (incomplete)"
    fi
done

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add missing role definition files"
echo "2. Configure .env with OPENAI_API_KEY"
echo "3. Test with: python run.py 'Your objective'"
echo ""
echo "Example commands:"
echo "  python run.py 'Launch marketing campaign'"
echo "  DOMAIN=technical python run.py 'Build REST API'"
echo "  DOMAIN=ops python run.py 'Design onboarding workflow'"
echo ""