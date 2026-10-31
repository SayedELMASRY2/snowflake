#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo " Starting End-to-End Snowflake & dbt Analytics Pipeline Execution"
echo "======================================================================"

# 1. Activate isolated Python 3.11 virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# 2. Source local environment variables if .env exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "[Info] Loading environment variables from $SCRIPT_DIR/.env..."
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# 3. Check for required Snowflake password
if [ -z "$SNOWFLAKE_PASSWORD" ]; then
    echo "[ERROR] SNOWFLAKE_PASSWORD is not set."
    echo "Please configure SNOWFLAKE_PASSWORD in $SCRIPT_DIR/.env or export it."
    exit 1
fi

export SNOWFLAKE_ACCOUNT="${SNOWFLAKE_ACCOUNT:-UTIUWFL-VV06936}"
export SNOWFLAKE_USER="${SNOWFLAKE_USER:-SAYED.ELMASRI2004@GMAIL.COM}"
export SNOWFLAKE_ROLE="${SNOWFLAKE_ROLE:-ACCOUNTADMIN}"
export SNOWFLAKE_WAREHOUSE="${SNOWFLAKE_WAREHOUSE:-ECOMMERCE_WH}"
export SNOWFLAKE_DATABASE="${SNOWFLAKE_DATABASE:-ECOMMERCE_DB}"
export SNOWFLAKE_SCHEMA="${SNOWFLAKE_SCHEMA:-PUBLIC}"

echo "[Step 1] Verifying dbt connection to Snowflake..."
cd "$SCRIPT_DIR/ecommerce_dbt"
"$SCRIPT_DIR/.venv/bin/dbt" debug --profiles-dir "$SCRIPT_DIR/ecommerce_dbt"

echo "[Step 2] Executing Snowflake infrastructure setup and CSV ingestion..."
cd "$SCRIPT_DIR"
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/ingest_data.py"

echo "[Step 3] Running dbt transformation pipeline (Staging + Marts)..."
cd "$SCRIPT_DIR/ecommerce_dbt"
"$SCRIPT_DIR/.venv/bin/dbt" run --profiles-dir "$SCRIPT_DIR/ecommerce_dbt"

echo "[Step 4] Running dbt data quality test suite (53 tests)..."
"$SCRIPT_DIR/.venv/bin/dbt" test --profiles-dir "$SCRIPT_DIR/ecommerce_dbt"

echo "[Step 5] Generating dbt documentation and catalog..."
"$SCRIPT_DIR/.venv/bin/dbt" docs generate --profiles-dir "$SCRIPT_DIR/ecommerce_dbt"

echo "[Step 6] Running cross-model verification and revenue reconciliation..."
cd "$SCRIPT_DIR"
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/verify_pipeline.py"


echo "======================================================================"
echo " Pipeline Execution and Verification Completed Successfully!"
echo "======================================================================"
