"""
Helper functions shared across the application.
"""
from tkinter import ttk, messagebox
from customtkinter import CTkToplevel, CTkTextbox, CTkCheckBox
import tkinter as tk
from datetime import datetime
import logging
import re
import os
import pandas as pd
from utils import StyleManager, CSVManager, DatePicker


def refresh_treeview(tree, csv_manager: CSVManager, data=None):
    """Refresh the treeview with data."""
    for item in tree.get_children():
        tree.delete(item)
        
    if data is None:
        data = csv_manager.read_data()
    
    columns = tree["columns"]
    
    for customer in data:
        values = []
        for col in columns:
            if col == "Paid":
                installment_dates = customer.get("Installment Dates", "").split(";")
                first_date = installment_dates[0] if installment_dates else ""
                paid_installments = eval(customer.get("Paid_Installments", "[]"))
                is_paid = first_date in paid_installments
                values.append("نعم" if is_paid else "لا")
            else:
                values.append(customer.get(col, ""))
        
        item = tree.insert("", "end", values=values)
        
        if "Paid" in columns:
            if values[columns.index("Paid")] == "نعم":
                tree.item(item, tags=("paid",))
            else:
                tree.item(item, tags=("unpaid",))
    
    if "Paid" in columns:
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])


def show_payment_history(app, frames, csv_manager: CSVManager, refresh_payment_history_views):
    """Show payment history for selected customer."""
    current_frame = None
    for frame in frames.values():
        if frame.winfo_ismapped():
            current_frame = frame
            break
            
    if not current_frame or not hasattr(current_frame, 'tree'):
        messagebox.showerror("خطأ", "لم يتم العثور على قائمة العملاء.")
        return
        
    tree = current_frame.tree
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showerror("خطأ", "يرجى تحديد عميل لعرض سجل المدفوعات.")
        return
        
    if len(selected_items) > 1:
        messagebox.showerror("خطأ", "يرجى تحديد عميل واحد فقط.")
        return
        
    try:
        item = selected_items[0]
        customer_name = tree.item(item)["values"][0]
        
        data = csv_manager.read_data()
        customer_data = None
        for customer in data:
            if customer["Name"] == customer_name:
                customer_data = customer
                break
                
        if not customer_data:
            messagebox.showerror("خطأ", "لم يتم العثور على بيانات العميل.")
            return
            
        history_window = CTkToplevel(app)
        history_window.geometry("800x760")
        history_window.title(f"سجل المدفوعات - {customer_name}")
        
        history_window.transient(app)
        history_window.grab_set()
        
        main_frame = StyleManager.create_frame(history_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        StyleManager.create_label(
            main_frame,
            text=f"سجل المدفوعات - {customer_name}",
            font_style="subheading"
        ).pack(pady=(0, 20))
        
        table_frame = StyleManager.create_frame(main_frame)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("Date", "Value", "Status", "Action")
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview"
        )
        
        column_widths = {
            "Date": 150,
            "Value": 150,
            "Status": 150,
            "Action": 150
        }
        
        column_headers = {
            "Date": "تاريخ القسط",
            "Value": "قيمة القسط",
            "Status": "الحالة",
            "Action": "إجراء"
        }
        
        for col in columns:
            tree.column(col, width=column_widths[col], anchor="center")
            tree.heading(col, text=column_headers[col])
            
        if customer_data:
            installment_dates = customer_data["Installment Dates"].split(";")
            default_value = float(customer_data["Installment Value"])
            paid_installments = eval(customer_data.get("Paid_Installments", "[]"))
            
            try:
                installment_values = eval(customer_data.get("Installment_Values", "{}"))
            except:
                installment_values = {}
            
            date_to_row_map = {}
            today = datetime.now().strftime("%Y-%m-%d")
            
            for date in installment_dates:
                is_paid = date in paid_installments
                status = "مدفوع" if is_paid else "غير مدفوع"
                status_tags = ("paid",) if is_paid else ("unpaid",)
                
                value = installment_values.get(date, default_value)
                
                is_future = date > today
                
                action = "" if is_paid else "تسجيل كمدفوع" if not is_future else "موعد مستقبلي"
                
                row_id = tree.insert("", "end", values=(date, f"{value:.2f}", status, action), tags=status_tags)
                date_to_row_map[date] = row_id
        
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(fill="both", expand=True)
        
        def mark_as_paid(event):
            try:
                item = tree.identify_row(event.y)
                if not item:
                    return
                    
                values = tree.item(item)["values"]
                date = values[0]
                
                if values[3] == "تسجيل كمدفوع":
                    if csv_manager.mark_installment_as_paid(customer_name, date):
                        tree.item(item, values=(date, values[1], "مدفوع", ""), tags=("paid",))
                        messagebox.showinfo("نجاح", "تم تسجيل القسط كمدفوع بنجاح.")
                    else:
                        messagebox.showerror("خطأ", "فشل في تسجيل القسط كمدفوع.")
                        
            except Exception as e:
                logging.error(f"Error marking installment as paid: {str(e)}")
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تسجيل القسط: {str(e)}")
                
        def edit_installment(event):
            try:
                item = tree.identify_row(event.y)
                if not item:
                    return
                    
                values = tree.item(item)["values"]
                date = values[0]
                value = values[1]
                is_paid = values[2] == "مدفوع"
                
                edit_window = CTkToplevel(history_window)
                edit_window.geometry("500x450")
                edit_window.title("تعديل القسط")
                
                edit_window.transient(history_window)
                edit_window.grab_set()
                
                main_frame = StyleManager.create_frame(edit_window)
                main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                StyleManager.create_label(
                    main_frame,
                    text="تعديل بيانات القسط",
                    font_style="subheading"
                ).pack(pady=(0, 20))
                
                info_frame = StyleManager.create_frame(main_frame)
                info_frame.pack(fill="x", pady=10)
                
                StyleManager.create_label(
                    info_frame,
                    text=f"العميل: {customer_name}",
                    font_style="body_bold"
                ).pack(anchor="w")
                
                fields_frame = StyleManager.create_frame(main_frame)
                fields_frame.pack(fill="x", pady=20)
                
                date_frame = StyleManager.create_frame(fields_frame)
                date_frame.pack(fill="x", pady=10)
                
                StyleManager.create_label(
                    date_frame,
                    text="تاريخ القسط:",
                    font_style="body"
                ).pack(side="left", padx=(0, 10))
                
                date_entry = StyleManager.create_entry(date_frame)
                date_entry.pack(side="left", fill="x", expand=True)
                date_entry.insert(0, date)
                
                def open_date_picker():
                    DatePicker(edit_window, date_entry)
                    
                date_picker_btn = StyleManager.create_button(
                    date_frame,
                    text="📅",
                    width=40,
                    command=open_date_picker
                )
                date_picker_btn.pack(side="left", padx=(10, 0))
                
                amount_frame = StyleManager.create_frame(fields_frame)
                amount_frame.pack(fill="x", pady=10)
                
                StyleManager.create_label(
                    amount_frame,
                    text="قيمة القسط:",
                    font_style="body"
                ).pack(side="left", padx=(0, 10))
                
                amount_entry = StyleManager.create_entry(amount_frame)
                amount_entry.pack(side="left", fill="x", expand=True)
                amount_entry.insert(0, str(value))
                
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
                
                buttons_frame = StyleManager.create_frame(main_frame)
                buttons_frame.pack(fill="x", pady=(20, 10))
                buttons_frame.grid_columnconfigure(0, weight=1)
                buttons_frame.grid_columnconfigure(1, weight=1)
                
                def save_changes():
                    try:
                        new_date = date_entry.get().strip()
                        new_value_str = amount_entry.get().strip()
                        new_paid_status = paid_status.get()
                        
                        try:
                            datetime.strptime(new_date, "%Y-%m-%d")
                        except ValueError:
                            messagebox.showerror("خطأ", "تنسيق التاريخ غير صحيح. يجب أن يكون بهذا الشكل: YYYY-MM-DD")
                            return
                        
                        if not re.match(r"^\d+(\.\d{1,2})?$", new_value_str):
                            messagebox.showerror("خطأ", "قيمة القسط يجب أن تكون رقمًا صالحًا.")
                            return
                            
                        new_value = float(new_value_str)
                        
                        if csv_manager.update_installment(customer_name, date, new_date, new_value):
                            if is_paid != new_paid_status:
                                if new_paid_status:
                                    csv_manager.mark_installment_as_paid(customer_name, new_date)
                                else:
                                    csv_manager.unmark_installment_as_paid(customer_name, new_date)
                                
                            messagebox.showinfo("نجاح", "تم تحديث بيانات القسط بنجاح.")
                            edit_window.destroy()
                            history_window.destroy()
                            show_payment_history(app, frames, csv_manager, refresh_payment_history_views)
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
        
        tree.bind("<Double-1>", mark_as_paid)
        tree.bind("<Button-3>", edit_installment)
        
        if customer_data:
            total_installments = len(installment_dates)
            paid_count = len(paid_installments)
            remaining_count = total_installments - paid_count
            
            total_amount = sum(float(installment_values.get(date, default_value)) for date in installment_dates)
            paid_amount = sum(float(installment_values.get(date, default_value)) for date in paid_installments)
            remaining_amount = total_amount - paid_amount
            
            summary_frame = StyleManager.create_frame(main_frame)
            summary_frame.pack(fill="x", padx=20, pady=(0, 20))
            
            StyleManager.create_label(
                summary_frame,
                text=f"عدد الأقساط المدفوعة: {paid_count} من {total_installments}",
                font_style="body_bold"
            ).pack(pady=5)
            
            StyleManager.create_label(
                summary_frame,
                text=f"المبلغ المدفوع: {paid_amount:.2f} من {total_amount:.2f} ({round(paid_amount/total_amount*100, 1)}%)",
                font_style="body_bold"
            ).pack(pady=5)
            
            StyleManager.create_label(
                summary_frame,
                text=f"المبلغ المتبقي: {remaining_amount:.2f}",
                font_style="body_bold"
            ).pack(pady=5)
        
        StyleManager.create_button(
            main_frame,
            text="إغلاق",
            style="secondary",
            width=200,
            command=history_window.destroy
        ).pack(side="bottom", pady=20)
        
    except Exception as e:
        logging.error(f"Error showing payment history: {str(e)}")
        messagebox.showerror("خطأ", f"حدث خطأ أثناء عرض سجل المدفوعات: {str(e)}")


def export_to_excel(csv_manager: CSVManager):
    """Export customer data to Excel file with enhanced formatting."""
    try:
        data = csv_manager.read_data()
        if not data:
            messagebox.showerror("خطأ", "لا توجد بيانات للتصدير.")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"customers_export_{timestamp}.xlsx"
        
        arabic_columns = {
            "Name": "اسم العميل",
            "Phone": "رقم الهاتف",
            "Amount": "المبلغ الإجمالي",
            "Installments": "عدد الأقساط",
            "Installment Value": "قيمة القسط",
            "Start Date": "تاريخ البدء",
            "Installment Dates": "تواريخ الأقساط",
            "Notification Sent": "تم الإرسال"
        }
        
        cleaned_data = []
        for row in data:
            cleaned_row = row.copy()
            cleaned_row["Notification Sent"] = "نعم" if row["Notification Sent"] else "لا"
            try:
                cleaned_row["Amount"] = float(row["Amount"])
                cleaned_row["Installment Value"] = float(row["Installment Value"])
                cleaned_row["Installments"] = int(row["Installments"])
            except (ValueError, TypeError):
                pass
            cleaned_data.append(cleaned_row)
        
        df = pd.DataFrame(cleaned_data)
        df = df.rename(columns=arabic_columns)
        
        with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='بيانات العملاء', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['بيانات العملاء']
            
            header_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'font_name': 'Arial',
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#2B7DE9',
                'font_color': 'white',
                'border': 2,
                'text_wrap': True,
                'border_color': '#1a5fb4'
            })
            
            cell_format = workbook.add_format({
                'font_size': 14,
                'font_name': 'Arial',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'text_wrap': True,
                'border_color': '#666666'
            })
            
            column_widths = {
                "اسم العميل": 25,
                "رقم الهاتف": 20,
                "المبلغ الإجمالي": 20,
                "عدد الأقساط": 15,
                "قيمة القسط": 20,
                "تاريخ البدء": 20,
                "تواريخ الأقساط": 40,
                "تم الإرسال": 15
            }
            
            for idx, col in enumerate(df.columns):
                if col in column_widths:
                    col_width = column_widths[col]
                else:
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    )
                    col_width = min(max(max_length + 4, 15), 50)
                
                worksheet.set_column(idx, idx, col_width)
                worksheet.write(0, idx, col, header_format)
                
                for row in range(1, len(df) + 1):
                    worksheet.write(row, idx, df.iloc[row-1][col], cell_format)
            
            for row_num in range(1, len(df) + 1):
                row_format = workbook.add_format({
                    'font_size': 14,
                    'font_name': 'Arial',
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1,
                    'border_color': '#666666',
                    'text_wrap': True,
                    'bg_color': '#F5F5F5' if row_num % 2 == 0 else 'white'
                })
                
                for col_num in range(len(df.columns)):
                    worksheet.write(row_num, col_num, df.iloc[row_num-1][df.columns[col_num]], row_format)
            
            worksheet.set_default_row(45)
            worksheet.set_row(0, 60)
            worksheet.freeze_panes(1, 0)
            worksheet.right_to_left()
        
        messagebox.showinfo("نجاح", f"تم تصدير البيانات إلى ملف Excel: {excel_filename}")
        os.startfile(os.path.abspath(excel_filename))
        
    except ImportError:
        messagebox.showerror("خطأ", "الرجاء التأكد من تثبيت حزمة xlsxwriter")
        logging.error("xlsxwriter package not installed")
    except Exception as e:
        logging.error(f"Error exporting to Excel: {str(e)}")
        messagebox.showerror("خطأ", "حدث خطأ أثناء تصدير البيانات.")


def refresh_payment_history_views(app):
    """Refresh all open payment history windows."""
    for widget in app.winfo_children():
        if isinstance(widget, CTkToplevel) and "سجل المدفوعات" in widget.title():
            widget.destroy()

