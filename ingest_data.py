#!/usr/bin/env python3
"""
Automated Snowflake Ingestion and Setup Script
Ingests customers.csv, products.csv, and orders.csv into ECOMMERCE_DB.RAW.*
Uses Snowflake internal staging and COPY INTO commands.
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
    role = os.environ.get('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')
    warehouse = os.environ.get('SNOWFLAKE_WAREHOUSE', 'ECOMMERCE_WH')

    if not password:
        print("ERROR: SNOWFLAKE_PASSWORD environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to Snowflake account '{account}' as user '{user}'...")
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        role=role,
        warehouse=warehouse
    )
    cur = conn.cursor()

    print("Step 1: Ensuring warehouse, database, and schemas exist...")
    cur.execute("CREATE WAREHOUSE IF NOT EXISTS ECOMMERCE_WH WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;")
    cur.execute("CREATE DATABASE IF NOT EXISTS ECOMMERCE_DB;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS ECOMMERCE_DB.RAW;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS ECOMMERCE_DB.STAGING;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS ECOMMERCE_DB.MARTS;")

    cur.execute("USE DATABASE ECOMMERCE_DB;")
    cur.execute("USE SCHEMA RAW;")
    cur.execute("USE WAREHOUSE ECOMMERCE_WH;")

    print("Step 2: Creating file format and stage...")
    cur.execute("""
    CREATE OR REPLACE FILE FORMAT ECOMMERCE_DB.RAW.CSV_INGEST_FORMAT
        TYPE = 'CSV'
        FIELD_DELIMITER = ','
        SKIP_HEADER = 1
        FIELD_OPTIONALLY_ENCLOSED_BY = '\"'
        NULL_IF = ('', 'NULL', 'null')
        EMPTY_FIELD_AS_NULL = TRUE
        TRIM_SPACE = TRUE
        ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;
    """)

    cur.execute("""
    CREATE OR REPLACE STAGE ECOMMERCE_DB.RAW.CSV_STAGE
        FILE_FORMAT = ECOMMERCE_DB.RAW.CSV_INGEST_FORMAT;
    """)

    print("Step 3: Creating raw tables...")
    cur.execute("""
    CREATE OR REPLACE TABLE ECOMMERCE_DB.RAW.CUSTOMERS (
        customer_id NUMBER(38,0),
        customer_name VARCHAR(255),
        email VARCHAR(255),
        city VARCHAR(255),
        signup_date DATE
    );
    """)

    cur.execute("""
    CREATE OR REPLACE TABLE ECOMMERCE_DB.RAW.PRODUCTS (
        product_id NUMBER(38,0),
        product_name VARCHAR(255),
        category VARCHAR(100),
        price NUMBER(10,2)
    );
    """)

    cur.execute("""
    CREATE OR REPLACE TABLE ECOMMERCE_DB.RAW.ORDERS (
        order_id NUMBER(38,0),
        customer_id NUMBER(38,0),
        product_id NUMBER(38,0),
        quantity VARCHAR(50),
        order_date DATE,
        status VARCHAR(50)
    );
    """)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')

    tables_and_files = [
        ('CUSTOMERS', os.path.join(data_dir, 'customers.csv')),
        ('PRODUCTS', os.path.join(data_dir, 'products.csv')),
        ('ORDERS', os.path.join(data_dir, 'orders.csv'))
    ]

    print("Step 4: Uploading files to internal stage and executing COPY INTO...")
    for table_name, file_path in tables_and_files:
        print(f"  Uploading {file_path} to @CSV_STAGE...")
        cur.execute(f"PUT 'file://{file_path}' @ECOMMERCE_DB.RAW.CSV_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;")
        
        file_name = os.path.basename(file_path)
        print(f"  Copying into {table_name} from @CSV_STAGE/{file_name}.gz...")
        cur.execute(f"""
        COPY INTO ECOMMERCE_DB.RAW.{table_name}
        FROM @ECOMMERCE_DB.RAW.CSV_STAGE/{file_name}.gz
        FILE_FORMAT = ECOMMERCE_DB.RAW.CSV_INGEST_FORMAT
        ON_ERROR = 'CONTINUE';
        """)

    print("\n--- Verifying Ingested Tables ---")
    for table_name, _ in tables_and_files:
        cur.execute(f"SELECT COUNT(*) FROM ECOMMERCE_DB.RAW.{table_name};")
        cnt = cur.fetchone()[0]
        print(f"  ECOMMERCE_DB.RAW.{table_name}: {cnt} rows")

    cur.close()
    conn.close()
    print("\nIngestion completed successfully!")

if __name__ == '__main__':
    main()
