"""
Background notification module for automatic installment reminders.
"""
import threading
import time
import logging
import pywhatkit as kit
from datetime import datetime
from utils import CSVManager

notification_enabled = True  # Enable notifications by default


def check_due_installments(csv_manager: CSVManager):
    """Check for installments due in 3 days and send notifications."""
    while True:
        if not notification_enabled:
            time.sleep(60 * 60)
            continue
        try:
            logging.info("Starting automatic installment check")
            
            data = csv_manager.read_data()
            if not data:
                logging.info("No customer data found for notifications")
                time.sleep(60 * 60)
                continue
                
            today = datetime.now()
            notification_window = 3
            
            success_count = 0
            fail_count = 0
            skip_count = 0
            
            logging.info(f"Checking notifications for {len(data)} customers")
            
            for customer in data:
                try:
                    dates_str = customer.get("Installment Dates", "")
                    if not dates_str:
                        logging.warning(f"Customer {customer['Name']} has no installment dates")
                        continue
                        
                    try:
                        paid_installments = eval(customer.get("Paid_Installments", "[]"))
                    except:
                        paid_installments = []
                        
                    try:
                        notified_installments = eval(customer.get("Notified_Installments", "[]"))
                    except:
                        notified_installments = []
                        
                    installment_dates = dates_str.split(";")
                    
                    for date_str in installment_dates:
                        try:
                            if date_str in paid_installments or date_str in notified_installments:
                                continue
                                
                            date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
                            days_until_due = (date - today).days
                            
                            if 0 <= days_until_due <= notification_window:
                                logging.info(f"Found upcoming payment for {customer['Name']} due in {days_until_due} days")
                                
                                message = (
                                    f"مرحبًا {customer['Name']},\n"
                                    f"تذكير بدفع قسط بقيمة {customer['Installment Value']} ريال "
                                    f"في تاريخ {date_str}.\n"
                                    f"شكرًا لتعاملك معنا!"
                                )
                                
                                phone = customer["Phone"]
                                if not phone.startswith("+"):
                                    phone = "+" + phone
                                
                                time.sleep(2)
                                
                                max_retries = 2
                                retry_count = 0
                                success = False
                                last_error = None
                                
                                while retry_count < max_retries and not success:
                                    retry_count += 1
                                    try:
                                        logging.info(f"Attempt {retry_count} to send notification to {customer['Name']} at {phone}")
                                        
                                        kit.sendwhatmsg_instantly(
                                            phone_no=phone,
                                            message=message,
                                            wait_time=30,
                                            tab_close=True,
                                            close_time=20
                                        )
                                        
                                        time.sleep(5)
                                        
                                        notified_installments.append(date_str)
                                        customer["Notified_Installments"] = str(notified_installments)
                                        csv_manager.save_data(data)
                                        logging.info(f"Automatic notification sent to {customer['Name']} at {phone} for installment {date_str}")
                                        success = True
                                        success_count += 1
                                        
                                    except Exception as e:
                                        last_error = str(e)
                                        logging.error(f"Error sending WhatsApp message to {customer['Name']} at {phone} (Attempt {retry_count}): {last_error}")
                                        
                                        if retry_count < max_retries:
                                            time.sleep(10)
                                
                                if not success:
                                    fail_count += 1
                                    logging.error(f"Failed to send notification to {customer['Name']} after {max_retries} attempts. Last error: {last_error}")
                                    
                        except ValueError as e:
                            logging.error(f"Error parsing date {date_str} for customer {customer['Name']}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logging.error(f"Error processing customer {customer.get('Name', 'unknown')}: {str(e)}")
                    
            logging.info(f"Notification check completed. Success: {success_count}, Failed: {fail_count}, Skipped: {skip_count}")
                
        except Exception as e:
            logging.error(f"Error in automatic notification check: {str(e)}")
            
        time.sleep(60 * 60)


def start_notification_thread(csv_manager: CSVManager):
    """Start a background thread to check for due installments."""
    notification_thread = threading.Thread(target=check_due_installments, args=(csv_manager,), daemon=True)
    notification_thread.start()
    logging.info("Notification thread started")

