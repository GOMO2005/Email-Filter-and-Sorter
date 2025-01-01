import imaplib
import email
from email.header import decode_header
import pandas as pd
import re
from datetime import datetime

# User input
email_user = input("Enter your email address: ")
email_pass = input("Enter your email password: ")
keywords = input("Enter keywords for filtering (comma separated): ").split(",")

# Connect to the email server
def connect_to_email():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")  # For Gmail. Use appropriate server for other providers
    mail.login(email_user, email_pass)
    mail.select("inbox")  # Select inbox
    return mail

# Fetch emails from inbox
def fetch_emails(mail):
    status, messages = mail.search(None, "ALL")  # Fetch all emails
    email_ids = messages[0].split()  # List of email IDs
    return email_ids

# Process and filter emails
def process_emails(mail, email_ids, keywords):
    email_data = []
    
    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")  # Fetch email
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                sender = msg.get("From")
                date = msg.get("Date")
                
                # Extract email content (body)
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            try:
                                body = part.get_payload(decode=True).decode('utf-8')  # Try UTF-8 decoding
                            except UnicodeDecodeError:
                                try:
                                    body = part.get_payload(decode=True).decode('ISO-8859-1')  # Fallback to ISO-8859-1
                                except UnicodeDecodeError:
                                    body = part.get_payload(decode=True).decode(errors='ignore')  # Ignore undecodable parts
                            break
                else:
                    try:
                        body = msg.get_payload(decode=True).decode('utf-8')  # Try UTF-8 decoding
                    except UnicodeDecodeError:
                        try:
                            body = msg.get_payload(decode=True).decode('ISO-8859-1')  # Fallback to ISO-8859-1
                        except UnicodeDecodeError:
                            body = msg.get_payload(decode=True).decode(errors='ignore')  # Ignore undecodable parts

                # Clean up the body text by removing unnecessary \r\n characters
                body = body.replace("\r\n", " ").replace("\n", " ").strip()

                # Check if email contains any of the input keywords
                matched_keywords = [keyword for keyword in keywords if re.search(r'\b' + re.escape(keyword.strip()) + r'\b', subject, re.IGNORECASE) or re.search(r'\b' + re.escape(keyword.strip()) + r'\b', body, re.IGNORECASE)]
                
                # Only process emails with matched keywords
                if matched_keywords:
                    # Determine email date and categorize it (recent vs old)
                    email_date = email.utils.parsedate_to_datetime(date).replace(tzinfo=None)  # Remove timezone info
                    email_age = (datetime.now() - email_date).days
                    recency = "Recent" if email_age <= 1 else "Old"
                    
                    # Generate email summary (first 100 chars of body)
                    email_summary = body[:100]
                    
                    # Store email information
                    email_info = {
                        "sender_email": sender,
                        "subject": subject,
                        "date_received": date,
                        "keywords_matched": matched_keywords,
                        "email_age": recency,
                        "email_summary": email_summary
                    }
                    
                    email_data.append(email_info)
                
    return email_data

# Display emails in DataFrame format
def display_email_data(email_data):
    df = pd.DataFrame(email_data)
    print("\nFiltered and Sorted Emails:")
    print(df)

# Main execution
def main():
    mail = connect_to_email()
    email_ids = fetch_emails(mail)
    email_data = process_emails(mail, email_ids, keywords)
    display_email_data(email_data)

# Run the main function
if __name__ == "__main__":
    main()
