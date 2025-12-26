from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkToplevel, CTkTextbox, CTkCheckBox, CTkScrollableFrame, CTkRadioButton
from tkinter import ttk, messagebox, filedialog, StringVar, BooleanVar
import tkinter as tk
import os
import re
import logging
from datetime import datetime, timedelta
from utils import StyleManager, CSVManager, FileManager, DatePicker
from helpers import refresh_treeview, show_payment_history, export_to_excel, refresh_payment_history_views


def setup_manage_installments_page(frame, frames, show_frame, app, csv_manager):
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="إدارة الأقساط",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))
    
    StyleManager.create_label(
        header_frame,
        text="متابعة وإدارة الأقساط والمدفوعات",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))
    
    # Create table container
    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)
    
    # Create a Treeview widget with modern styling
    columns = ("Name", "Phone", "Installment Date", "Installment Value", "Paid")
    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="Custom.Treeview"
    )
    
    # Set column widths and headings
    column_widths = {
        "Name": 150,
        "Phone": 120,
        "Installment Date": 120,
        "Installment Value": 120,
        "Paid": 100
    }
    
    column_headers = {
        "Name": "اسم العميل",
        "Phone": "رقم الهاتف",
        "Installment Date": "تاريخ القسط",
        "Installment Value": "قيمة القسط",
        "Paid": "مدفوع"
    }
    
    for col in columns:
        tree.column(col, width=column_widths[col], anchor="center")
        tree.heading(col, text=column_headers[col])
    
    tree.grid(row=0, column=0, sticky="nsew")
    
    # Add modern scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)
    
    # Store the Treeview widget as an attribute of the frame
    frame.tree = tree
    
    # Load data into the Treeview
    def load_data():
        try:
            # Clear existing items
            for row in tree.get_children():
                tree.delete(row)
                
            data = csv_manager.read_data()
            today = datetime.now().date()
            
            # Group installments by customer
            customer_installments = {}
            
            for customer in data:
                customer_name = customer["Name"]
                customer_phone = customer["Phone"]
                installment_dates = customer["Installment Dates"].split(";")
                paid_installments = eval(customer.get("Paid_Installments", "[]"))
                
                # Get individual installment values
                try:
                    installment_values = eval(customer.get("Installment_Values", "{}"))
                    if not isinstance(installment_values, dict):
                        installment_values = {}
                except:
                    installment_values = {}
                
                # Create customer group
                if customer_name not in customer_installments:
                    customer_installments[customer_name] = {
                        "phone": customer_phone,
                        "installments": []
                    }
                
                # Add installments to customer group
                for date in installment_dates:
                    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                    is_paid = date in paid_installments
                    value = installment_values.get(date, customer["Installment Value"])
                    
                    customer_installments[customer_name]["installments"].append({
                        "date": date_obj,
                        "date_str": date,
                        "value": value,
                        "is_paid": is_paid
                    })
            
            # Sort customers by name
            sorted_customers = sorted(customer_installments.items())
            
            # Insert into tree
            for customer_name, customer_data in sorted_customers:
                # Sort installments by date
                installments = sorted(customer_data["installments"], key=lambda x: x["date"])
                
                # Calculate payment summary
                total_installments = len(installments)
                paid_count = sum(1 for i in installments if i["is_paid"])
                payment_status = f"مدفوع: {paid_count}/{total_installments}"
                
                # Insert customer header with arrow and payment status
                header_item = tree.insert("", "end", values=(
                    f"▼ {customer_name}",  # Add arrow to indicate expandable
                    customer_data["phone"],
                    payment_status,  # Show payment status in date column
                    "",  # Empty value
                    ""   # Empty paid status
                ), tags=("header",))
                
                # Insert installments under header
                for installment in installments:
                    values = (
                        "",  # Empty name (will be indented)
                        "",  # Empty phone
                        installment["date_str"],
                        installment["value"],
                        "نعم" if installment["is_paid"] else "لا"
                    )
                    
                    item = tree.insert(header_item, "end", values=values)
                    
                    # Add tag for paid/unpaid status
                    if installment["is_paid"]:
                        tree.item(item, tags=("paid",))
                    else:
                        tree.item(item, tags=("unpaid",))
                
                # Initially collapse the customer's installments
                tree.item(header_item, open=False)
            
            # Configure styles
            tree.tag_configure("header", 
                background=StyleManager.COLORS["surface"],
                font=StyleManager.FONTS["body_bold"]
            )
            tree.tag_configure("paid", 
                foreground=StyleManager.COLORS["success"],
                font=StyleManager.FONTS["body"]
            )
            tree.tag_configure("unpaid", 
                foreground=StyleManager.COLORS["danger"],
                font=StyleManager.FONTS["body"]
            )
            
            # Add click handler for headers
            def on_header_click(event):
                item = tree.identify_row(event.y)
                if item and "header" in tree.item(item)["tags"]:
                    # Toggle the arrow direction
                    values = list(tree.item(item)["values"])
                    if values[0].startswith("▼"):
                        values[0] = values[0].replace("▼", "▶")
                        tree.item(item, open=False)
                    else:
                        values[0] = values[0].replace("▶", "▼")
                        tree.item(item, open=True)
                    tree.item(item, values=values)
            
            tree.bind("<Button-1>", on_header_click)
            
        except Exception as e:
            logging.error(f"Error loading installments data: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء تحميل البيانات.")
    
    # Initial data load
    load_data()
    
    # Buttons Container
    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    buttons_frame.grid_columnconfigure(2, weight=1)
    
    # Refresh button
    def refresh_installments():
        load_data()
        messagebox.showinfo("نجاح", "تم تحديث البيانات بنجاح.")
    
    StyleManager.create_button(
        buttons_frame,
        text="تحديث البيانات",
        width=200,
        command=refresh_installments
    ).grid(row=0, column=0, padx=10, pady=10)
    
    # Mark as paid button
    def mark_as_paid():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد قسط لتمييزه كمُدفوع.")
            return
        
        try:
            for item in selected_items:
                # Skip if header item is selected
                if "header" in tree.item(item)["tags"]:
                    continue
                    
                values = tree.item(item)["values"]
                parent = tree.parent(item)
                customer_name = tree.item(parent)["values"][0].replace("▼ ", "").replace("▶ ", "")
                installment_date = values[2]
                
                if csv_manager.mark_installment_as_paid(customer_name, installment_date):
                    tree.set(item, "Paid", "نعم")
                    tree.item(item, tags=("paid",))
                else:
                    messagebox.showerror("خطأ", f"فشل في تمييز القسط كمدفوع للعميل {customer_name}")
                    return
            
            messagebox.showinfo("نجاح", "تم تمييز الأقساط المحددة كمُدفوعة.")
            load_data()  # Refresh the view to ensure consistency
            
            # Refresh other relevant views if they exist
            if "view" in frames:
                refresh_treeview(frames["view"].tree, csv_manager)
                
        except Exception as e:
            logging.error(f"Error marking installments as paid: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء تمييز الأقساط كمدفوعة.")
    
    StyleManager.create_button(
        buttons_frame,
        text="تمييز كمُدفوع",
        width=200,
        command=mark_as_paid
    ).grid(row=0, column=1, padx=10, pady=10)
    
    # Edit installment button
    def edit_installment():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("خطأ", "يرجى تحديد قسط للتعديل.")
            return
        
        if len(selected_items) > 1:
            messagebox.showerror("خطأ", "يرجى تحديد قسط واحد فقط للتعديل.")
            return
            
        try:
            item = selected_items[0]
            # Skip if header item is selected
            if "header" in tree.item(item)["tags"]:
                messagebox.showerror("خطأ", "يرجى تحديد قسط للتعديل.")
                return
                
            values = tree.item(item)["values"]
            parent = tree.parent(item)
            customer_name = tree.item(parent)["values"][0].replace("▼ ", "").replace("▶ ", "")
            customer_phone = tree.item(parent)["values"][1]
            installment_date = values[2]
            installment_value = values[3]
            is_paid = values[4] == "نعم"
            
            # Create edit installment window
            edit_window = CTkToplevel(app)
            edit_window.geometry("500x450")
            edit_window.title("تعديل القسط")
            
            # Make window modal
            edit_window.transient(app)
            edit_window.grab_set()
            
            # Create main frame
            main_frame = StyleManager.create_frame(edit_window)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Add title
            StyleManager.create_label(
                main_frame,
                text="تعديل بيانات القسط",
                font_style="subheading"
            ).pack(pady=(0, 20))
            
            # Customer info (non-editable)
            info_frame = StyleManager.create_frame(main_frame)
            info_frame.pack(fill="x", pady=10)
            
            StyleManager.create_label(
                info_frame,
                text=f"العميل: {customer_name}",
                font_style="body_bold"
            ).pack(anchor="w")
            
            StyleManager.create_label(
                info_frame,
                text=f"رقم الهاتف: {customer_phone}",
                font_style="body"
            ).pack(anchor="w")
            
            # Editable fields
            fields_frame = StyleManager.create_frame(main_frame)
            fields_frame.pack(fill="x", pady=20)
            
            # Date field
            date_frame = StyleManager.create_frame(fields_frame)
            date_frame.pack(fill="x", pady=10)
            
            StyleManager.create_label(
                date_frame,
                text="تاريخ القسط:",
                font_style="body"
            ).pack(side="left", padx=(0, 10))
            
            date_entry = StyleManager.create_entry(date_frame)
            date_entry.pack(side="left", fill="x", expand=True)
            date_entry.insert(0, installment_date)
            
            # Date picker button
            def open_date_picker():
                DatePicker(edit_window, date_entry)
                
            date_picker_btn = StyleManager.create_button(
                date_frame,
                text="📅",
                width=40,
                command=open_date_picker
            )
            date_picker_btn.pack(side="left", padx=(10, 0))
            
            # Amount field
            amount_frame = StyleManager.create_frame(fields_frame)
            amount_frame.pack(fill="x", pady=10)
            
            StyleManager.create_label(
                amount_frame,
                text="قيمة القسط:",
                font_style="body"
            ).pack(side="left", padx=(0, 10))
            
            amount_entry = StyleManager.create_entry(amount_frame)
            amount_entry.pack(side="left", fill="x", expand=True)
            amount_entry.insert(0, str(installment_value))
            
            # Paid status
            paid_frame = StyleManager.create_frame(fields_frame)
            paid_frame.pack(fill="x", pady=10)
            
            paid_status = tk.BooleanVar(value=is_paid)
            
            paid_checkbox = CTkCheckBox(
                paid_frame,
                text="مدفوع",
                variable=paid_status,
                onvalue=True,
                offvalue=False,
                checkbox_width=24,
                checkbox_height=24,
                corner_radius=5,
                border_width=2,
                fg_color=StyleManager.COLORS["primary"],
                hover_color=StyleManager.COLORS["secondary"],
                checkmark_color=StyleManager.COLORS["text"]
            )
            paid_checkbox.pack(anchor="w")
            
            # Action buttons
            buttons_frame = StyleManager.create_frame(main_frame)
            buttons_frame.pack(fill="x", pady=(20, 10))
            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)
            
            # Save changes
            def save_changes():
                try:
                    new_date = date_entry.get().strip()
                    new_value_str = amount_entry.get().strip()
                    new_paid_status = paid_status.get()
                    
                    # Validate date format
                    try:
                        datetime.strptime(new_date, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showerror("خطأ", "تنسيق التاريخ غير صحيح. يجب أن يكون بهذا الشكل: YYYY-MM-DD")
                        return
                    
                    # Validate amount
                    if not re.match(r"^\d+(\.\d{1,2})?$", new_value_str):
                        messagebox.showerror("خطأ", "قيمة القسط يجب أن تكون رقمًا صالحًا.")
                        return
                        
                    new_value = float(new_value_str)
                    
                    # Update installment in database
                    if csv_manager.update_installment(customer_name, installment_date, new_date, new_value):
                        # Update paid status if needed
                        if is_paid != new_paid_status:
                            if new_paid_status:
                                csv_manager.mark_installment_as_paid(customer_name, new_date)
                            else:
                                csv_manager.unmark_installment_as_paid(customer_name, new_date)
                            
                        messagebox.showinfo("نجاح", "تم تحديث بيانات القسط بنجاح.")
                        edit_window.destroy()
                        load_data()  # Refresh the view
                        refresh_payment_history_views(app)  # Refresh payment history views
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات القسط.")
                        
                except Exception as e:
                    logging.error(f"Error saving installment changes: {str(e)}")
                    messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ التغييرات: {str(e)}")
            
            StyleManager.create_button(
                buttons_frame,
                text="حفظ التغييرات",
                width=200,
                command=save_changes
            ).grid(row=0, column=0, padx=5, pady=5)
            
            # Cancel button
            StyleManager.create_button(
                buttons_frame,
                text="إلغاء",
                width=200,
                style="secondary",
                command=edit_window.destroy
            ).grid(row=0, column=1, padx=5, pady=5)
            
        except Exception as e:
            logging.error(f"Error opening edit installment window: {str(e)}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء فتح نافذة التعديل: {str(e)}")
    
    StyleManager.create_button(
        buttons_frame,
        text="تعديل القسط",
        width=200,
        command=edit_installment
    ).grid(row=0, column=2, padx=10, pady=10)
    
    # Back button
    StyleManager.create_button(
        buttons_frame,
        text="العودة",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=3, padx=10, pady=10)

def setup_backup_restore_page():
    frame = frames["backup_restore"]
    frame.grid_columnconfigure(0, weight=1)
    
