from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkToplevel, CTkTextbox, CTkCheckBox, CTkScrollableFrame, CTkRadioButton
from tkinter import ttk, messagebox, filedialog, StringVar, BooleanVar
import tkinter as tk
import os
import re
import logging
from datetime import datetime, timedelta
from utils import StyleManager, CSVManager, FileManager, DatePicker
from helpers import refresh_treeview, show_payment_history, export_to_excel, refresh_payment_history_views


def setup_send_notification_page(frame, frames, show_frame, app, csv_manager):
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="إرسال إشعارات الواتساب",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))
    
    StyleManager.create_label(
        header_frame,
        text="إرسال تذكيرات الأقساط للعملاء عبر الواتساب",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))
    
    # Create table container
    table_frame = StyleManager.create_frame(frame)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    table_frame.grid_columnconfigure(0, weight=1)
    table_frame.grid_rowconfigure(0, weight=1)
    
    # Create a Treeview widget with modern styling
    columns = ("Name", "Phone", "Installment Date", "Installment Value")
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
        "Installment Value": 120
    }
    
    column_headers = {
        "Name": "اسم العميل",
        "Phone": "رقم الهاتف",
        "Installment Date": "تاريخ القسط",
        "Installment Value": "قيمة القسط"
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
        for row in tree.get_children():
            tree.delete(row)
            
        data = csv_manager.read_data()
        today = datetime.now().date()
        
        for customer in data:
            installment_dates = customer["Installment Dates"].split(";")
            for date in installment_dates:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                # Only show upcoming installments
                if date_obj >= today:
                    values = (
                        customer["Name"],
                        customer["Phone"],
                        date,
                        customer["Installment Value"]
                    )
                    tree.insert("", "end", values=values)
        
        # Configure sent notification style
        tree.tag_configure("sent", foreground=StyleManager.COLORS["success"])
    
    load_data()
    
    # Buttons Container
    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    buttons_frame.grid_columnconfigure(2, weight=1)
    
    # Send WhatsApp Notification Button
    def send_whatsapp_notification():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد عميل لإرسال الإشعار.")
            return
            
        item = tree.item(selected_item[0])  # Get the first selected item
        values = item["values"]
        name = values[0]
        phone = str(values[1])
        installment_date = values[2]
        installment_value = values[3]
        
        # Format phone number
        if not phone.startswith("+"):
            phone = "+" + phone
        
        # Show preview window
        preview_window = CTkToplevel(app)
        preview_window.geometry("500x550")
        preview_window.title("معاينة الرسالة")
        
        # Add header
        StyleManager.create_label(
            preview_window,
            text="معاينة رسالة الواتساب",
            font_style="heading"
        ).pack(pady=(20, 10))
        
        # Default message template
        default_message =  (
         f"مرحبًا {name},\n"
            f"هذه الرسالة مجرد تذكير لدفع الالتزام الخاص بك على حساب الشركة :\n"
            f"QA80QISB000000000155537130012\n"
            f"شكرًا لتعاملك مع شركة الحلول المتطورة للتجارة""."
        )
        
        # Message customization section
        customization_frame = StyleManager.create_frame(preview_window)
        customization_frame.pack(fill="x", padx=20, pady=10)
        
        StyleManager.create_label(
            customization_frame,
            text="نص الرسالة:",
            font_style="body_bold"
        ).pack(anchor="w", pady=(5, 0))
        
        message_text = CTkTextbox(
            customization_frame,
            width=400,
            height=150,
            font=StyleManager.FONTS["body"]
        )
        message_text.pack(pady=10, padx=10, fill="both", expand=True)
        message_text.insert("end", default_message)
        
        # Template variables info
        template_info = StyleManager.create_frame(preview_window)
        template_info.pack(fill="x", padx=20, pady=5)
        
        StyleManager.create_label(
            template_info,
            text="يمكنك استخدام المتغيرات التالية في الرسالة:",
            font_style="small"
        ).pack(anchor="w")
        
        StyleManager.create_label(
            template_info,
            text=  (
         f"مرحبًا {name},\n"
            f"هذه الرسالة مجرد تذكير لدفع الالتزام الخاص بك على حساب الشركة :\n"
            f"QA80QISB000000000155537130012\n"
            f"شكرًا لتعاملك مع شركة الحلول المتطورة للتجارة""."
        ),
            font_style="small",
            text_color=StyleManager.COLORS["text_secondary"]
        ).pack(anchor="w")
        
        # Message sending options frame
        options_frame = StyleManager.create_frame(preview_window)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        # Add a checkbox for retrying if failed
        retry_var = BooleanVar(value=True)
        retry_check = CTkCheckBox(
            options_frame, 
            text="محاولة الإرسال مرة أخرى في حالة الفشل",
            variable=retry_var
        )
        retry_check.pack(anchor="w", pady=5)
        
        # Max retry count
        retry_count_frame = StyleManager.create_frame(options_frame)
        retry_count_frame.pack(fill="x", pady=5)
        
        StyleManager.create_label(
            retry_count_frame,
            text="عدد المحاولات:",
            font_style="body"
        ).pack(side="left", padx=(0, 10))
        
        retry_count_var = StringVar(value="3")
        retry_count_entry = StyleManager.create_entry(
            retry_count_frame,
            width=50,
            textvariable=retry_count_var
        )
        retry_count_entry.pack(side="left")
        
        # Buttons frame
        buttons_frame = StyleManager.create_frame(preview_window)
        buttons_frame.pack(fill="x", padx=20, pady=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Status label for showing sending progress
        status_label = StyleManager.create_label(
            preview_window,
            text="",
            font_style="small",
            text_color=StyleManager.COLORS["text_secondary"]
        )
        status_label.pack(pady=(0, 10))
        
        def send_message():
            try:
                # Get customized message
                custom_message = message_text.get("1.0", "end-1c")
                
                # Apply template variables
                message = custom_message.replace("{name}", name).replace("{date}", installment_date).replace("{value}", str(installment_value))
                
                # Get retry settings
                should_retry = retry_var.get()
                max_retries = 1
                try:
                    max_retries = int(retry_count_var.get())
                    if max_retries < 1:
                        max_retries = 1
                except ValueError:
                    max_retries = 3
                
                # Disable buttons during sending
                for widget in buttons_frame.winfo_children():
                    widget.configure(state="disabled")
                
                # Initialize retry variables
                attempts = 0
                success = False
                window_exists = True
                errors = []
                
                while attempts < max_retries and not success and window_exists:
                    attempts += 1
                    try:
                        # Check if window still exists
                        try:
                            # Update status only if window exists
                            if window_exists:
                                status_label.configure(text=f"جاري إرسال الرسالة... المحاولة {attempts}/{max_retries}")
                                preview_window.update()
                        except (TclError, RuntimeError):
                            window_exists = False
                            logging.warning("Preview window was closed during operation")
                            break
                        
                        # Send WhatsApp message with error handling
                        try:
                            kit.sendwhatmsg_instantly(
                                phone_no=phone,
                                message=message,
                                wait_time=15,  # Increased wait time to 15 seconds
                                tab_close=True,
                                close_time=10  # Increased close time to 10 seconds
                            )
                        except Exception as e:
                            raise Exception(f"فشل في إرسال الرسالة: {str(e)}")
                        
                        # Update notification status
                        data = csv_manager.read_data()
                        updated = False
                        for customer in data:
                            if customer["Name"] == name:
                                customer["Notification Sent"] = True
                                updated = True
                                break
                        
                        if updated and csv_manager.save_data(data):
                            success = True
                            
                            # Check if window still exists before updating it
                            try:
                                if window_exists:
                                    status_label.configure(text="تم الإرسال بنجاح!")
                                    messagebox.showinfo("نجاح", f"تم إرسال الإشعار إلى {name} بنجاح.")
                                    preview_window.destroy()
                                    window_exists = False
                            except (TclError, RuntimeError):
                                window_exists = False
                                
                            load_data()  # Refresh the view
                            logging.info(f"Manual notification sent to {name} at {phone}")
                        else:
                            errors.append("فشل في تحديث حالة الإشعار")
                    
                    except Exception as e:
                        errors.append(str(e))
                        logging.error(f"Error in send_message attempt {attempts}: {str(e)}")
                        
                        # Wait before retry if needed
                        if attempts < max_retries and should_retry:
                            time.sleep(5)
                
                if not success:
                    error_message = "\n".join(errors)
                    messagebox.showerror("خطأ", f"فشل في إرسال الإشعار:\n{error_message}")
                    logging.error(f"Failed to send notification to {name} after {max_retries} attempts")
                
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
                logging.error(f"Unexpected error in send_message: {str(e)}")
                # Re-enable buttons if window still exists
                try:
                    for widget in buttons_frame.winfo_children():
                        widget.configure(state="normal")
                except (TclError, RuntimeError):
                    pass
        
        # Send button
        StyleManager.create_button(
            buttons_frame,
            text="إرسال",
            width=200,
            command=send_message
        ).grid(row=0, column=0, padx=10)
        
        # Cancel button
        StyleManager.create_button(
            buttons_frame,
            text="إلغاء",
            style="secondary",
            width=200,
            command=preview_window.destroy
        ).grid(row=0, column=1, padx=10)
    
    # Refresh button
    StyleManager.create_button(
        buttons_frame,
        text="تحديث البيانات",
        width=200,
        command=load_data
    ).grid(row=0, column=0, padx=10, pady=10)
    
    # Send notification button
    StyleManager.create_button(
        buttons_frame,
        text="إرسال إشعار",
        width=200,
        command=send_whatsapp_notification
    ).grid(row=0, column=1, padx=10, pady=10)
    
    # Back button
    StyleManager.create_button(
        buttons_frame,
        text="العودة",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=2, padx=10, pady=10)

