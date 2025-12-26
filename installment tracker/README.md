# Installment Tracker Application

A desktop GUI application for managing customer installments with payment tracking, file attachments, and WhatsApp notifications.

## Project Structure

```
installment tracker/
├── main.py                    # Main application entry point
├── utils.py                   # Utility classes (StyleManager, CSVManager, FileManager, DatePicker)
├── helpers.py                 # Shared helper functions
├── notifications.py           # Background notification thread
├── pages/                     # Page modules
│   ├── home_page.py          # Home/dashboard page
│   ├── add_page.py           # Add customer page
│   ├── view_page.py          # View customers page
│   ├── manage_page.py        # Manage installments page
│   ├── backup_page.py        # Backup/restore page
│   └── notifications_page.py # Send notifications page
├── data/                      # Application data
│   ├── customers.csv         # Customer data file
│   ├── backups/              # CSV backup files
│   └── customer_files/       # Customer document files
├── logs/                      # Application logs
│   └── app.log
├── config/                    # Configuration files
│   └── PyWhatKit_DB.txt     # WhatsApp configuration
└── requirements.txt          # Python dependencies
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Features

- ✅ Add and manage customers
- ✅ Track installment payments
- ✅ File attachments per customer
- ✅ Payment history tracking
- ✅ Excel export
- ✅ Backup and restore functionality
- ✅ WhatsApp notifications (manual and automated)
- ✅ Search and filter customers

## Data Organization

- **Customer Data**: Stored in `data/customers.csv`
- **Backups**: Automatically saved to `data/backups/`
- **Customer Files**: Stored in `data/customer_files/` (organized by customer name)
- **Logs**: Application logs in `logs/app.log`

## Notes

- The application uses a modular structure for better maintainability
- All data files are organized in the `data/` directory
- Configuration files are in the `config/` directory
- Logs are stored in the `logs/` directory

