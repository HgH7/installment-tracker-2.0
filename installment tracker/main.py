"""
Main application entry point for the Installment Tracker.
"""
import customtkinter
from customtkinter import CTk
from tkinter import messagebox
import os
import sys
import logging
import traceback

# Setup logging
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

logging.basicConfig(
    filename=os.path.join(logs_dir, 'app.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# Import utilities and managers
from utils import StyleManager, CSVManager, FileManager
from helpers import refresh_treeview, show_payment_history, export_to_excel, refresh_payment_history_views

# Import page modules
from pages.home_page import setup_home_page

# Import notification module
from notifications import start_notification_thread

# Global variables
app = None
frames = {}

# Initialize managers
csv_filename = "data/customers.csv"
backup_folder = "data/backups"
csv_manager = CSVManager(csv_filename, backup_folder)
file_manager = FileManager("data/customer_files")


def initialize_app():
    """Initialize the main application window with error handling"""
    global app
    try:
        logging.info("Starting application initialization...")
        
        app = CTk()
        if not app:
            raise Exception("Failed to create main window")
            
        app.geometry("1280x800")
        app.title("نظام إدارة الأقساط")
        
        try:
            app._set_appearance_mode("dark")
            logging.info("Appearance mode set successfully")
        except Exception as e:
            logging.error(f"Failed to set appearance mode: {str(e)}")
        
        try:
            screen_width = app.winfo_screenwidth()
            screen_height = app.winfo_screenheight()
            x = (screen_width - 1280) // 2
            y = (screen_height - 800) // 2
            app.geometry(f"1280x800+{x}+{y}")
            logging.info("Window centered successfully")
        except Exception as e:
            logging.error(f"Failed to center window: {str(e)}")
        
        return app
    except Exception as e:
        logging.critical(f"Failed to initialize application: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("خطأ حرج", "فشل في بدء التطبيق. يرجى مراجعة ملف السجل للتفاصيل.")
        sys.exit(1)


def show_frame(frame):
    """Show the specified frame and hide others"""
    for f in frames.values():
        f.grid_remove()
    frame.grid()


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


if __name__ == "__main__":
    try:
        # Import page setup functions dynamically to avoid circular imports
        from pages.add_page import setup_add_page
        from pages.view_page import setup_view_page
        from pages.manage_page import setup_manage_installments_page
        from pages.backup_page import setup_backup_restore_page
        from pages.notifications_page import setup_send_notification_page
        
        # Initialize the application
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
        
        # Create main container
        container = StyleManager.create_frame(app)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # Create frames
        page_names = ["home", "add", "view", "manage", "backup_restore", "send_notification"]
        
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
            ("setup_home_page", lambda: setup_home_page(frames["home"], frames, show_frame)),
            ("setup_add_page", lambda: setup_add_page(frames["add"], frames, show_frame, app, csv_manager, file_manager)),
            ("setup_view_page", lambda: setup_view_page(frames["view"], frames, show_frame, app, csv_manager)),
            ("setup_manage_installments_page", lambda: setup_manage_installments_page(frames["manage"], frames, show_frame, app, csv_manager)),
            ("setup_backup_restore_page", lambda: setup_backup_restore_page(frames["backup_restore"], frames, show_frame, csv_manager)),
            ("setup_send_notification_page", lambda: setup_send_notification_page(frames["send_notification"], frames, show_frame, app, csv_manager))
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
        start_notification_thread(csv_manager)
        
        # Start the main loop
        main()
    except Exception as e:
        logging.critical(f"Application failed to start: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("خطأ حرج", "فشل في بدء التطبيق. يرجى التأكد من تثبيت جميع المكتبات المطلوبة.")
        sys.exit(1)