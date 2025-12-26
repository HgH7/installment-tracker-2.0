"""
Utility classes and functions for the Installment Tracker application.
"""
import customtkinter
from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkToplevel
from tkinter import ttk, messagebox
import os
import csv
import re
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Optional
from tkcalendar import Calendar


class StyleManager:
    """Manages application-wide styling"""
    
    # Color scheme
    COLORS = {
        "primary": "#2B7DE9",
        "secondary": "#23B0FF",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "background": "#1a1a1a",
        "surface": "#2d2d2d",
        "text": "#ffffff",
        "text_secondary": "#b3b3b3",
        "border": "#404040"
    }
    
    # Font configurations
    FONTS = {
        "heading": ("Arial", 24, "bold"),
        "subheading": ("Arial", 18, "bold"),
        "body": ("Arial", 14),
        "body_bold": ("Arial", 14, "bold"),
        "small": ("Arial", 12),
        "button": ("Arial", 16, "bold")
    }
    
    # Button styles
    BUTTON_STYLES = {
        "primary": {
            "fg_color": COLORS["primary"],
            "hover_color": COLORS["secondary"],
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 0,
            "height": 45
        },
        "secondary": {
            "fg_color": "transparent",
            "hover_color": COLORS["surface"],
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 2,
            "border_color": COLORS["primary"],
            "height": 45
        },
        "danger": {
            "fg_color": COLORS["danger"],
            "hover_color": "#c82333",
            "text_color": COLORS["text"],
            "font": ("Arial", 18, "bold"),
            "corner_radius": 12,
            "border_width": 0,
            "height": 45
        }
    }
    
    @classmethod
    def setup_theme(cls):
        """Configure the global theme settings"""
        try:
            customtkinter.set_appearance_mode("dark")
            customtkinter.set_default_color_theme("blue")
            
            # Configure ttk styles for Treeview
            style = ttk.Style()
            style.theme_use('default')
            
            # Configure Treeview colors
            style.configure("Treeview",
                background=cls.COLORS["surface"],
                foreground=cls.COLORS["text"],
                fieldbackground=cls.COLORS["surface"],
                font=cls.FONTS["body"]
            )
            
            # Configure Treeview selected items
            style.map('Treeview',
                background=[('selected', cls.COLORS["primary"])],
                foreground=[('selected', cls.COLORS["text"])]
            )
            
            # Configure Treeview headers
            style.configure("Treeview.Heading",
                background=cls.COLORS["primary"],
                foreground=cls.COLORS["text"],
                font=cls.FONTS["body_bold"]
            )
            
            logging.info("Theme setup completed successfully")
        except Exception as e:
            logging.error(f"Error setting up theme: {str(e)}")
            raise
    
    @classmethod
    def create_frame(cls, master, **kwargs) -> CTkFrame:
        """Create a styled frame"""
        try:
            frame_config = {
                "corner_radius": 15,
                "border_width": 0
            }
            
            if "fg_color" not in kwargs:
                frame_config["fg_color"] = cls.COLORS["surface"]
            
            frame_config.update(kwargs)
            
            return CTkFrame(master, **frame_config)
        except Exception as e:
            logging.error(f"Error creating frame: {str(e)}")
            raise
    
    @classmethod
    def create_button(cls, master, text: str, style: str = "primary", **kwargs) -> CTkButton:
        """Create a styled button"""
        try:
            button_style = cls.BUTTON_STYLES[style].copy()
            button_style.update(kwargs)
            return CTkButton(master, text=text, **button_style)
        except Exception as e:
            logging.error(f"Error creating button: {str(e)}")
            raise
    
    @classmethod
    def create_label(cls, master, text: str, font_style: str = "body", **kwargs) -> CTkLabel:
        """Create a styled label"""
        try:
            if 'text_color' not in kwargs:
                kwargs['text_color'] = cls.COLORS["text"]
            if 'font' not in kwargs:
                kwargs['font'] = cls.FONTS[font_style]
                
            return CTkLabel(master, text=text, **kwargs)
        except Exception as e:
            logging.error(f"Error creating label: {str(e)}")
            raise
    
    @classmethod
    def create_entry(cls, master, **kwargs) -> CTkEntry:
        """Create a styled entry"""
        try:
            entry_config = {
                "fg_color": cls.COLORS["background"],
                "text_color": cls.COLORS["text"],
                "border_color": cls.COLORS["primary"],
                "corner_radius": 8
            }
            
            if 'font' not in kwargs:
                entry_config['font'] = cls.FONTS["body"]
                
            entry_config.update(kwargs)
            
            return CTkEntry(master, **entry_config)
        except Exception as e:
            logging.error(f"Error creating entry: {str(e)}")
            raise


class FileManager:
    """Handles all file operations for customer documents"""
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self._ensure_base_directory()
        
    def _ensure_base_directory(self):
        """Ensure the base directory exists"""
        try:
            if not os.path.exists(self.base_dir):
                os.makedirs(self.base_dir)
                logging.info(f"Created base directory: {self.base_dir}")
        except Exception as e:
            logging.error(f"Error creating base directory: {str(e)}")
            raise
            
    def _get_customer_dir(self, customer_name: str) -> str:
        """Get the directory path for a customer's files"""
        safe_name = "".join(c for c in customer_name if c.isalnum() or c in (' ', '-', '_')).strip()
        customer_dir = os.path.join(self.base_dir, safe_name)
        
        if not os.path.exists(customer_dir):
            os.makedirs(customer_dir)
            logging.info(f"Created customer directory: {customer_dir}")
            
        return customer_dir
        
    def add_files(self, customer_name: str, files: List[str]) -> bool:
        """Add files for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            
            if not os.path.exists(customer_dir):
                os.makedirs(customer_dir)
                logging.info(f"Created directory for customer {customer_name}")
            
            success = True
            
            for file_path in files:
                try:
                    file_name = os.path.basename(file_path)
                    safe_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '-', '_')).strip()
                    
                    base, ext = os.path.splitext(safe_name)
                    counter = 1
                    while os.path.exists(os.path.join(customer_dir, safe_name)):
                        safe_name = f"{base}_{counter}{ext}"
                        counter += 1
                    
                    dest_path = os.path.join(customer_dir, safe_name)
                    shutil.copy2(file_path, dest_path)
                    logging.info(f"Added file {safe_name} for customer {customer_name}")
                    
                except Exception as e:
                    logging.error(f"Error adding file {file_path} for customer {customer_name}: {str(e)}")
                    success = False
                    
            return success
            
        except Exception as e:
            logging.error(f"Error in add_files for customer {customer_name}: {str(e)}")
            return False
            
    def get_files(self, customer_name: str) -> List[str]:
        """Get list of files for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            if not os.path.exists(customer_dir):
                return []
                
            return [f for f in os.listdir(customer_dir) if os.path.isfile(os.path.join(customer_dir, f))]
            
        except Exception as e:
            logging.error(f"Error getting files for customer {customer_name}: {str(e)}")
            return []
            
    def delete_file(self, customer_name: str, file_name: str) -> bool:
        """Delete a specific file for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            file_path = os.path.join(customer_dir, file_name)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Deleted file {file_name} for customer {customer_name}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error deleting file {file_name} for customer {customer_name}: {str(e)}")
            return False
            
    def delete_customer_files(self, customer_name: str) -> bool:
        """Delete all files for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            if os.path.exists(customer_dir):
                shutil.rmtree(customer_dir)
                logging.info(f"Deleted all files for customer {customer_name}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error deleting files for customer {customer_name}: {str(e)}")
            return False
            
    def open_file(self, customer_name: str, file_name: str) -> bool:
        """Open a file using the system's default application"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            file_path = os.path.join(customer_dir, file_name)
            
            if os.path.exists(file_path):
                os.startfile(file_path)
                logging.info(f"Opened file {file_name} for customer {customer_name}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error opening file {file_name} for customer {customer_name}: {str(e)}")
            return False


class CSVManager:
    """Handles all CSV file operations with caching and optimized data handling"""
    def __init__(self, csv_file: str, backup_folder: str):
        self.csv_file = csv_file
        self.backup_folder = backup_folder
        self.columns = ["Name", "Phone", "Amount", "Installments", 
                       "Installment Value", "Start Date", "Installment Dates", 
                       "Notification Sent", "Paid_Installments", "Notified_Installments",
                       "Installment_Values"]
        self._cache = {}
        self._cache_timestamp = None
        self._cache_duration = 60
        self._ensure_files_exist()
        
    def _is_cache_valid(self) -> bool:
        """Check if cache is valid"""
        if not self._cache or not self._cache_timestamp:
            return False
        return (datetime.now() - self._cache_timestamp).seconds < self._cache_duration
        
    def _update_cache(self, data: List[Dict]):
        """Update cache with new data"""
        self._cache = data
        self._cache_timestamp = datetime.now()
        
    def read_data(self) -> List[Dict]:
        """Read data from CSV file with caching"""
        try:
            if self._is_cache_valid():
                return self._cache.copy()
                
            data = []
            with open(self.csv_file, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    cleaned_row = self._clean_row_data(row)
                    if "Notified_Installments" not in cleaned_row:
                        cleaned_row["Notified_Installments"] = "[]"
                    data.append(cleaned_row)
                    
            self._update_cache(data)
            return data
        except FileNotFoundError:
            logging.error(f"CSV file not found: {self.csv_file}")
            self._create_empty_csv()
            return []
        except Exception as e:
            logging.error(f"Error reading CSV file: {str(e)}")
            return []
            
    def _clean_row_data(self, row: Dict) -> Dict:
        """Clean and validate row data"""
        cleaned_row = row.copy()
        
        if "Phone" in cleaned_row:
            cleaned_row["Phone"] = f"+{cleaned_row['Phone']}" if not cleaned_row['Phone'].startswith("+") else cleaned_row['Phone']
            
        try:
            cleaned_row["Amount"] = float(cleaned_row.get("Amount", 0))
            cleaned_row["Installment Value"] = float(cleaned_row.get("Installment Value", 0))
            cleaned_row["Installments"] = int(cleaned_row.get("Installments", 0))
        except (ValueError, TypeError):
            logging.warning(f"Invalid numeric values in row: {row}")
            
        cleaned_row["Notification Sent"] = str(cleaned_row.get("Notification Sent", "")).lower() == "true"
        
        if "Paid_Installments" not in cleaned_row:
            cleaned_row["Paid_Installments"] = "[]"
            
        if "Notified_Installments" not in cleaned_row:
            cleaned_row["Notified_Installments"] = "[]"
            
        return cleaned_row
        
    def save_data(self, data: List[Dict]) -> bool:
        """Save data to CSV file with backup"""
        try:
            validated_data = []
            for row in data:
                if self._validate_row(row):
                    validated_data.append(row)
                else:
                    logging.warning(f"Invalid row data skipped: {row}")
            
            self.create_backup()
            
            with open(self.csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.columns)
                writer.writeheader()
                writer.writerows(validated_data)
                
            self._update_cache(validated_data)
            return True
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            return False
            
    def _validate_row(self, row: Dict) -> bool:
        """Validate row data"""
        required_fields = ["Name", "Phone", "Amount", "Installments"]
        
        if not all(field in row for field in required_fields):
            return False
            
        try:
            float(row["Amount"])
            float(row["Installment Value"])
            int(row["Installments"])
        except (ValueError, TypeError):
            return False
            
        phone_pattern = r"^\+?\d{10,15}$"
        if not re.match(phone_pattern, str(row["Phone"])):
            return False
            
        if "Notification Sent" not in row:
            row["Notification Sent"] = False
        if "Paid_Installments" not in row:
            row["Paid_Installments"] = "[]"
        if "Notified_Installments" not in row:
            row["Notified_Installments"] = "[]"
            
        return True
    
    def _ensure_files_exist(self):
        """Ensure necessary files and folders exist."""
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
                
            if not os.path.exists(self.csv_file):
                self._create_empty_csv()
                
        except Exception as e:
            logging.error(f"Error ensuring files exist: {str(e)}")
            raise
            
    def _create_empty_csv(self):
        """Create empty CSV file with headers."""
        try:
            with open(self.csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(self.columns)
        except Exception as e:
            logging.error(f"Error creating empty CSV: {str(e)}")
            raise
            
    def append_customer(self, customer_data: Dict) -> bool:
        """Append a new customer to the CSV file."""
        try:
            missing_fields = [field for field in self.columns if field not in customer_data]
            if missing_fields:
                logging.error(f"Missing required fields: {missing_fields}")
                messagebox.showerror("خطأ", f"الحقول التالية مطلوبة: {', '.join(missing_fields)}")
                return False
            
            if not self.create_backup():
                logging.error("Failed to create backup before appending customer")
                messagebox.showerror("خطأ", "فشل في إنشاء نسخة احتياطية")
                return False
            
            file_exists = os.path.exists(self.csv_file) and os.path.getsize(self.csv_file) > 0
            
            with open(self.csv_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.columns)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(customer_data)
            
            self._cache = {}
            self._cache_timestamp = None
            return True
        except PermissionError:
            logging.error("Permission denied while writing to CSV file")
            messagebox.showerror("خطأ", "لا يوجد صلاحية للوصول إلى ملف البيانات")
            return False
        except Exception as e:
            logging.error(f"Error appending customer: {str(e)}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ البيانات: {str(e)}")
            return False
    
    def update_customer(self, name: str, updated_data: Dict) -> bool:
        """Update customer data in CSV file."""
        try:
            data = self.read_data()
            customer_found = False
            
            for i, row in enumerate(data):
                if row["Name"] == name:
                    preserved_fields = {
                        "Notification Sent": row.get("Notification Sent", False),
                        "Paid_Installments": row.get("Paid_Installments", "[]"),
                        "Notified_Installments": row.get("Notified_Installments", "[]"),
                        "Installment_Values": row.get("Installment_Values", "{}")
                    }
                    data[i] = {**row, **updated_data, **preserved_fields}
                    customer_found = True
                    break
            
            if not customer_found:
                logging.error(f"Customer not found: {name}")
                return False
                
            success = self.save_data(data)
            if success:
                logging.info(f"Successfully updated customer: {name}")
            return success
        except Exception as e:
            logging.error(f"Error updating customer: {str(e)}")
            return False
            
    def delete_customer(self, name: str) -> bool:
        """Delete customer from CSV file."""
        try:
            data = self.read_data()
            original_length = len(data)
            data = [row for row in data if row["Name"] != name]
            
            if len(data) == original_length:
                logging.error(f"Customer not found: {name}")
                return False
                
            return self.save_data(data)
        except Exception as e:
            logging.error(f"Error deleting customer: {str(e)}")
            return False
            
    def create_backup(self) -> Optional[str]:
        """Create a backup of the current data."""
        try:
            if not os.path.exists(self.csv_file):
                logging.error("No data file to backup")
                return None
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = os.path.join(self.backup_folder, f"backup_{timestamp}.csv")
            
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            
            shutil.copy2(self.csv_file, backup_filename)
            logging.info(f"Backup created: {backup_filename}")
            return backup_filename
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return None
            
    def restore_backup(self, backup_file: str) -> bool:
        """Restore from a backup file."""
        try:
            backup_path = os.path.join(self.backup_folder, backup_file)
            if not os.path.exists(backup_path):
                logging.error(f"Backup file not found: {backup_path}")
                return False
                
            self.create_backup()
            
            shutil.copy2(backup_path, self.csv_file)
            
            self._cache = {}
            self._cache_timestamp = None
            
            return True
            
        except Exception as e:
            logging.error(f"Error restoring backup: {str(e)}")
            return False
            
    def get_backup_files(self) -> List[str]:
        """Get list of available backup files."""
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            return sorted(
                [f for f in os.listdir(self.backup_folder) if f.endswith(".csv")],
                reverse=True
            )
        except Exception as e:
            logging.error(f"Error getting backup files: {str(e)}")
            return []

    def search_customers(self, query: str) -> List[Dict]:
        """Search customers by any field."""
        try:
            data = self.read_data()
            query = query.lower()
            return [
                row for row in data 
                if any(
                    str(value).lower().find(query) != -1 
                    for value in row.values()
                )
            ]
        except Exception as e:
            logging.error(f"Error searching customers: {str(e)}")
            return []

    def mark_installment_as_paid(self, customer_name: str, installment_date: str) -> bool:
        """Mark a specific installment as paid."""
        try:
            data = self.read_data()
            
            for i, row in enumerate(data):
                if row["Name"] == customer_name:
                    try:
                        paid_installments = eval(row.get("Paid_Installments", "[]"))
                        if not isinstance(paid_installments, list):
                            paid_installments = []
                    except:
                        paid_installments = []
                        
                    if installment_date not in paid_installments:
                        paid_installments.append(installment_date)
                        data[i]["Paid_Installments"] = str(paid_installments)
                        return self.save_data(data)
                    else:
                        logging.info(f"Installment already paid: {installment_date}")
                        return True
            
            logging.warning(f"Customer not found: {customer_name}")
            return False
            
        except Exception as e:
            logging.error(f"Error marking installment as paid: {str(e)}")
            return False

    def get_payment_status(self, customer_name: str, installment_date: str) -> bool:
        """Check if a specific installment has been paid."""
        try:
            data = self.read_data()
            for customer in data:
                if customer["Name"] == customer_name:
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                        return installment_date in paid_installments
                    except:
                        return False
            return False
        except Exception as e:
            logging.error(f"Error checking payment status: {str(e)}")
            return False
            
    def update_installment(self, customer_name: str, old_date: str, new_date: str, new_value: float) -> bool:
        """Update an installment's date and value."""
        try:
            data = self.read_data()
            
            for i, customer in enumerate(data):
                if customer["Name"] == customer_name:
                    dates_str = customer.get("Installment Dates", "")
                    if not dates_str:
                        logging.warning(f"Customer {customer_name} has no installment dates")
                        return False
                        
                    installment_dates = dates_str.split(";")
                    
                    if old_date not in installment_dates:
                        logging.warning(f"Installment date {old_date} not found for customer {customer_name}")
                        return False
                        
                    installment_dates[installment_dates.index(old_date)] = new_date
                    data[i]["Installment Dates"] = ";".join(installment_dates)
                    
                    try:
                        installment_values = eval(customer.get("Installment_Values", "{}"))
                        if old_date in installment_values:
                            installment_values[new_date] = new_value
                            del installment_values[old_date]
                        else:
                            installment_values[new_date] = new_value
                        data[i]["Installment_Values"] = str(installment_values)
                    except:
                        data[i]["Installment_Values"] = str({new_date: new_value})
                    
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                        if old_date in paid_installments:
                            paid_installments.remove(old_date)
                            paid_installments.append(new_date)
                            data[i]["Paid_Installments"] = str(paid_installments)
                    except Exception as e:
                        logging.error(f"Error updating paid status: {str(e)}")
                    
                    if self.save_data(data):
                        return True
                    return False
            
            logging.warning(f"Customer not found: {customer_name}")
            return False
            
        except Exception as e:
            logging.error(f"Error updating installment: {str(e)}")
            return False
            
    def unmark_installment_as_paid(self, customer_name: str, installment_date: str) -> bool:
        """Remove a specific installment from the paid list."""
        try:
            data = self.read_data()
            
            for i, row in enumerate(data):
                if row["Name"] == customer_name:
                    try:
                        paid_installments = eval(row.get("Paid_Installments", "[]"))
                        if not isinstance(paid_installments, list):
                            paid_installments = []
                    except:
                        paid_installments = []
                        
                    if installment_date in paid_installments:
                        paid_installments.remove(installment_date)
                        data[i]["Paid_Installments"] = str(paid_installments)
                        return self.save_data(data)
                    else:
                        logging.info(f"Installment wasn't marked as paid: {installment_date}")
                        return True
            
            logging.warning(f"Customer not found: {customer_name}")
            return False
            
        except Exception as e:
            logging.error(f"Error unmarking installment as paid: {str(e)}")
            return False


class DatePicker(CTkToplevel):
    """Popup calendar to select a date."""
    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.geometry("400x450")
        self.title("اختر التاريخ")
        
        main_frame = StyleManager.create_frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        StyleManager.create_label(
            main_frame,
            text="اختر تاريخ بدء الأقساط",
            font_style="subheading"
        ).pack(pady=(0, 20))
        
        self.cal = Calendar(
            main_frame,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            background=StyleManager.COLORS["surface"],
            foreground=StyleManager.COLORS["text"],
            headersbackground=StyleManager.COLORS["primary"],
            headersforeground=StyleManager.COLORS["text"],
            selectbackground=StyleManager.COLORS["secondary"],
            selectforeground=StyleManager.COLORS["text"],
            normalbackground=StyleManager.COLORS["background"],
            normalforeground=StyleManager.COLORS["text"],
            weekendbackground=StyleManager.COLORS["background"],
            weekendforeground=StyleManager.COLORS["text"],
            othermonthbackground=StyleManager.COLORS["background"],
            othermonthforeground=StyleManager.COLORS["text_secondary"]
        )
        self.cal.pack(pady=20, padx=20, fill="both", expand=True)
        
        buttons_frame = StyleManager.create_frame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        StyleManager.create_button(
            buttons_frame,
            text="تحديد",
            width=150,
            command=self.select_date
        ).grid(row=0, column=0, padx=5)
        
        StyleManager.create_button(
            buttons_frame,
            text="إلغاء",
            style="secondary",
            width=150,
            command=self.destroy
        ).grid(row=0, column=1, padx=5)
        
        self.transient(parent)
        self.grab_set()
        self.focus_set()
    
    def select_date(self):
        """Set the selected date and close the window."""
        self.entry_widget.delete(0, "end")
        self.entry_widget.insert(0, self.cal.get_date())
        self.destroy()

