#!/bin/bash
# validate_hat_sentry.sh — Validation locale avant push
# Usage: bash scripts/validate_hat_sentry.sh
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "========================================="
echo " HAT SENTRY — Validation Locale"
echo "========================================="
echo ""

# --- 1. Python compilation ---
echo "1. Python compilation..."
for f in hat_sentry/models/*.py hat_sentry_binance/models/*.py; do
    if [ -f "$f" ]; then
        if ! python3 -m py_compile "$f" 2>/dev/null; then
            echo -e "  ${RED}FAIL${NC} $f"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "  ${GREEN}OK${NC}   $f"
        fi
    fi
done
echo ""

# --- 2. XML parsing ---
echo "2. XML parsing..."
for f in $(find . -name "*.xml" -not -path "./.git/*"); do
    if ! python3 -c "import xml.etree.ElementTree as ET; ET.parse('$f')" 2>/dev/null; then
        echo -e "  ${RED}FAIL${NC} $f"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "  ${GREEN}OK${NC}   $f"
    fi
done
echo ""

# --- 3. Cross-validation: record rules vs model fields ---
echo "3. Record rules ↔ model fields cross-validation..."
for xml_file in hat_sentry/security/hat_sentry_security.xml; do
    if [ ! -f "$xml_file" ]; then continue; fi

    # Extract domain_force fields
    domains=$(grep -oP "domain_force.*?\[.*?\]" "$xml_file" 2>/dev/null || true)

    # For each rule, check if the model has the referenced fields
    while IFS= read -r line; do
        # Extract field names from domain like ('company_id', 'in', ...)
        fields=$(echo "$line" | grep -oP "'\K[^']+(?=',)" | head -5 || true)

        for field in $fields; do
            # Skip common Odoo fields
            if [[ "$field" == "company_id" || "$field" == "id" || "$field" == "create_date" || "$field" == "write_date" ]]; then
                # For company_id, we need to check if the model actually has it
                # Find which model this rule is for
                model=$(grep -B5 "$line" "$xml_file" | grep -oP 'ref="model_\K[^"]+' | head -1 || true)
                if [ -n "$model" ]; then
                    # Convert model name to Python file path
                    py_file="hat_sentry/models/$(echo "$model" | sed 's/\./_/g').py"
                    if [ -f "$py_file" ]; then
                        if ! grep -q "company_id" "$py_file" 2>/dev/null; then
                            echo -e "  ${RED}FAIL${NC} Rule references 'company_id' but $py_file has no company_id field"
                            ERRORS=$((ERRORS + 1))
                        fi
                    fi
                fi
            fi
        done
    done <<< "$domains"
done
echo ""

# --- 4. Check XML IDs referenced in security XML exist ---
echo "4. XML ID cross-validation..."
for xml_file in hat_sentry/security/hat_sentry_security.xml; do
    if [ ! -f "$xml_file" ]; then continue; fi

    # Extract ref="model_*" references
    refs=$(grep -oP 'ref="\K[^"]+' "$xml_file" | grep "^model_" || true)
    for ref in $refs; do
        # Convert model_xxx to _name = "xxx"
        model_name=$(echo "$ref" | sed 's/^model_//' | sed 's/_/./g')
        # Check if any Python file defines this model
        found=$(grep -rl "_name = \"$model_name\"" hat_sentry/models/ hat_sentry_binance/models/ 2>/dev/null || true)
        if [ -z "$found" ]; then
            echo -e "  ${YELLOW}WARN${NC} $ref referenced but no model definition found for $model_name"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
done
echo ""

# --- 5. Check __manifest__.py data files exist ---
echo "5. Manifest data files validation..."
for manifest in hat_sentry/__manifest__.py hat_sentry_binance/__manifest__.py; do
    if [ ! -f "$manifest" ]; then continue; fi
    module_dir=$(dirname "$manifest")

    # Extract data files
    data_files=$(grep -oP '"data":\s*\[\K[^\]]+' "$manifest" | tr ',' '\n' | tr -d '"' | tr -d "'" | tr -d ' ' || true)
    while IFS= read -r f; do
        f=$(echo "$f" | tr -d ' ')
        if [ -z "$f" ]; then continue; fi
        if [ ! -f "$module_dir/$f" ]; then
            echo -e "  ${RED}FAIL${NC} $manifest references $f but file not found"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "  ${GREEN}OK${NC}   $module_dir/$f"
        fi
    done <<< "$data_files"
done
echo ""

# --- 6. Check ir.model.access.csv models exist ---
echo "6. Access CSV ↔ model validation..."
for csv_file in hat_sentry/security/ir.model.access.csv hat_sentry_binance/security/ir.model.access.csv; do
    if [ ! -f "$csv_file" ]; then continue; fi

    # Extract model names from CSV (field 3 = model_id:id like "model_hat_sentry_asset")
    models=$(tail -n +2 "$csv_file" | cut -d',' -f3 | sed 's/^model_//' | sed 's/_/./g' | sort -u || true)
    while IFS= read -r model; do
        model=$(echo "$model" | tr -d ' ')
        if [ -z "$model" ]; then continue; fi
        # Check if model is defined
        model_dot=$(echo "$model" | sed 's/_/./g')
        found=$(grep -rl "_name = \"$model_dot\"" hat_sentry/models/ hat_sentry_binance/models/ 2>/dev/null || true)
        if [ -z "$found" ]; then
            # Check if it's an AbstractModel
            abstract=$(grep -rl "_name = \"$model_dot\"" hat_sentry/models/ hat_sentry_binance/models/ 2>/dev/null | xargs grep -l "AbstractModel" 2>/dev/null || true)
            if [ -z "$abstract" ]; then
                echo -e "  ${YELLOW}WARN${NC} CSV references model '$model_dot' but no definition found"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    done <<< "$models"
done
echo ""

# --- Summary ---
echo "========================================="
echo " RESULTS"
echo "========================================="
echo -e " Errors:   ${RED}$ERRORS${NC}"
echo -e " Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}VALIDATION FAILED — Fix errors before push${NC}"
    exit 1
else
    echo -e "${GREEN}VALIDATION PASSED${NC} — Safe to push"
    exit 0
fi
