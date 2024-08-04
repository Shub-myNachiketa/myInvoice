import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def fetch_order_wise_data(conn):
    query = '''
    SELECT
        i.date AS time,
        i.id AS invoice_id,
        c.name AS customer_name,
        c.email AS customer_email,
        c.phone AS customer_phone,
        SUM(ii.quantity) AS total_product_quantity,
        SUM(p.price * ii.quantity) AS total_price,
        COALESCE(SUM(i.additional_discount), 0) AS additional_discount,
        SUM(p.price * ii.quantity) - COALESCE(SUM(i.additional_discount), 0) AS payable_amount,
        i.payment_mode AS payment_mode
    FROM invoices i
    JOIN customers c ON i.customer_id = c.id
    JOIN invoice_items ii ON i.id = ii.invoice_id
    JOIN products p ON ii.product_id = p.id
    GROUP BY i.id
    '''
    return pd.read_sql_query(query, conn)

def fetch_item_wise_data(conn):
    query = '''
    SELECT
        i.date AS time,
        i.id AS invoice_id,
        c.name AS customer_name,
        c.email AS customer_email,
        c.phone AS customer_phone,
        p.name AS product_name,
        ii.quantity AS product_quantity,
        (SELECT SUM(quantity) FROM invoice_items WHERE invoice_id = i.id) AS total_product_quantity,
        p.price AS price,
        p.price * ii.quantity AS total_price,
        COALESCE(i.additional_discount, 0) AS additional_discount,
        p.price * ii.quantity - COALESCE(i.additional_discount, 0) AS payable_amount,
        i.payment_mode AS payment_mode
    FROM invoices i
    JOIN customers c ON i.customer_id = c.id
    JOIN invoice_items ii ON i.id = ii.invoice_id
    JOIN products p ON ii.product_id = p.id
    '''
    return pd.read_sql_query(query, conn)

def export_to_excel(order_wise_df, item_wise_df):
    try:
        # Create a Pandas Excel writer using OpenPyXL as the engine
        with pd.ExcelWriter('order_item_wise_export.xlsx', engine='openpyxl') as writer:
            # Write Order Wise Data
            order_wise_df.to_excel(writer, sheet_name='Order Wise', index=False)

            # Write Item Wise Data
            item_wise_df.to_excel(writer, sheet_name='Item Wise', index=False)

        print("Database export completed and saved as 'order_item_wise_export.xlsx'")

    except PermissionError as e:
        print(f"PermissionError: {e}. Please ensure that the file is not open in another application and try again.")
    except Exception as e:
        print(f"An error occurred: {e}")
