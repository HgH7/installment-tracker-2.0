import customtkinter
from customtkinter import *
from tkinter import messagebox, ttk, StringVar, BooleanVar, filedialog
import tkinter as tk
from tkinter import TclError
import re
import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from tkcalendar import Calendar
import shutil
import threading
import pywhatkit as kit
import logging
from typing import List, Dict, Optional, Union
import time
import sys
import traceback

# Ensure logs directory exists
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Set up logging with more detailed format
logging.basicConfig(
    filename=os.path.join(logs_dir, 'app.log'),
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

# Add console logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# Global variables
app = None
frames = {}

class StyleManager:
    """Manages application-wide styling"""
    
    # Color scheme
    COLORS = {
        "primary": "#2B7DE9",      # Blue
        "secondary": "#23B0FF",    # Light Blue
        "success": "#28a745",      # Green
        "warning": "#ffc107",      # Yellow
        "danger": "#dc3545",       # Red
        "background": "#1a1a1a",   # Dark background
        "surface": "#2d2d2d",      # Slightly lighter background
        "text": "#ffffff",         # White text
        "text_secondary": "#b3b3b3", # Gray text
        "border": "#404040"        # Border color
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
            # Create base frame configuration
            frame_config = {
                "corner_radius": 15,
                "border_width": 0
            }
            
            # Only set fg_color if not provided in kwargs
            if "fg_color" not in kwargs:
                frame_config["fg_color"] = cls.COLORS["surface"]
            
            # Update with any additional kwargs
            frame_config.update(kwargs)
            
            return CTkFrame(
                master,
                **frame_config
            )
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
            # Only set text_color and font if not provided in kwargs
            if 'text_color' not in kwargs:
                kwargs['text_color'] = cls.COLORS["text"]
            if 'font' not in kwargs:
                kwargs['font'] = cls.FONTS[font_style]
                
            return CTkLabel(
                master,
                text=text,
                **kwargs
            )
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
            
            # Only set font if not provided in kwargs
            if 'font' not in kwargs:
                entry_config['font'] = cls.FONTS["body"]
                
            # Update with any additional kwargs
            entry_config.update(kwargs)
            
            return CTkEntry(
                master,
                **entry_config
            )
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
        # Sanitize customer name for use in file path
        safe_name = "".join(c for c in customer_name if c.isalnum() or c in (' ', '-', '_')).strip()
        customer_dir = os.path.join(self.base_dir, safe_name)
        
        # Create customer directory if it doesn't exist
        if not os.path.exists(customer_dir):
            os.makedirs(customer_dir)
            logging.info(f"Created customer directory: {customer_dir}")
            
        return customer_dir
        
    def add_files(self, customer_name: str, files: List[str]) -> bool:
        """Add files for a customer"""
        try:
            customer_dir = self._get_customer_dir(customer_name)
            
            # Ensure customer directory exists
            if not os.path.exists(customer_dir):
                os.makedirs(customer_dir)
                logging.info(f"Created directory for customer {customer_name}")
            
            success = True
            
            for file_path in files:
                try:
                    # Get file name and create safe version
                    file_name = os.path.basename(file_path)
                    safe_name = "".join(c for c in file_name if c.isalnum() or c in ('.', '-', '_')).strip()
                    
                    # Create unique filename if file already exists
                    base, ext = os.path.splitext(safe_name)
                    counter = 1
                    while os.path.exists(os.path.join(customer_dir, safe_name)):
                        safe_name = f"{base}_{counter}{ext}"
                        counter += 1
                    
                    # Copy file to customer directory
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

# Initialize file manager
file_manager = FileManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "customer_files"))

def initialize_app():
    """Initialize the main application window with error handling"""
    global app
    try:
        logging.info("Starting application initialization...")
        
        # Initialize the main window
        app = CTk()
        if not app:
            raise Exception("Failed to create main window")
            
        app.geometry("1280x800")
        app.title("نظام إدارة الأقساط")
        
        # Try setting appearance mode
        try:
            app._set_appearance_mode("dark")
            logging.info("Appearance mode set successfully")
        except Exception as e:
            logging.error(f"Failed to set appearance mode: {str(e)}")
            # Continue anyway as this is not critical
        
        # Center the window on screen
        try:
            screen_width = app.winfo_screenwidth()
            screen_height = app.winfo_screenheight()
            x = (screen_width - 1280) // 2
            y = (screen_height - 800) // 2
            app.geometry(f"1280x800+{x}+{y}")
            logging.info("Window centered successfully")
        except Exception as e:
            logging.error(f"Failed to center window: {str(e)}")
            # Continue anyway as this is not critical
        
        return app
    except Exception as e:
        logging.critical(f"Failed to initialize application: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("خطأ حرج", "فشل في بدء التطبيق. يرجى مراجعة ملف السجل للتفاصيل.")
        sys.exit(1)

def main():
    """Main application entry point with error handling"""
    global app
    try:
        logging.info("Application starting...")
        if not app:
            app = initialize_app()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Critical error in main: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("خطأ حرج", f"حدث خطأ غير متوقع: {str(e)}\nيرجى مراجعة ملف السجل للتفاصيل.")
        sys.exit(1)

def show_frame(frame):
    """Show the specified frame and hide others"""
    for f in frames.values():
        f.grid_remove()
    frame.grid()

def refresh_treeview(tree, data=None):
    """Refresh the treeview with data."""
    # Clear existing items
    for item in tree.get_children():
        tree.delete(item)
        
    # If no data provided, read from CSV
    if data is None:
        data = csv_manager.read_data()
    
    # Get column names
    columns = tree["columns"]
    
    # Insert data into treeview with proper status handling
    for customer in data:
        values = []
        for col in columns:
            if col == "Paid":
                # Get the first installment date and check if it's paid
                installment_dates = customer.get("Installment Dates", "").split(";")
                first_date = installment_dates[0] if installment_dates else ""
                paid_installments = eval(customer.get("Paid_Installments", "[]"))
                is_paid = first_date in paid_installments
                values.append("نعم" if is_paid else "لا")
            else:
                values.append(customer.get(col, ""))
        
        item = tree.insert("", "end", values=values)
        
        # Add color coding for paid status if applicable
        if "Paid" in columns:
            if values[columns.index("Paid")] == "نعم":
                tree.item(item, tags=("paid",))
            else:
                tree.item(item, tags=("unpaid",))
    
    # Configure payment status styles if needed
    if "Paid" in columns:
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])

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
        self._cache_duration = 60  # Cache duration in seconds
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
            # Return cached data if valid
            if self._is_cache_valid():
                return self._cache.copy()  # Return a copy to prevent cache modification
                
            data = []
            with open(self.csv_file, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Format and validate data
                    cleaned_row = self._clean_row_data(row)
                    # Ensure Notified_Installments exists
                    if "Notified_Installments" not in cleaned_row:
                        cleaned_row["Notified_Installments"] = "[]"
                    data.append(cleaned_row)
                    
            # Update cache with new data
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
        
        # Format phone number
        if "Phone" in cleaned_row:
            cleaned_row["Phone"] = f"+{cleaned_row['Phone']}" if not cleaned_row['Phone'].startswith("+") else cleaned_row['Phone']
            
        # Convert numeric values
        try:
            cleaned_row["Amount"] = float(cleaned_row.get("Amount", 0))
            cleaned_row["Installment Value"] = float(cleaned_row.get("Installment Value", 0))
            cleaned_row["Installments"] = int(cleaned_row.get("Installments", 0))
        except (ValueError, TypeError):
            logging.warning(f"Invalid numeric values in row: {row}")
            
        # Ensure boolean fields
        cleaned_row["Notification Sent"] = str(cleaned_row.get("Notification Sent", "")).lower() == "true"
        
        # Initialize Paid_Installments if not present
        if "Paid_Installments" not in cleaned_row:
            cleaned_row["Paid_Installments"] = "[]"
            
        # Initialize Notified_Installments if not present
        if "Notified_Installments" not in cleaned_row:
            cleaned_row["Notified_Installments"] = "[]"
            
        return cleaned_row
        
    def save_data(self, data: List[Dict]) -> bool:
        """Save data to CSV file with backup"""
        try:
            # Validate data before saving
            validated_data = []
            for row in data:
                if self._validate_row(row):
                    validated_data.append(row)
                else:
                    logging.warning(f"Invalid row data skipped: {row}")
            
            # Create backup before saving
            self.create_backup()
            
            with open(self.csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.columns)
                writer.writeheader()
                writer.writerows(validated_data)
                
            # Update cache with new data
            self._update_cache(validated_data)
            return True
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            return False
            
    def _validate_row(self, row: Dict) -> bool:
        """Validate row data"""
        required_fields = ["Name", "Phone", "Amount", "Installments"]
        
        # Check required fields
        if not all(field in row for field in required_fields):
            return False
            
        # Validate numeric fields
        try:
            float(row["Amount"])
            float(row["Installment Value"])
            int(row["Installments"])
        except (ValueError, TypeError):
            return False
            
        # Validate phone number format
        phone_pattern = r"^\+?\d{10,15}$"
        if not re.match(phone_pattern, str(row["Phone"])):
            return False
            
        # Ensure optional fields have default values if missing
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
            # Validate required fields
            missing_fields = [field for field in self.columns if field not in customer_data]
            if missing_fields:
                logging.error(f"Missing required fields: {missing_fields}")
                messagebox.showerror("خطأ", f"الحقول التالية مطلوبة: {', '.join(missing_fields)}")
                return False
            
            # Create backup before appending
            if not self.create_backup():
                logging.error("Failed to create backup before appending customer")
                messagebox.showerror("خطأ", "فشل في إنشاء نسخة احتياطية")
                return False
            
            # Check if file exists and has headers
            file_exists = os.path.exists(self.csv_file) and os.path.getsize(self.csv_file) > 0
            
            with open(self.csv_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.columns)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(customer_data)
            
            # Clear cache to force reload
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
                    # Preserve existing fields that are not in updated_data
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
            
            # Ensure backup directory exists
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            
            shutil.copy2(self.csv_file, backup_filename)  # copy2 preserves metadata
            logging.info(f"Backup created: {backup_filename}")
            return backup_filename
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return None
            
    def restore_backup(self, backup_file: str) -> bool:
        """Restore from a backup file."""
        try:
            # Check if backup file exists
            backup_path = os.path.join(self.backup_folder, backup_file)
            if not os.path.exists(backup_path):
                logging.error(f"Backup file not found: {backup_path}")
                return False
                
            # Backup current file before restoring
            self.create_backup()
            
            # Copy backup to main file
            shutil.copy2(backup_path, self.csv_file)
            
            # Clear cache to force reload
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
                reverse=True  # Newest first
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
                    # Get current paid installments
                    try:
                        paid_installments = eval(row.get("Paid_Installments", "[]"))
                        if not isinstance(paid_installments, list):
                            paid_installments = []
                    except:
                        paid_installments = []
                        
                    # Add the installment date if not already paid
                    if installment_date not in paid_installments:
                        paid_installments.append(installment_date)
                        data[i]["Paid_Installments"] = str(paid_installments)
                        # Save updated data
                        return self.save_data(data)
                    else:
                        logging.info(f"Installment already paid: {installment_date}")
                        return True  # Already paid is not an error
            
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
                    # Get installment dates
                    dates_str = customer.get("Installment Dates", "")
                    if not dates_str:
                        logging.warning(f"Customer {customer_name} has no installment dates")
                        return False
                        
                    installment_dates = dates_str.split(";")
                    
                    # Check if old date exists
                    if old_date not in installment_dates:
                        logging.warning(f"Installment date {old_date} not found for customer {customer_name}")
                        return False
                        
                    # Update the date
                    installment_dates[installment_dates.index(old_date)] = new_date
                    data[i]["Installment Dates"] = ";".join(installment_dates)
                    
                    # Update installment values if they exist
                    try:
                        installment_values = eval(customer.get("Installment_Values", "{}"))
                        if old_date in installment_values:
                            installment_values[new_date] = new_value
                            del installment_values[old_date]
                        else:
                            installment_values[new_date] = new_value
                        data[i]["Installment_Values"] = str(installment_values)
                    except:
                        # If no installment values exist, create new dictionary
                        data[i]["Installment_Values"] = str({new_date: new_value})
                    
                    # Update payment status if needed
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                        if old_date in paid_installments:
                            paid_installments.remove(old_date)
                            paid_installments.append(new_date)
                            data[i]["Paid_Installments"] = str(paid_installments)
                    except Exception as e:
                        logging.error(f"Error updating paid status: {str(e)}")
                    
                    # Save the updated data
                    if self.save_data(data):
                        # Refresh payment history views after successful update
                        refresh_payment_history_views()
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
                    # Get current paid installments
                    try:
                        paid_installments = eval(row.get("Paid_Installments", "[]"))
                        if not isinstance(paid_installments, list):
                            paid_installments = []
                    except:
                        paid_installments = []
                        
                    # Remove the installment date if it's paid
                    if installment_date in paid_installments:
                        paid_installments.remove(installment_date)
                        data[i]["Paid_Installments"] = str(paid_installments)
                        # Save updated data
                        return self.save_data(data)
                    else:
                        logging.info(f"Installment wasn't marked as paid: {installment_date}")
                        return True  # Not being in the list is not an error
            
            logging.warning(f"Customer not found: {customer_name}")
            return False
            
        except Exception as e:
            logging.error(f"Error unmarking installment as paid: {str(e)}")
            return False

# Initialize CSV manager
csv_filename = "customers.csv"
backup_folder = "backups"
csv_manager = CSVManager(csv_filename, backup_folder)

def read_csv_safely():
    """Read data from CSV file using CSVManager."""
    return csv_manager.read_data()

def save_to_csv_and_excel(data):
    """Save data using CSVManager."""
    return csv_manager.save_data(data)

def validate_and_save(name_entry, phone_entry, amount_entry, installments_entry, start_date_entry, file_list=None):
    """Validate and save customer data"""
    try:
        # Get values from entries
        name = name_entry.get().strip()
        phone = phone_entry.get().strip()
        amount = amount_entry.get().strip()
        installments = installments_entry.get().strip()
        start_date = start_date_entry.get().strip()

        # Validate all fields are filled
        if not all([name, phone, amount, installments, start_date]):
            messagebox.showerror("خطأ", "جميع الحقول مطلوبة.")
            return False

        # Validate phone number
        if not re.match(r"^\+?\d{10,15}$", phone):
            messagebox.showerror("خطأ", "رقم الهاتف غير صالح.")
            return False

        # Validate amount
        if not re.match(r"^\d+(\.\d{1,2})?$", amount):
            messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقمًا صالحًا.")
            return False

        # Validate installments
        if not installments.isdigit() or int(installments) <= 0:
            messagebox.showerror("خطأ", "عدد الأقساط يجب أن يكون رقمًا صحيحًا أكبر من صفر.")
            return False

        # Validate date format
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("خطأ", "تنسيق التاريخ غير صحيح. يجب أن يكون بهذا الشكل: YYYY-MM-DD")
            return False

        amount = float(amount)
        installments = int(installments)
        installment_value = round(amount / installments, 2)
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Generate installment dates (one per month)
        installment_dates = []
        current_date = start_date_obj
        for _ in range(installments):
            installment_dates.append(current_date.strftime("%Y-%m-%d"))
            # Add one month to current date
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        customer_data = {
            "Name": name,
            "Phone": phone,
            "Amount": amount,
            "Installments": installments,
            "Installment Value": installment_value,
            "Start Date": start_date,
            "Installment Dates": ";".join(installment_dates),
            "Notification Sent": False,
            "Paid_Installments": "[]",
            "Notified_Installments": "[]",
            "Installment_Values": "{}"  # Initialize empty installment values
        }

        # Save customer data
        if csv_manager.append_customer(customer_data):
            # Save files if provided
            if file_list and hasattr(file_list, 'files') and file_list.files:
                if file_manager.add_files(name, file_list.files):
                    logging.info(f"Successfully saved files for customer {name}")
                else:
                    logging.error(f"Failed to save files for customer {name}")
                    messagebox.showwarning("تحذير", "تم حفظ بيانات العميل ولكن فشل حفظ الملفات المرفقة")
            
            # Clear all entry fields
            name_entry.delete(0, "end")
            phone_entry.delete(0, "end")
            amount_entry.delete(0, "end")
            installments_entry.delete(0, "end")
            start_date_entry.delete(0, "end")
            
            # Clear file list but preserve the widget
            if file_list:
                file_list.files = []
                file_list.configure(state="normal")
                file_list.delete("1.0", "end")
                file_list.configure(state="disabled")
            
            messagebox.showinfo("نجاح", "تم إضافة العميل بنجاح.")
            return True
        else:
            return False
            
    except Exception as e:
        logging.error(f"Error saving customer data: {str(e)}")
        messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ البيانات: {str(e)}")
        return False

class DatePicker(CTkToplevel):
    """Popup calendar to select a date."""
    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.geometry("400x450")
        self.title("اختر التاريخ")
        
        # Create main frame
        main_frame = StyleManager.create_frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add title
        StyleManager.create_label(
            main_frame,
            text="اختر تاريخ بدء الأقساط",
            font_style="subheading"
        ).pack(pady=(0, 20))
        
        # Calendar widget with custom colors
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
        
        # Buttons frame
        buttons_frame = StyleManager.create_frame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Select button
        StyleManager.create_button(
            buttons_frame,
            text="تحديد",
            width=150,
            command=self.select_date
        ).grid(row=0, column=0, padx=5)
        
        # Cancel button
        StyleManager.create_button(
            buttons_frame,
            text="إلغاء",
            style="secondary",
            width=150,
            command=self.destroy
        ).grid(row=0, column=1, padx=5)
        
        # Make the window modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
    
    def select_date(self):
        """Set the selected date and close the window."""
        self.entry_widget.delete(0, "end")
        self.entry_widget.insert(0, self.cal.get_date())
        self.destroy()

def show_payment_history():
    """Show payment history for selected customer."""
    # Get the current frame's treeview
    current_frame = None
    for frame in frames.values():
        if frame.winfo_ismapped():  # Check if frame is visible
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
        
        # Get customer data
        data = csv_manager.read_data()
        customer_data = None
        for customer in data:
            if customer["Name"] == customer_name:
                customer_data = customer
                break
                
        if not customer_data:
            messagebox.showerror("خطأ", "لم يتم العثور على بيانات العميل.")
            return
            
        # Create payment history window
        history_window = CTkToplevel(app)
        history_window.geometry("800x760")
        history_window.title(f"سجل المدفوعات - {customer_name}")
        
        # Make window modal
        history_window.transient(app)
        history_window.grab_set()
        
        # Create main frame
        main_frame = StyleManager.create_frame(history_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add title
        StyleManager.create_label(
            main_frame,
            text=f"سجل المدفوعات - {customer_name}",
            font_style="subheading"
        ).pack(pady=(0, 20))
        
        # Create table container
        table_frame = StyleManager.create_frame(main_frame)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        # Create a Treeview widget
        columns = ("Date", "Value", "Status", "Action")
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview"
        )
        
        # Set column widths and headings
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
            
            # Get installment values if they exist
            try:
                installment_values = eval(customer_data.get("Installment_Values", "{}"))
            except:
                installment_values = {}
            
            # Create a dictionary to store row IDs for each installment date
            date_to_row_map = {}
            today = datetime.now().strftime("%Y-%m-%d")
            
            for date in installment_dates:
                is_paid = date in paid_installments
                status = "مدفوع" if is_paid else "غير مدفوع"
                status_tags = ("paid",) if is_paid else ("unpaid",)
                
                # Get the installment value, using the specific value if it exists
                value = installment_values.get(date, default_value)
                
                # Determine if this installment date is in the future
                is_future = date > today
                
                # For unpaid installments, add a "Mark as Paid" button, unless it's in the future
                action = "" if is_paid else "تسجيل كمدفوع" if not is_future else "موعد مستقبلي"
                
                # Insert row and store the row ID
                row_id = tree.insert("", "end", values=(date, f"{value:.2f}", status, action), tags=status_tags)
                date_to_row_map[date] = row_id
        
        # Configure tags
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(fill="both", expand=True)
        
        # Function to mark installment as paid
        def mark_as_paid(event):
            try:
                item = tree.identify_row(event.y)
                if not item:
                    return
                    
                values = tree.item(item)["values"]
                date = values[0]
                
                if values[3] == "تسجيل كمدفوع":  # Only if action is "Mark as Paid"
                    if csv_manager.mark_installment_as_paid(customer_name, date):
                        # Update the row
                        tree.item(item, values=(date, values[1], "مدفوع", ""), tags=("paid",))
                        messagebox.showinfo("نجاح", "تم تسجيل القسط كمدفوع بنجاح.")
                    else:
                        messagebox.showerror("خطأ", "فشل في تسجيل القسط كمدفوع.")
                        
            except Exception as e:
                logging.error(f"Error marking installment as paid: {str(e)}")
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تسجيل القسط: {str(e)}")
                
        # Function to edit installment
        def edit_installment(event):
            try:
                item = tree.identify_row(event.y)
                if not item:
                    return
                    
                values = tree.item(item)["values"]
                date = values[0]
                value = values[1]
                is_paid = values[2] == "مدفوع"
                
                # Create edit installment window
                edit_window = CTkToplevel(history_window)
                edit_window.geometry("500x450")
                edit_window.title("تعديل القسط")
                
                # Make window modal
                edit_window.transient(history_window)
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
                date_entry.insert(0, date)
                
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
                amount_entry.insert(0, str(value))
                
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
                        if csv_manager.update_installment(customer_name, date, new_date, new_value):
                            # Update paid status if needed
                            if is_paid != new_paid_status:
                                if new_paid_status:
                                    csv_manager.mark_installment_as_paid(customer_name, new_date)
                                else:
                                    csv_manager.unmark_installment_as_paid(customer_name, new_date)
                                
                            messagebox.showinfo("نجاح", "تم تحديث بيانات القسط بنجاح.")
                            edit_window.destroy()
                            # Refresh the payment history view
                            history_window.destroy()
                            show_payment_history()
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
        
        # Bind double-click event for marking as paid
        tree.bind("<Double-1>", mark_as_paid)
        
        # Bind right-click event for editing
        tree.bind("<Button-3>", edit_installment)
        
        # Calculate payment summary
        if customer_data:
            total_installments = len(installment_dates)
            paid_count = len(paid_installments)
            remaining_count = total_installments - paid_count
            
            # Calculate total amounts
            total_amount = sum(float(installment_values.get(date, default_value)) for date in installment_dates)
            paid_amount = sum(float(installment_values.get(date, default_value)) for date in paid_installments)
            remaining_amount = total_amount - paid_amount
            
            # Create summary frame
            summary_frame = StyleManager.create_frame(main_frame)
            summary_frame.pack(fill="x", padx=20, pady=(0, 20))
            
            # Add summary information
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
        
        # Close button
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

def export_to_excel():
    """Export customer data to Excel file with enhanced formatting."""
    try:
        data = csv_manager.read_data()
        if not data:
            messagebox.showerror("خطأ", "لا توجد بيانات للتصدير.")
            return
            
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"customers_export_{timestamp}.xlsx"
        
        # Convert data to DataFrame with Arabic column names
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
        
        # Clean and prepare data
        cleaned_data = []
        for row in data:
            cleaned_row = row.copy()
            # Convert boolean to Arabic text
            cleaned_row["Notification Sent"] = "نعم" if row["Notification Sent"] else "لا"
            # Ensure numeric values are properly formatted
            try:
                cleaned_row["Amount"] = float(row["Amount"])
                cleaned_row["Installment Value"] = float(row["Installment Value"])
                cleaned_row["Installments"] = int(row["Installments"])
            except (ValueError, TypeError):
                pass
            cleaned_data.append(cleaned_row)
        
        df = pd.DataFrame(cleaned_data)
        df = df.rename(columns=arabic_columns)
        
        # Create Excel writer with xlsxwriter engine
        with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='بيانات العملاء', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['بيانات العملاء']
            
            # Define formats
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
            
            # Predefined column widths for specific columns
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
            
            # Set column widths and apply formats
            for idx, col in enumerate(df.columns):
                # Use predefined width or calculate based on content
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
                
                # Apply format to entire column
                for row in range(1, len(df) + 1):
                    worksheet.write(row, idx, df.iloc[row-1][col], cell_format)
            
            # Add alternating row colors
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
            
            # Set larger row height for all rows
            worksheet.set_default_row(45)  # Increased row height
            worksheet.set_row(0, 60)  # Make header row even taller
            
            # Freeze the header row
            worksheet.freeze_panes(1, 0)
            
            # Set RTL direction for the worksheet
            worksheet.right_to_left()
        
        # Show success message
        messagebox.showinfo("نجاح", f"تم تصدير البيانات إلى ملف Excel: {excel_filename}")
        
        # Open the Excel file automatically
        os.startfile(os.path.abspath(excel_filename))
        
    except ImportError:
        messagebox.showerror("خطأ", "الرجاء التأكد من تثبيت حزمة xlsxwriter")
        logging.error("xlsxwriter package not installed")
    except Exception as e:
        logging.error(f"Error exporting to Excel: {str(e)}")
        messagebox.showerror("خطأ", "حدث خطأ أثناء تصدير البيانات.")

def setup_add_page():
    frame = frames["add"]
    frame.grid_columnconfigure(0, weight=1)
    
    # Create header
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="إضافة عميل جديد",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))
    
    StyleManager.create_label(
        header_frame,
        text="أدخل بيانات العميل وتفاصيل الأقساط",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))
    
    # Create form container
    form_frame = StyleManager.create_frame(frame)
    form_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    form_frame.grid_columnconfigure(0, weight=1)
    form_frame.grid_columnconfigure(1, weight=2)
    
    # Form fields
    fields = [
        {"label": "اسم العميل:", "type": "text"},
        {"label": "رقم الهاتف:", "type": "phone"},
        {"label": "المبلغ:", "type": "number"},
        {"label": "عدد الأقساط:", "type": "number"}
    ]
    
    entries = []
    row = 0
    
    for field in fields:
        # Create field container
        field_frame = StyleManager.create_frame(form_frame)
        field_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        field_frame.grid_columnconfigure(1, weight=1)
        
        # Add label
        StyleManager.create_label(
            field_frame,
            text=field["label"],
            font_style="body_bold"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Add entry
        entry = StyleManager.create_entry(field_frame, width=300)
        entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        entries.append(entry)
        
        row += 1
    
    # Date Picker Section
    date_frame = StyleManager.create_frame(form_frame)
    date_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    date_frame.grid_columnconfigure(1, weight=1)
    
    StyleManager.create_label(
        date_frame,
        text="تاريخ بدء الأقساط:",
        font_style="body_bold"
    ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
    
    start_date_entry = StyleManager.create_entry(date_frame, width=200)
    start_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
    
    date_picker_btn = StyleManager.create_button(
        date_frame,
        text="📅 اختر التاريخ",
        style="secondary",
        command=lambda: DatePicker(app, start_date_entry)
    )
    date_picker_btn.grid(row=0, column=2, padx=10, pady=5)
    
    # Buttons container
    buttons_frame = StyleManager.create_frame(frame)
    buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)
    
    # Save Button
    save_btn = StyleManager.create_button(
        buttons_frame,
        text="حفظ العميل",
        width=200,
        command=lambda: validate_and_save(*entries, start_date_entry)
    )
    save_btn.grid(row=0, column=0, padx=10, pady=10)
    
    # Back Button
    back_btn = StyleManager.create_button(
        buttons_frame,
        text="رجوع",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    )
    back_btn.grid(row=0, column=1, padx=10, pady=10)

    # File upload section with modern design
    file_frame = StyleManager.create_frame(form_frame, fg_color="transparent")
    file_frame.grid(row=len(fields)*2+1, column=0, sticky="ew", pady=(20, 0))
    file_frame.grid_columnconfigure(1, weight=1)
    
    StyleManager.create_label(
        file_frame,
        text="📁 ملفات العميل",
        font_style="body_bold"
    ).grid(row=0, column=0, sticky="w", padx=(0, 10))
    
    # Create a frame for the file list and buttons
    file_list_frame = StyleManager.create_frame(file_frame, fg_color="transparent")
    file_list_frame.grid(row=0, column=1, sticky="ew", pady=(0, 10))
    file_list_frame.grid_columnconfigure(0, weight=1)
    
    # File list with scrollbar
    file_list = CTkTextbox(
        file_list_frame,
        width=400,
        height=100,
        font=StyleManager.FONTS["body"],
        fg_color=StyleManager.COLORS["background"],
        border_color=StyleManager.COLORS["border"],
        state="disabled"  # Make the text box read-only
    )
    file_list.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(file_list_frame, orient="vertical", command=file_list.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    file_list.configure(yscrollcommand=scrollbar.set)
    
    # Store selected files
    file_list.files = []
    
    # Buttons frame
    file_buttons_frame = StyleManager.create_frame(file_frame, fg_color="transparent")
    file_buttons_frame.grid(row=0, column=2, sticky="e")
    
    def add_files():
        files = filedialog.askopenfilenames(
            title="اختر ملفات العميل",
            filetypes=[
                ("All files", "*.*"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.png *.jpg *.jpeg"),
                ("Document files", "*.doc *.docx")
            ]
        )
        if files:
            file_list.files.extend(files)
            file_list.configure(state="normal")  # Temporarily enable for updating
            file_list.delete("1.0", "end")  # Clear existing content
            for file in files:
                file_list.insert("end", f"{os.path.basename(file)}\n")
            file_list.configure(state="disabled")  # Make read-only again
    
    def clear_files():
        if file_list.files:
            if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف جميع الملفات المحددة؟"):
                file_list.files = []
                file_list.configure(state="normal")
                file_list.delete("1.0", "end")
                file_list.configure(state="disabled")
    
    # Add file button
    StyleManager.create_button(
        file_buttons_frame,
        text="إضافة ملفات",
        width=120,
        command=add_files
    ).pack(side="left", padx=(0, 5))
    
    # Clear files button
    StyleManager.create_button(
        file_buttons_frame,
        text="مسح الملفات",
        style="secondary",
        width=120,
        command=clear_files
    ).pack(side="left")
    
    # Update save button to include file_list
    save_btn.configure(command=lambda: validate_and_save(*entries, start_date_entry, file_list))

def setup_view_page():
    frame = frames["view"]
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=0)  # Header
    frame.grid_rowconfigure(1, weight=0)  # Search bar
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
        refresh_treeview(frame.tree, results)
        
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
    refresh_treeview(tree)
    
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
                        refresh_treeview(tree)
                        refresh_payment_history_views()  # Refresh payment history views
                    else:
                        messagebox.showerror("خطأ", "فشل في تحديث بيانات العميل.")
                else:
                    # Update existing record
                    if csv_manager.update_customer(customer_name, updated_data):
                        messagebox.showinfo("نجاح", "تم تحديث بيانات العميل بنجاح!")
                        edit_window.destroy()
                        refresh_treeview(tree)
                        refresh_payment_history_views()  # Refresh payment history views
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
                refresh_treeview(tree)
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
        command=lambda: refresh_treeview(tree)
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
    
    # Create header
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
                refresh_treeview(frames["view"].tree)
                
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
                        refresh_payment_history_views()  # Refresh payment history views
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
    
    # Create header
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    StyleManager.create_label(
        header_frame,
        text="النسخ الاحتياطي واستعادة البيانات",
        font_style="heading"
    ).grid(row=0, column=0, pady=(20, 10))
    
    StyleManager.create_label(
        header_frame,
        text="إدارة النسخ الاحتياطية واستعادة البيانات",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, pady=(0, 20))
    
    # Create main content container
    content_frame = StyleManager.create_frame(frame)
    content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
    content_frame.grid_columnconfigure(0, weight=1)
    
    # Backup section
    backup_section = StyleManager.create_frame(content_frame)
    backup_section.grid(row=0, column=0, sticky="ew", pady=(0, 20))
    backup_section.grid_columnconfigure(1, weight=1)
    
    # Backup icon and title
    StyleManager.create_label(
        backup_section,
        text="💾",
        font=("Arial", 36)
    ).grid(row=0, column=0, padx=(20, 10), pady=20)
    
    backup_title_frame = CTkFrame(backup_section, fg_color="transparent")
    backup_title_frame.grid(row=0, column=1, sticky="nsew", pady=20)
    
    StyleManager.create_label(
        backup_title_frame,
        text="إنشاء نسخة احتياطية",
        font_style="subheading"
    ).grid(row=0, column=0, sticky="w")
    
    StyleManager.create_label(
        backup_title_frame,
        text="حفظ نسخة من البيانات الحالية",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, sticky="w")
    
    def create_backup():
        try:
            backup_file = csv_manager.create_backup()
            if backup_file:
                messagebox.showinfo("نجاح", f"تم إنشاء نسخة احتياطية في: {backup_file}")
            else:
                messagebox.showerror("خطأ", "فشل إنشاء النسخة الاحتياطية.")
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء إنشاء النسخة الاحتياطية.")
    
    StyleManager.create_button(
        backup_section,
        text="إنشاء نسخة احتياطية",
        width=200,
        command=create_backup
    ).grid(row=0, column=2, padx=20)
    
    # Restore section
    restore_section = StyleManager.create_frame(content_frame)
    restore_section.grid(row=1, column=0, sticky="ew")
    restore_section.grid_columnconfigure(1, weight=1)
    
    # Restore icon and title
    StyleManager.create_label(
        restore_section,
        text="🔄",
        font=("Arial", 36)
    ).grid(row=0, column=0, padx=(20, 10), pady=20)
    
    restore_title_frame = CTkFrame(restore_section, fg_color="transparent")
    restore_title_frame.grid(row=0, column=1, sticky="nsew", pady=20)
    
    StyleManager.create_label(
        restore_title_frame,
        text="استعادة نسخة احتياطية",
        font_style="subheading"
    ).grid(row=0, column=0, sticky="w")
    
    StyleManager.create_label(
        restore_title_frame,
        text="استعادة البيانات من نسخة احتياطية سابقة",
        font_style="body",
        text_color=StyleManager.COLORS["text_secondary"]
    ).grid(row=1, column=0, sticky="w")
    
    def restore_backup():
        try:
            backup_files = csv_manager.get_backup_files()
            if not backup_files:
                messagebox.showerror("خطأ", "لا توجد نسخ احتياطية متاحة.")
                return
            
            # Create restore window
            restore_window = CTkToplevel(app)
            restore_window.geometry("600x400")
            restore_window.title("استعادة نسخة احتياطية")
            restore_window.transient(app)  # Make window modal
            restore_window.grab_set()  # Make window modal
            
            # Add header
            StyleManager.create_label(
                restore_window,
                text="اختر النسخة الاحتياطية للاستعادة",
                font_style="heading"
            ).pack(pady=(20, 10))
            
            StyleManager.create_label(
                restore_window,
                text="سيتم استبدال البيانات الحالية بالنسخة المحددة",
                font_style="body",
                text_color=StyleManager.COLORS["text_secondary"]
            ).pack(pady=(0, 20))
            
            # Create list of backups
            backup_frame = StyleManager.create_frame(restore_window)
            backup_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Create scrollable frame for backups
            backup_list = CTkScrollableFrame(backup_frame)
            backup_list.pack(fill="both", expand=True)
            
            selected_backup = StringVar()
            
            for backup in sorted(backup_files, reverse=True):  # Show newest first
                # Create a radio button for each backup
                backup_date = backup.replace("backup_", "").replace(".csv", "")
                try:
                    formatted_date = datetime.strptime(backup_date, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_date = backup_date  # Fallback if date parsing fails
                
                radio = CTkRadioButton(
                    backup_list,
                    text=f"نسخة {formatted_date}",
                    variable=selected_backup,
                    value=backup,
                    font=StyleManager.FONTS["body"]
                )
                radio.pack(pady=5, padx=10, anchor="w")
            
            # Set default selection to newest backup
            if backup_files:
                selected_backup.set(backup_files[0])
            
            # Buttons frame
            buttons_frame = StyleManager.create_frame(restore_window)
            buttons_frame.pack(fill="x", padx=20, pady=20)
            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)
            
            def confirm_restore():
                try:
                    selected = selected_backup.get()
                    if not selected:
                        messagebox.showerror("خطأ", "يرجى اختيار نسخة احتياطية.")
                        return
                        
                    if messagebox.askyesno("تأكيد", "هل أنت متأكد من استعادة هذه النسخة؟ سيتم استبدال البيانات الحالية."):
                        if csv_manager.restore_backup(selected):
                            messagebox.showinfo("نجاح", "تم استعادة النسخة الاحتياطية بنجاح.")
                            restore_window.destroy()
                        else:
                            messagebox.showerror("خطأ", "فشل استعادة النسخة الاحتياطية.")
                except Exception as e:
                    logging.error(f"Error restoring backup: {str(e)}")
                    messagebox.showerror("خطأ", "حدث خطأ أثناء استعادة النسخة الاحتياطية.")
            
            # Confirm button
            StyleManager.create_button(
                buttons_frame,
                text="استعادة",
                width=200,
                command=confirm_restore
            ).grid(row=0, column=0, padx=10)
            
            # Cancel button
            StyleManager.create_button(
                buttons_frame,
                text="إلغاء",
                style="secondary",
                width=200,
                command=restore_window.destroy
            ).grid(row=0, column=1, padx=10)
            
        except Exception as e:
            logging.error(f"Error in restore backup window: {str(e)}")
            messagebox.showerror("خطأ", "حدث خطأ أثناء فتح نافذة الاستعادة.")
    
    StyleManager.create_button(
        restore_section,
        text="استعادة نسخة احتياطية",
        width=200,
        command=restore_backup
    ).grid(row=0, column=2, padx=20)
    
    # Back button container
    back_frame = StyleManager.create_frame(frame)
    back_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
    back_frame.grid_columnconfigure(0, weight=1)
    
    # Back button
    StyleManager.create_button(
        back_frame,
        text="العودة",
        style="secondary",
        width=200,
        command=lambda: show_frame(frames["home"])
    ).grid(row=0, column=0)

def setup_send_notification_page():
    frame = frames["send_notification"]
    frame.grid_columnconfigure(0, weight=1)
    
    # Create header
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
        default_message = (
            f"مرحبًا {name},\n"
            f"تذكير بدفع قسط بقيمة {installment_value} ريال في تاريخ {installment_date}.\n"
            f"شكرًا لتعاملك معنا!"
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
            text="{name} - اسم العميل\n{date} - تاريخ القسط\n{value} - قيمة القسط",
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

def check_due_installments():
    """Check for installments due in 3 days and send notifications."""
    while True:
        try:
            logging.info("Starting automatic installment check")
            
            # Read customer data
            data = csv_manager.read_data()
            if not data:
                logging.info("No customer data found for notifications")
                time.sleep(60 * 60)  # Check again in 1 hour
                continue
                
            # Get current date
            today = datetime.now()
            notification_window = 3  # days before payment to send notification
            
            # Track notification results
            success_count = 0
            fail_count = 0
            skip_count = 0
            
            logging.info(f"Checking notifications for {len(data)} customers")
            
            # Check each customer
            for customer in data:
                try:
                    # Get installment dates
                    dates_str = customer.get("Installment Dates", "")
                    if not dates_str:
                        logging.warning(f"Customer {customer['Name']} has no installment dates")
                        continue
                        
                    # Get paid installments to skip them
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                    except:
                        paid_installments = []
                        
                    # Get notified installments
                    try:
                        notified_installments = eval(customer.get("Notified_Installments", "[]"))
                    except:
                        notified_installments = []
                        
                    installment_dates = dates_str.split(";")
                    
                    # Check each installment date
                    for date_str in installment_dates:
                        try:
                            # Skip if already paid or notified
                            if date_str in paid_installments or date_str in notified_installments:
                                continue
                                
                            date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
                            days_until_due = (date - today).days
                            
                            # Send notification if due within notification window
                            if 0 <= days_until_due <= notification_window:
                                logging.info(f"Found upcoming payment for {customer['Name']} due in {days_until_due} days")
                                
                                message = (
                                    f"مرحبًا {customer['Name']},\n"
                                    f"تذكير بدفع قسط بقيمة {customer['Installment Value']} ريال "
                                    f"في تاريخ {date_str}.\n"
                                    f"شكرًا لتعاملك معنا!"
                                )
                                
                                # Prepare phone number
                                phone = customer["Phone"]
                                if not phone.startswith("+"):
                                    phone = "+" + phone
                                
                                # Add a small delay to prevent rate limiting
                                time.sleep(2)
                                
                                max_retries = 2
                                retry_count = 0
                                success = False
                                last_error = None
                                
                                # Try sending with retries
                                while retry_count < max_retries and not success:
                                    retry_count += 1
                                    try:
                                        logging.info(f"Attempt {retry_count} to send notification to {customer['Name']} at {phone}")
                                        
                                        # Send WhatsApp message with increased delays
                                        kit.sendwhatmsg_instantly(
                                            phone_no=phone,
                                            message=message,
                                            wait_time=30,  # Increased wait time to 30 seconds
                                            tab_close=True,
                                            close_time=20  # Increased close time to 20 seconds
                                        )
                                        
                                        # Add additional delay after sending
                                        time.sleep(5)
                                        
                                        # Update notification status for this installment
                                        notified_installments.append(date_str)
                                        customer["Notified_Installments"] = str(notified_installments)
                                        csv_manager.save_data(data)
                                        logging.info(f"Automatic notification sent to {customer['Name']} at {phone} for installment {date_str}")
                                        success = True
                                        success_count += 1
                                        
                                    except Exception as e:
                                        last_error = str(e)
                                        logging.error(f"Error sending WhatsApp message to {customer['Name']} at {phone} (Attempt {retry_count}): {last_error}")
                                        
                                        # Wait before retry
                                        if retry_count < max_retries:
                                            time.sleep(10)  # Increased retry delay to 10 seconds
                                
                                if not success:
                                    fail_count += 1
                                    logging.error(f"Failed to send notification to {customer['Name']} after {max_retries} attempts. Last error: {last_error}")
                                    
                        except ValueError as e:
                            logging.error(f"Error parsing date {date_str} for customer {customer['Name']}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logging.error(f"Error processing customer {customer.get('Name', 'unknown')}: {str(e)}")
                    
            # Log summary of notification attempts
            logging.info(f"Notification check completed. Success: {success_count}, Failed: {fail_count}, Skipped: {skip_count}")
                
        except Exception as e:
            logging.error(f"Error in automatic notification check: {str(e)}")
            
        # Sleep for 1 hour before next check
        time.sleep(60 * 60)

def start_notification_thread():
    """Start a background thread to check for due installments."""
    notification_thread = threading.Thread(target=check_due_installments, daemon=True)
    notification_thread.start()
    logging.info("Notification thread started")

def setup_home_page():
    """Setup the home page with a modern dashboard layout"""
    frame = frames["home"]
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_rowconfigure(0, weight=0)  # Header row
    frame.grid_rowconfigure(1, weight=1)  # First row of cards
    frame.grid_rowconfigure(2, weight=1)  # Second row of cards
    frame.grid_rowconfigure(3, weight=1)  # Third row of cards
    
    # Create header frame with gradient effect
    header_frame = StyleManager.create_frame(frame)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 40))
    header_frame.grid_columnconfigure(0, weight=1)
    
    # Add title with larger font and bold
    StyleManager.create_label(
        header_frame,
        text="نظام إدارة الأقساط",
        font=("Arial", 42, "bold"),
        text_color="#ffffff"
    ).grid(row=0, column=0, pady=(20, 20))
    
    # Menu items configuration
    menu_items = [
        {
            "text": "إضافة عميل",
            "command": lambda: show_frame(frames["add"]),
            "icon": "👤",
            "color": "#4CAF50"
        },
        {
            "text": "عرض العملاء",
            "command": lambda: show_frame(frames["view"]),
            "icon": "📋",
            "color": "#2196F3"
        },
        {
            "text": "إدارة الأقساط",
            "command": lambda: show_frame(frames["manage"]),  # Changed from manage_installments to manage
            "icon": "💰",
            "color": "#9C27B0"
        },
        {
            "text": "النسخ الاحتياطي",
            "command": lambda: show_frame(frames["backup_restore"]),
            "icon": "🔒",
            "color": "#FF9800"
        },
        {
            "text": "إرسال إشعارات",
            "command": lambda: show_frame(frames["send_notification"]),
            "icon": "📨",
            "color": "#E91E63"
        },
        {
            "text": "ملفات العملاء",
            "command": lambda: os.startfile("customer_files"),
            "icon": "📁",
            "color": "#607D8B"
        }
    ]
    
    # Create menu grid with improved spacing and responsiveness
    for i, item in enumerate(menu_items):
        row, col = divmod(i, 2)
        
        # Create a container frame for the button to handle hover effects
        button_container = CTkFrame(
            frame,
            fg_color="transparent"
        )
        button_container.grid(row=row+1, column=col, padx=30, pady=25, sticky="nsew")
        
        # Create button with icon and text
        button = CTkButton(
            button_container,
            text=f"{item['icon']}  {item['text']}",
            command=item["command"],
            width=500,
            height=80,
            corner_radius=15,
            fg_color=item["color"],
            hover_color=item["color"],  # Keep same color on hover
            text_color="#ffffff",
            font=("Arial", 24, "bold"),
            anchor="center"
        )
        button.pack(expand=True, fill="both")
        
        # Create hover effect
        def on_enter(e, button=button):
            # Add white border effect only
            button.configure(border_width=2, border_color="#ffffff")
            
        def on_leave(e, button=button):
            # Remove border effect
            button.configure(border_width=0)
        
        # Bind hover events
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

def refresh_payment_history_views():
    """Refresh all open payment history windows."""
    for widget in app.winfo_children():
        if isinstance(widget, CTkToplevel) and "سجل المدفوعات" in widget.title():
            widget.destroy()

def load_installments_data():
    """Load data into the installments management treeview"""
    try:
        frame = frames["manage"]
        tree = frame.tree
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Get customer data
        data = csv_manager.read_data()
        
        for customer in data:
            try:
                # Get paid and total installments
                paid_installments = eval(customer.get("Paid_Installments", "[]"))
                total_installments = int(customer.get("Installments", 0))
                
                # Get next due date
                installment_dates = customer.get("Installment Dates", "").split(";")
                next_due = ""
                for date in installment_dates:
                    if date not in paid_installments:
                        next_due = date
                        break
                
                # Format amount with two decimal places
                amount = float(customer.get("Amount", 0))
                formatted_amount = f"{amount:.2f}"
                
                # Insert into tree
                item = tree.insert("", "end", values=(
                    customer.get("Name", ""),
                    customer.get("Phone", ""),
                    formatted_amount,
                    total_installments,
                    f"{len(paid_installments)}/{total_installments}",
                    next_due
                ))
                
                # Add color coding based on payment status
                if len(paid_installments) == total_installments:
                    tree.item(item, tags=("paid",))
                else:
                    tree.item(item, tags=("unpaid",))
                
            except Exception as e:
                logging.error(f"Error processing customer in load_installments_data: {str(e)}")
                continue
        
        # Configure payment status styles
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
                
    except Exception as e:
        logging.error(f"Error loading installments data: {str(e)}")
        messagebox.showerror("خطأ", "حدث خطأ أثناء تحميل البيانات")

def show_installment_details(event):
    """Show details of a selected installment"""
    try:
        # Get the selected item
        tree = frames["manage"].tree
        selection = tree.selection()
        if not selection:
            return
            
        # Get customer data
        item = selection[0]
        values = tree.item(item, "values")
        customer_name = values[0]
        phone = values[1]
        
        # Get customer data from CSV
        data = csv_manager.read_data()
        customer = next((c for c in data if c["Name"] == customer_name and c["Phone"] == phone), None)
        if not customer:
            messagebox.showerror("خطأ", "لم يتم العثور على بيانات العميل")
            return
            
        # Create details window
        details_window = CTkToplevel(app)
        details_window.title(f"تفاصيل الأقساط - {customer_name}")
        details_window.geometry("600x400")
        details_window.resizable(False, False)
        
        # Create main frame
        main_frame = StyleManager.create_frame(details_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create header
        header_frame = StyleManager.create_frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        StyleManager.create_label(
            header_frame,
            text=f"تفاصيل أقساط العميل: {customer_name}",
            font_style="subheading"
        ).pack()
        
        # Create treeview
        tree_frame = StyleManager.create_frame(main_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Create treeview
        tree = ttk.Treeview(
            tree_frame,
            columns=("date", "amount", "status"),
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        
        # Configure columns
        tree.heading("date", text="تاريخ القسط")
        tree.heading("amount", text="المبلغ")
        tree.heading("status", text="الحالة")
        
        tree.column("date", width=150, anchor="center")
        tree.column("amount", width=150, anchor="center")
        tree.column("status", width=150, anchor="center")
        
        # Pack tree and scrollbars
        tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        
        y_scroll.config(command=tree.yview)
        x_scroll.config(command=tree.xview)
        
        # Get installment data
        total_amount = float(customer.get("Amount", 0))
        total_installments = int(customer.get("Installments", 0))
        installment_amount = total_amount / total_installments
        paid_installments = eval(customer.get("Paid_Installments", "[]"))
        installment_dates = customer.get("Installment Dates", "").split(";")
        
        # Add installments to tree
        for date in installment_dates:
            if date:
                status = "مدفوع" if date in paid_installments else "غير مدفوع"
                tree.insert("", "end", values=(
                    date,
                    f"{installment_amount:.2f}",
                    status
                ))
        
        # Configure styles
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
        
        # Add buttons frame
        buttons_frame = StyleManager.create_frame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        # Add mark as paid button
        def mark_as_paid():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("تنبيه", "الرجاء اختيار قسط")
                return
                
            item = selection[0]
            values = tree.item(item, "values")
            date = values[0]
            
            if date in paid_installments:
                messagebox.showinfo("معلومات", "هذا القسط مدفوع بالفعل")
                return
                
            if csv_manager.mark_installment_as_paid(customer_name, date):
                tree.item(item, values=(date, values[1], "مدفوع"), tags=("paid",))
                messagebox.showinfo("نجاح", "تم تسجيل القسط كمدفوع")
                load_installments_data()  # Refresh main view
            else:
                messagebox.showerror("خطأ", "فشل في تسجيل القسط كمدفوع")
        
        StyleManager.create_button(
            buttons_frame,
            text="تسجيل كمدفوع",
            command=mark_as_paid
        ).pack(side="right", padx=5)
        
        # Add unmark as paid button
        def unmark_as_paid():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("تنبيه", "الرجاء اختيار قسط")
                return
                
            item = selection[0]
            values = tree.item(item, "values")
            date = values[0]
            
            if date not in paid_installments:
                messagebox.showinfo("معلومات", "هذا القسط غير مدفوع")
                return
                
            if csv_manager.unmark_installment_as_paid(customer_name, date):
                tree.item(item, values=(date, values[1], "غير مدفوع"), tags=("unpaid",))
                messagebox.showinfo("نجاح", "تم إلغاء تسجيل القسط كمدفوع")
                load_installments_data()  # Refresh main view
            else:
                messagebox.showerror("خطأ", "فشل في إلغاء تسجيل القسط كمدفوع")
        
        StyleManager.create_button(
            buttons_frame,
            text="إلغاء تسجيل الدفع",
            command=unmark_as_paid
        ).pack(side="right", padx=5)
        
        # Add close button
        StyleManager.create_button(
            buttons_frame,
            text="إغلاق",
            command=details_window.destroy
        ).pack(side="left")
        
    except Exception as e:
        logging.error(f"Error showing installment details: {str(e)}")
        messagebox.showerror("خطأ", "حدث خطأ أثناء عرض تفاصيل الأقساط")

def perform_installment_search():
    """Search for installments based on the search query"""
    try:
        frame = frames["manage"]
        search_query = frame.search_entry.get().strip().lower()
        tree = frame.tree
        
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        # Get customer data
        data = csv_manager.read_data()
        
        for customer in data:
            try:
                # Check if customer matches search query
                if (search_query in customer.get("Name", "").lower() or 
                    search_query in customer.get("Phone", "").lower()):
                    
                    # Get paid and total installments
                    paid_installments = eval(customer.get("Paid_Installments", "[]"))
                    total_installments = int(customer.get("Installments", 0))
                    
                    # Get next due date
                    installment_dates = customer.get("Installment Dates", "").split(";")
                    next_due = ""
                    for date in installment_dates:
                        if date not in paid_installments:
                            next_due = date
                            break
                    
                    # Format amount with two decimal places
                    amount = float(customer.get("Amount", 0))
                    formatted_amount = f"{amount:.2f}"
                    
                    # Insert into tree
                    item = tree.insert("", "end", values=(
                        customer.get("Name", ""),
                        customer.get("Phone", ""),
                        formatted_amount,
                        total_installments,
                        f"{len(paid_installments)}/{total_installments}",
                        next_due
                    ))
                    
                    # Add color coding based on payment status
                    if len(paid_installments) == total_installments:
                        tree.item(item, tags=("paid",))
                    else:
                        tree.item(item, tags=("unpaid",))
                
            except Exception as e:
                logging.error(f"Error processing customer in search: {str(e)}")
                continue
        
        # Configure payment status styles
        tree.tag_configure("paid", foreground=StyleManager.COLORS["success"])
        tree.tag_configure("unpaid", foreground=StyleManager.COLORS["danger"])
                
    except Exception as e:
        logging.error(f"Error performing installment search: {str(e)}")
        messagebox.showerror("خطأ", "حدث خطأ أثناء البحث")

# Initialize the application and create frames
if __name__ == "__main__":
    try:
        # Initialize the application and create frames
        app = initialize_app()
        if not app:
            raise Exception("Failed to initialize application")
            
        # Setup theme
        try:
            StyleManager.setup_theme()
            logging.info("Theme setup completed")
        except Exception as e:
            logging.error(f"Theme setup failed: {str(e)}")
            messagebox.showwarning("تحذير", "فشل في تحميل النمط. سيتم استخدام النمط الافتراضي.")
        
        # Create main container with padding
        container = StyleManager.create_frame(app)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configure container grid
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # Create frames
        page_names = ["home", "add", "view", "manage", "backup_restore", "send_notification"]  # Removed manage_installments, using manage instead
        
        for name in page_names:
            try:
                frame = StyleManager.create_frame(container)
                frame.grid(row=0, column=0, sticky="nsew")
                frames[name] = frame
                frame.grid_columnconfigure(0, weight=1)
                frame.grid_rowconfigure(0, weight=1)
                logging.info(f"Created frame: {name}")
            except Exception as e:
                logging.error(f"Error creating frame {name}: {str(e)}")
                raise
        
        # Setup all pages with error handling
        setup_functions = [
            ("setup_home_page", setup_home_page),
            ("setup_add_page", setup_add_page),
            ("setup_view_page", setup_view_page),
            ("setup_manage_installments_page", setup_manage_installments_page),
            ("setup_backup_restore_page", setup_backup_restore_page),
            ("setup_send_notification_page", setup_send_notification_page)
        ]
        
        for func_name, func in setup_functions:
            try:
                if not callable(func):
                    raise Exception(f"{func_name} is not defined")
                func()
                logging.info(f"{func_name} completed successfully")
            except Exception as e:
                logging.error(f"Error in {func_name}: {str(e)}")
                raise
        
        # Show home frame and start notification thread
        show_frame(frames["home"])
        start_notification_thread()
        
        # Start the main loop
        main()
    except Exception as e:
        logging.critical(f"Application failed to start: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("خطأ حرج", "فشل في بدء التطبيق. يرجى التأكد من تثبيت جميع المكتبات المطلوبة.")
        sys.exit(1)