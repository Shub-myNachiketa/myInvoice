import sqlite3
import pandas as pd
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label as PopupLabel

# Import the export function from your file
from export_to_excel import export_to_excel

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
        COALESCE(i.additional_discount, 0) AS additional_discount,
        SUM(p.price * ii.quantity) - COALESCE(i.additional_discount, 0) AS payable_amount,
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
        p.price AS price,
        p.price * ii.quantity AS total_price,
        i.additional_discount AS additional_discount,
        p.price * ii.quantity - COALESCE(i.additional_discount, 0) AS payable_amount,
        i.payment_mode AS payment_mode
    FROM invoices i
    JOIN customers c ON i.customer_id = c.id
    JOIN invoice_items ii ON i.id = ii.invoice_id
    JOIN products p ON ii.product_id = p.id
    '''
    return pd.read_sql_query(query, conn)

class InvoiceApp(App):
    def build(self):
        self.conn = sqlite3.connect('invoices.db')

        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Customer Details
        customer_layout = BoxLayout(orientation='vertical', spacing=10)
        customer_layout.add_widget(Label(text='Customer Name'))
        self.customer_name = TextInput(size_hint_y=None, height=40)
        customer_layout.add_widget(self.customer_name)

        customer_layout.add_widget(Label(text='Email'))
        self.customer_email = TextInput(size_hint_y=None, height=40)
        customer_layout.add_widget(self.customer_email)

        customer_layout.add_widget(Label(text='Phone'))
        self.customer_phone = TextInput(size_hint_y=None, height=40, input_filter='int')
        self.customer_phone.bind(text=self.validate_phone_number)
        customer_layout.add_widget(self.customer_phone)

        self.layout.add_widget(customer_layout)

        # Product List with Scroll
        self.product_list_container = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.product_list_container.bind(minimum_height=self.product_list_container.setter('height'))

        self.product_list_scroll = ScrollView(size_hint=(1, 0.6), size=(self.layout.width, 400))
        self.product_list_scroll.add_widget(self.product_list_container)

        self.layout.add_widget(self.product_list_scroll)

        # Add Product Button
        self.add_product_button = Button(text='Add Product', size_hint_y=None, height=40)
        self.add_product_button.bind(on_press=self.add_product)
        self.layout.add_widget(self.add_product_button)

        # Additional Discount
        additional_discount_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        self.additional_discount_input = TextInput(hint_text='Additional Discount Amount', input_filter='float', size_hint_x=0.7)
        apply_discount_button = Button(text='Apply', size_hint_x=0.3)
        apply_discount_button.bind(on_press=self.apply_discount_to_products)
        additional_discount_layout.add_widget(self.additional_discount_input)
        additional_discount_layout.add_widget(apply_discount_button)

        self.layout.add_widget(additional_discount_layout)

        # Payment Mode
        payment_mode_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        payment_mode_layout.add_widget(Label(text='Payment Mode:', size_hint_x=None, width=120))
        self.payment_mode_spinner = Spinner(
            text='Select Payment Mode',
            values=('CASH', 'UPI'),
            size_hint_x=None,
            width=200
        )
        payment_mode_layout.add_widget(self.payment_mode_spinner)
        self.layout.add_widget(payment_mode_layout)

        # Total Price
        self.total_price_label = Label(text='Total Price: ₹0.00', size_hint_y=None, height=40)
        self.layout.add_widget(self.total_price_label)

        # Payable Amount
        self.payable_amount_label = Label(text='Payable Amount: ₹0.00', size_hint_y=None, height=40)
        self.layout.add_widget(self.payable_amount_label)

        # Generate Invoice Button
        self.generate_button = Button(text='Generate Invoice', size_hint_y=None, height=40)
        self.generate_button.bind(on_press=self.generate_invoice)
        self.layout.add_widget(self.generate_button)

        # Report Button
        self.report_button = Button(text='Generate Report', size_hint_y=None, height=40)
        self.report_button.bind(on_press=self.generate_report)
        self.layout.add_widget(self.report_button)

        # Initialize product rows
        self.product_rows = []

        return self.layout

    def validate_phone_number(self, instance, value):
        if len(value) > 10:
            self.customer_phone.text = value[:10]
        elif not value.isdigit():
            self.customer_phone.text = ''.join(filter(str.isdigit, value))

    def add_product(self, instance):
        product_row = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=60)
        
        product_spinner = Spinner(
            text='Select Product',
            values=self.get_products(),
            size_hint_x=0.4
        )
        quantity_input = TextInput(hint_text='Quantity', input_filter='int', size_hint_x=0.2)
        price_label = Label(text='₹0.00', size_hint_x=0.2)
        remove_button = Button(text='X', size_hint_x=0.2)
        remove_button.bind(on_press=lambda btn: self.remove_product(product_row))
        
        product_spinner.bind(text=self.update_product_details)
        quantity_input.bind(text=self.update_totals)
        
        product_row.add_widget(product_spinner)
        product_row.add_widget(quantity_input)
        product_row.add_widget(price_label)
        product_row.add_widget(remove_button)
        
        self.product_list_container.add_widget(product_row)
        self.product_rows.append((product_row, product_spinner, quantity_input, price_label))
        
        self.update_totals()

    def remove_product(self, product_row):
        self.product_list_container.remove_widget(product_row)
        self.product_rows = [row for row in self.product_rows if row[0] != product_row]
        self.update_totals()

    def get_products(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM products")
        products = [row[0] for row in cursor.fetchall()]
        return products

    def update_product_details(self, spinner, text):
        for row, product_spinner, quantity_input, price_label in self.product_rows:
            if product_spinner == spinner:
                cursor = self.conn.cursor()
                cursor.execute("SELECT price FROM products WHERE name = ?", (text,))
                result = cursor.fetchone()
                if result:
                    price = result[0]
                    price_label.text = f'₹{price:,.2f}'
                    self.update_totals()
                else:
                    price_label.text = '₹0.00'

    def update_totals(self, instance=None, value=None):
        total_price = 0
        for _, _, quantity_input, price_label in self.product_rows:
            try:
                quantity = int(quantity_input.text or 0)
                price = float(price_label.text.replace('₹', '').replace(',', ''))
                total_price += quantity * price
            except ValueError:
                continue
        
        self.total_price_label.text = f'Total Price: ₹{total_price:,.2f}'
        
        additional_discount = float(self.additional_discount_input.text or 0)
        payable_amount = total_price - additional_discount
        self.payable_amount_label.text = f'Payable Amount: ₹{payable_amount:,.2f}'

    def apply_discount_to_products(self, instance):
        self.update_totals()

    def generate_invoice(self, instance):
        name = self.customer_name.text
        email = self.customer_email.text
        phone = self.customer_phone.text
        payment_mode = self.payment_mode_spinner.text
        
        if not self.validate_invoice_data(name, email, phone, payment_mode):
            return
        
        total_price = float(self.total_price_label.text.replace('Total Price: ₹', '').replace(',', ''))
        additional_discount = float(self.additional_discount_input.text or 0)

        cursor = self.conn.cursor()
        
        cursor.execute("INSERT INTO invoices (customer_id, date, total, additional_discount, payment_mode) VALUES (?, ?, ?, ?, ?)", 
                       (self.get_customer_id(name, email, phone), pd.Timestamp.now().strftime('%Y-%m-%d'), total_price, additional_discount, payment_mode))
        invoice_id = cursor.lastrowid
        
        for _, product_spinner, quantity_input, _ in self.product_rows:
            product_name = product_spinner.text
            quantity = int(quantity_input.text or 0)
            cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,))
            result = cursor.fetchone()
            if result:
                product_id = result[0]
                cursor.execute("INSERT INTO invoice_items (invoice_id, product_id, quantity) VALUES (?, ?, ?)", (invoice_id, product_id, quantity))
            else:
                self.show_popup('Error', f'Product "{product_name}" not found in database.')
        
        self.conn.commit()
        self.show_popup('Invoice Generated', f'Invoice ID: {invoice_id}')

    def get_customer_id(self, name, email, phone):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM customers WHERE name = ? AND email = ? AND phone = ?", (name, email, phone))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            cursor.execute("INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
            self.conn.commit()
            return cursor.lastrowid

    def validate_invoice_data(self, name, email, phone, payment_mode):
        if not name or not email or not phone or payment_mode == 'Select Payment Mode':
            self.show_popup('Validation Error', 'Please fill out all fields correctly.')
            return False
        return True

    def show_popup(self, title, message):
        popup = Popup(title=title, content=PopupLabel(text=message), size_hint=(None, None), size=(400, 200))
        popup.open()

    def generate_report(self, instance):
        try:
            order_wise_df = fetch_order_wise_data(self.conn)
            item_wise_df = fetch_item_wise_data(self.conn)
            export_to_excel(order_wise_df, item_wise_df)
            self.show_popup('Report Generated', 'Report has been generated and saved as "order_item_wise_export.xlsx".')
        except Exception as e:
            self.show_popup('Error', f'An error occurred while generating the report: {e}')

if __name__ == '__main__':
    InvoiceApp().run()
