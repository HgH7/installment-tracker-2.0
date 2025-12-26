from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkToplevel, CTkTextbox, CTkCheckBox, CTkScrollableFrame, CTkRadioButton
from tkinter import ttk, messagebox, filedialog, StringVar, BooleanVar
import tkinter as tk
import os
import re
import logging
from datetime import datetime, timedelta
from utils import StyleManager, CSVManager, FileManager, DatePicker
from helpers import refresh_treeview, show_payment_history, export_to_excel, refresh_payment_history_views


def setup_view_page(frame, frames, show_frame, app, csv_manager):
    frame.grid_rowconfigure(2, weight=1)  # Table
    frame.grid_rowconfigure(3, weight=0)  # Buttons
    
    # Simplified header with clean design
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 15))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="عرض العملاء",
        font_style="heading"
    ).grid(row=0, column=0, pady=(5, 5), sticky="w")
    
    # Simplified search area with better spacing
    search_frame = StyleManager.create_frame(frame)
    search_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))
    search_frame.grid_columnconfigure(1, weight=1)
    
    # Simple search label
    StyleManager.create_label(
        search_frame,
        text="بحث:",
        font_style="body_bold"
    ).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
    
    # Clean search entry
    search_entry = StyleManager.create_entry(
        search_frame,
        width=400,
        font=("Arial", 14),
        height=35,
        placeholder_text="أدخل اسم العميل أو رقم الهاتف..."
    )
    search_entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")
    
    def perform_search():
        query = search_entry.get().strip()
        results = csv_manager.search_customers(query)
        refresh_treeview(frame.tree, csv_manager, results)
        
        # Update status message with search results
        result_count = len(results)
        status_label.configure(text=f"العملاء: {result_count}")
    
    # Add keyboard binding for Enter key
    search_entry.bind("<Return>", lambda event: perform_search())
    
    search_button = StyleManager.create_button(
        search_frame,
        text="بحث",
        width=100,
        height=35,
        command=perform_search
    )
    search_button.grid(row=0, column=2, padx=(0, 0), pady=5)
    
    # Simple status label
    status_label = StyleManager.create_label(
        search_frame,
        text="",
        font_style="small",
        text_color=StyleManager.COLORS["text_secondary"]
    )
    status_label.grid(row=0, column=3, padx=(10, 0), pady=5, sticky="e")
    
    # Clean table container with more breathing room
    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)
    
    # Configure Treeview style for better visibility and modern look
    style = ttk.Style()
    style.configure(
        "Custom.Treeview",
        rowheight=40,
        font=("Arial", 12),
        background=StyleManager.COLORS["surface"],
        foreground=StyleManager.COLORS["text"],
        fieldbackground=StyleManager.COLORS["surface"]
    )
    style.configure(
        "Custom.Treeview.Heading",
        font=("Arial", 12, "bold"),
        background=StyleManager.COLORS["primary"],
        foreground=StyleManager.COLORS["text"]
    )
    style.map(
        "Custom.Treeview",
        background=[("selected", StyleManager.COLORS["primary"])],
        foreground=[("selected", StyleManager.COLORS["text"])]
    )
    
    # Define column headers mapping - simplified
    column_headers = {
        "Name": "اسم العميل",
        "Phone": "رقم الهاتف",
        "Amount": "المبلغ",
        "Installments": "عدد الأقساط",
        "Installment Value": "قيمة القسط",
        "Start Date": "تاريخ البدء"
    }
    
    # Create Treeview with responsive columns
    tree = ttk.Treeview(
        table_frame,
        columns=list(column_headers.keys()),
        show="headings",
        style="Custom.Treeview"
    )
    
    # Configure column proportions
    column_weights = {
        "Name": 25,
        "Phone": 20,
        "Amount": 15,
        "Installments": 15,
        "Installment Value": 15,
        "Start Date": 10
    }
    
    # Set dynamic column widths and headers
    for col in column_headers.keys():
        width = int((column_weights[col] / 100) * 1200)  # Base width of 1200 pixels
        tree.column(col, width=width, minwidth=100)
        tree.heading(col, text=column_headers[col])
    
    tree.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    
    # Add scrollbars
    y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    y_scrollbar.grid(row=0, column=1, sticky="ns")
    
    x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    x_scrollbar.grid(row=1, column=0, sticky="ew")
    
    tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
    
    # Store the Treeview widget as an attribute of the frame
    frame.tree = tree
    
    # Initial data load
    refresh_treeview(tree, csv_manager)
    
    # Update status label with initial count
    data = csv_manager.read_data()
    status_label.configure(text=f"العملاء: {len(data)}")
    
    # Edit customer function - keeping functionality intact
    def edit_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد عميل للتعديل.")
            return
            
        # Get selected customer data
        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]
        
        # Get full customer data
        data = csv_manager.read_data()
        customer = next((c for c in data if c["Name"] == customer_name), None)
        
        if not customer:
            messagebox.showerror("خطأ", "لم يتم العثور على بيانات العميل.")
            return
        
        # Create edit window
        edit_window = CTkToplevel(app)
        edit_window.geometry("800x600")
        edit_window.title(f"تعديل بيانات العميل: {customer_name}")
        
        # Add header
        StyleManager.create_label(
            edit_window,
            text=f"تعديل بيانات العميل: {customer_name}",
            font_style="heading"
        ).pack(pady=(20, 10))
        
        # Create form container
        form_frame = StyleManager.create_frame(edit_window)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Form fields with current values
        fields = [
            {"label": "اسم العميل:", "key": "Name", "type": "text"},
            {"label": "رقم الهاتف:", "key": "Phone", "type": "phone"},
            {"label": "المبلغ:", "key": "Amount", "type": "number"},
            {"label": "عدد الأقساط:", "key": "Installments", "type": "number"}
        ]
        
        entries = {}
        row = 0
        
        for field in fields:
            # Create field container
            field_frame = StyleManager.create_frame(form_frame)
            field_frame.pack(fill="x", padx=10, pady=10)
            field_frame.grid_columnconfigure(1, weight=1)
            
            # Add label
            StyleManager.create_label(
                field_frame,
                text=field["label"],
                font_style="body_bold"
            ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            # Add entry with current value
            entry = StyleManager.create_entry(field_frame, width=300)
            entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, str(customer.get(field["key"], "")))
            entries[field["key"]] = entry
            
            row += 1
        
        # Date Picker Section
        date_frame = StyleManager.create_frame(form_frame)
        date_frame.pack(fill="x", padx=10, pady=10)
        date_frame.grid_columnconfigure(1, weight=1)
        
        StyleManager.create_label(
            date_frame,
            text="تاريخ بدء الأقساط:",
            font_style="body_bold"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        start_date_entry = StyleManager.create_entry(date_frame, width=200)
        start_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        start_date_entry.insert(0, str(customer.get("Start Date", "")))
        entries["Start Date"] = start_date_entry
        
        date_picker_btn = StyleManager.create_button(
            date_frame,
            text="اختر التاريخ",
            style="secondary",
            command=lambda: DatePicker(edit_window, start_date_entry)
        )
        date_picker_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # Buttons container
        buttons_frame = StyleManager.create_frame(edit_window)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        def save_changes():
            # Validation patterns
            name_pattern = r"^[A-Za-z؀-ۿ\s]+$"
            phone_pattern = r"^\+?\d{10,15}$"
            amount_pattern = r"^\d+(\.\d{1,2})?$"
            installments_pattern = r"^\d+$"
            
            # Get values from entries
            name = entries["Name"].get().strip()
            phone = entries["Phone"].get().strip()
            amount = entries["Amount"].get().strip()
            installments = entries["Installments"].get().strip()
            start_date = entries["Start Date"].get().strip()
            
            # Validate inputs
            if not re.fullmatch(name_pattern, name):
                messagebox.showerror("خطأ", "الاسم يجب أن يحتوي فقط على أحرف ومسافات.")
                return
                
            if not re.fullmatch(phone_pattern, phone):
                messagebox.showerror("خطأ", "رقم الهاتف يجب أن يحتوي على أرقام فقط ويبدأ بـ +.")
                return
                
            if not re.fullmatch(amount_pattern, amount):
                messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقمًا صالحًا.")
                return
                
            if not re.fullmatch(installments_pattern, installments):
                messagebox.showerror("خطأ", "عدد الأقساط يجب أن يكون رقمًا صحيحًا.")
                return
            
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("خطأ", "تنسيق التاريخ غير صحيح. يجب أن يكون بهذا الشكل: YYYY-MM-DD")
                return
            
            try:
                # Convert and calculate values
                amount_float = float(amount)
                installments_int = int(installments)
                installment_value = round(amount_float / installments_int, 2)
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                
                # Generate new installment dates
                installment_dates = [
                    (start_date_obj + timedelta(days=30 * i)).strftime("%Y-%m-%d") 
                    for i in range(installments_int)
                ]
                
                # Prepare updated data
                updated_data = {
                    "Name": name,
                    "Phone": phone,
                    "Amount": amount_float,
                    "Installments": installments_int,
                    "Installment Value": installment_value,
                    "Start Date": start_date,
                    "Installment Dates": ";".join(installment_dates)
                }
                
                # If name changed, delete old record and create new one
                if customer_name != name:
                    if csv_manager.delete_customer(customer_name) and csv_manager.append_customer({
                        **updated_data,
                        "Notification Sent": customer.get("Notification Sent", False),
                        "Paid_Installments": customer.get("Paid_Installments", "[]")
                    }):
                        messagebox.showinfo("نجاح", "تم تحديث بيانات العميل بنجاح!")
                        edit_window.destroy()
                        refresh_treeview(tree, csv_manager)
                        refresh_payment_history_views(app)  # Refresh payment history views
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات العميل.")
                else:
                    # Update existing record
                    if csv_manager.update_customer(customer_name, updated_data):
                        messagebox.showinfo("نجاح", "تم تحديث بيانات العميل بنجاح!")
                        edit_window.destroy()
                        refresh_treeview(tree, csv_manager)
                        refresh_payment_history_views(app)  # Refresh payment history views
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات العميل.")
                
            except ValueError as e:
                messagebox.showerror("خطأ", f"خطأ في البيانات المدخلة: {str(e)}")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
            
        # Save Button
        StyleManager.create_button(
            buttons_frame,
            text="حفظ التغييرات",
            width=200,
            command=save_changes
        ).grid(row=0, column=0, padx=10, pady=10)
        
        # Cancel Button
        StyleManager.create_button(
            buttons_frame,
            text="إلغاء",
            style="secondary",
            width=200,
            command=edit_window.destroy
        ).grid(row=0, column=1, padx=10, pady=10)
        
        # Make the window modal
        edit_window.transient(app)
        edit_window.grab_set()
        edit_window.focus_set()
    
    # Delete customer function
    def delete_customer():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد عميل للحذف.")
            return
            
        # Get selected customer data
        item = tree.item(selected_items[0])
        values = item["values"]
        customer_name = values[0]
        
        # Confirm deletion
        if messagebox.askyesno("تأكيد الحذف", f"هل أنت متأكد من حذف العميل {customer_name}؟\nلا يمكن التراجع عن هذه العملية."):
            if csv_manager.delete_customer(customer_name):
                messagebox.showinfo("نجاح", f"تم حذف العميل {customer_name} بنجاح.")
                refresh_treeview(tree, csv_manager)
            else:
                messagebox.showerror("خطأ", "فشل في حذف العميل.")
    
    # Action buttons with simplified design
    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 30))
    
    # Create two columns for better spacing
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    
    # Left buttons container
    left_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    left_buttons.grid(row=0, column=0, sticky="w")
    
    # Right buttons container
    right_buttons = StyleManager.create_frame(buttons_frame, fg_color="transparent")
    right_buttons.grid(row=0, column=1, sticky="e")
    
    # Left side buttons - operations
    refresh_btn = StyleManager.create_button(
        left_buttons,
        text="تحديث",
        width=120,
        command=lambda: refresh_treeview(tree, csv_manager)
    )
    refresh_btn.pack(side="left", padx=(0, 10), pady=10)
    
    history_btn = StyleManager.create_button(
        left_buttons,
        text="سجل الدفع",
        width=120,
        command=show_payment_history
    )
    history_btn.pack(side="left", padx=(0, 10), pady=10)

    export_btn = StyleManager.create_button(
        left_buttons,
        text="تصدير Excel",
        width=120,
        command=export_to_excel
    )
    export_btn.pack(side="left", padx=(0, 10), pady=10)
    
    # Right side buttons - customer management
    back_btn = StyleManager.create_button(
        right_buttons,
        text="العودة",
        style="secondary",
        width=120,
        command=lambda: show_frame(frames["home"])
    )
    back_btn.pack(side="right", padx=(0, 0), pady=10)
    
    delete_btn = StyleManager.create_button(
        right_buttons,
        text="حذف العميل",
        style="danger",
        width=120,
        command=delete_customer
    )
    delete_btn.pack(side="right", padx=(0, 10), pady=10)
    
    edit_btn = StyleManager.create_button(
        right_buttons,
        text="تعديل العميل",
        width=120,
        command=edit_customer
    )
    edit_btn.pack(side="right", padx=(0, 10), pady=10)

def setup_manage_installments_page():
    frame = frames["manage"]
    frame.grid_columnconfigure(0, weight=1)
    
