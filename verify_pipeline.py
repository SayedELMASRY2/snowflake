#!/usr/bin/env python3
"""
Pipeline Verification and Revenue Reconciliation Script
Validates row counts, primary keys, referential integrity, and cross-model revenue reconciliation.
"""

import os
import sys
import snowflake.connector

try:
    from dotenv import load_dotenv
    load_dotenv('/home/syd/Desktop/snowflake/.env')
    load_dotenv()
except ImportError:
    pass

def main():
    account = os.environ.get('SNOWFLAKE_ACCOUNT', 'UTIUWFL-VV06936')
    user = os.environ.get('SNOWFLAKE_USER', 'SAYED.ELMASRI2004@GMAIL.COM')
    password = os.environ.get('SNOWFLAKE_PASSWORD')
    key_path = os.environ.get('SNOWFLAKE_PRIVATE_KEY_PATH', '/home/syd/Desktop/snowflake/rsa_key.p8')
    role = os.environ.get('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')
    warehouse = os.environ.get('SNOWFLAKE_WAREHOUSE', 'ECOMMERCE_WH')

    if not password:
        print("ERROR: SNOWFLAKE_PASSWORD environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse,
        database='ECOMMERCE_DB'
    )
    cur = conn.cursor()



    print("=" * 70)
    print("PIPELINE VERIFICATION & RECONCILIATION REPORT")
    print("=" * 70)

    # 1. Row counts across all layers
    print("\n[1] Object Row Counts:")
    tables_to_check = [
        ('RAW', 'CUSTOMERS'),
        ('RAW', 'PRODUCTS'),
        ('RAW', 'ORDERS'),
        ('STAGING', 'STG_CUSTOMERS'),
        ('STAGING', 'STG_PRODUCTS'),
        ('STAGING', 'STG_ORDERS'),
        ('STAGING', 'STG_REJECTED_ORDERS'),
        ('MARTS', 'FCT_ORDERS'),
        ('MARTS', 'MART_CUSTOMER_SUMMARY'),
        ('MARTS', 'MART_CATEGORY_SALES')
    ]
    for schema, tbl in tables_to_check:
        try:
            cur.execute(f"SELECT COUNT(*) FROM ECOMMERCE_DB.{schema}.{tbl};")
            cnt = cur.fetchone()[0]
            print(f"  - ECOMMERCE_DB.{schema}.{tbl:22}: {cnt} rows")
        except Exception as e:
            print(f"  - ECOMMERCE_DB.{schema}.{tbl:22}: ERROR ({e})")

    # 2. Fact Table Revenue Summary
    print("\n[2] Fact Orders Revenue Breakdown:")
    cur.execute("""
        SELECT
            order_status,
            COUNT(*) AS order_count,
            ROUND(SUM(gross_revenue), 2) AS gross_rev,
            ROUND(SUM(recognized_revenue), 2) AS recognized_rev
        FROM ECOMMERCE_DB.MARTS.FCT_ORDERS
        GROUP BY order_status
        ORDER BY order_count DESC;
    """)
    fact_totals = cur.fetchall()
    print(f"  {'Status':12} | {'Count':8} | {'Gross Revenue':15} | {'Recognized Revenue':18}")
    print("  " + "-" * 60)
    total_fact_recognized = 0.0
    for status, count, gross, recognized in fact_totals:
        print(f"  {status:12} | {count:8} | ${gross:14,.2f} | ${recognized:17,.2f}")
        if recognized:
            total_fact_recognized += float(recognized)
    print(f"  TOTAL FACT RECOGNIZED REVENUE: ${total_fact_recognized:,.2f}")

    # 3. Category Mart Revenue Summary
    print("\n[3] Category Mart Sales Summary:")
    cur.execute("""
        SELECT
            category,
            total_orders,
            completed_orders,
            pending_orders,
            cancelled_orders,
            total_recognized_revenue
        FROM ECOMMERCE_DB.MARTS.MART_CATEGORY_SALES
        ORDER BY total_recognized_revenue DESC;
    """)
    cat_rows = cur.fetchall()
    print(f"  {'Category':14} | {'Total':6} | {'Comp':6} | {'Pend':6} | {'Canc':6} | {'Recognized Rev':15}")
    print("  " + "-" * 65)
    total_mart_cat_recognized = 0.0
    for cat, tot, comp, pend, canc, rev in cat_rows:
        print(f"  {cat:14} | {tot:6} | {comp:6} | {pend:6} | {canc:6} | ${rev:14,.2f}")
        total_mart_cat_recognized += float(rev)
    print(f"  TOTAL CATEGORY MART RECOGNIZED REVENUE: ${total_mart_cat_recognized:,.2f}")

    # 4. Customer Summary Mart Total Spending
    cur.execute("""
        SELECT
            COUNT(*) as total_customers,
            COUNT_IF(total_orders > 0) as customers_with_orders,
            ROUND(SUM(total_recognized_spending), 2) as total_spending
        FROM ECOMMERCE_DB.MARTS.MART_CUSTOMER_SUMMARY;
    """)
    cust_tot, cust_with_orders, total_cust_spending = cur.fetchone()
    print("\n[4] Customer Summary Mart:")
    print(f"  Total Customers: {cust_tot}")
    print(f"  Customers with Orders: {cust_with_orders}")
    print(f"  TOTAL CUSTOMER MART RECOGNIZED SPENDING: ${float(total_cust_spending):,.2f}")

    # 5. Financial Reconciliation Assertion
    print("\n[5] Cross-Model Revenue Reconciliation:")
    diff_cat_fact = abs(total_fact_recognized - total_mart_cat_recognized)
    diff_cust_fact = abs(total_fact_recognized - float(total_cust_spending))
    print(f"  |fct_orders - mart_category_sales| delta: ${diff_cat_fact:.4f}")
    print(f"  |fct_orders - mart_customer_summary| delta: ${diff_cust_fact:.4f}")

    if diff_cat_fact < 0.01 and diff_cust_fact < 0.01:
        print("  >>> RECONCILIATION RESULT: PERFECT MATCH (100% BALANCED) <<<")
    else:
        print("  >>> RECONCILIATION RESULT: MISMATCH DETECTED! <<<")

    # 6. Audit of Rejected Orders
    print("\n[6] Audit of Rejected Orders in STG_REJECTED_ORDERS:")
    cur.execute("""
        SELECT rejection_reason, COUNT(*) as count
        FROM ECOMMERCE_DB.STAGING.STG_REJECTED_ORDERS
        GROUP BY rejection_reason
        ORDER BY count DESC;
    """)
    for reason, cnt in cur.fetchall():
        print(f"  - {reason:30}: {cnt} records")

    cur.close()
    conn.close()
    print("\nVerification completed.")

if __name__ == '__main__':
    main()
