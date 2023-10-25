#!/usr/bin/env python3

import socket
import subprocess
import time
import concurrent.futures
import argparse
import requests
# Added HTTP GET requests to this stress-test-tool.
def http_get_request(target_url, num_requests, delay, verbose=False):
    for _ in range(num_requests):
        try:
            response = requests.get(target_url)
            if verbose:
                print(f"HTTP GET request to {target_url} returned status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send HTTP GET request to {target_url}: {e}")
        time.sleep(delay)

def send_udp_packet(target_host, target_port, packet_size, verbose=False):
    # Function to send a UDP packet
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Generate a large packet with random data
    data = b'X' * packet_size

    udp_socket.sendto(data, (target_host, target_port))

    udp_socket.close()

    if verbose:
        print(f"Sent UDP packet to {target_host}:{target_port} (size: {packet_size} bytes)")

# Other functions, same as before

def parse_args():
    # Function to parse command-line arguments
    parser = argparse.ArgumentParser(description="Python3 program for stress-testing a target host using UDP, ICMP, or TCP.")
    parser.add_argument("test_type", choices=['udp', 'icmp', 'tcp', 'all'], help="Stress-test type (UDP, ICMP, TCP, or ALL)")
    parser.add_argument("target_host", help="Target host IP address")
    parser.add_argument("-n", "--num_threads", type=int, default=5, help="Number of threads for parallel processing")
    parser.add_argument("-d", "--delay", type=float, default=0.1, help="Delay between packets (seconds)")
    parser.add_argument("-p", "--packet_size", type=int, default=1024, help="Packet size for UDP (bytes)")
    parser.add_argument("-x", "--num_packets_udp", type=int, default=100, help="Number of UDP packets to send")
    parser.add_argument("-e", "--timeout_icmp", type=float, default=1.0, help="ICMP test timeout (seconds)")
    parser.add_argument("-o", "--num_packets_icmp", type=int, default=5, help="Number of ICMP packets to send")
    parser.add_argument("-m", "--num_connections_tcp", type=int, default=10, help="Number of TCP connections to make")
    parser.add_argument("-r", "--target_port_udp", type=int, default=5000, help="Target port number for UDP")
    parser.add_argument("-a", "--target_port_tcp", type=int, default=80, help="Target port number for TCP")
    parser.add_argument("--kill", choices=['flood'], help="Kill stress test using maximum values")
    parser.add_argument("--tcp_flood_handshake", action="store_true", help="Perform TCP handshake flood")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    parser.add_argument("--noob", action="store_true", help="Run the script in noob mode")
    parser.add_argument("--http-url", help="Target URL for HTTP GET requests")
    parser.add_argument("--http-requests", type=int, default=100, help="Number of HTTP GET requests to send")
    parser.add_argument("--http-delay", type=float, default=0.1, help="Delay between HTTP GET requests (seconds)")

    return parser.parse_args()

def prompt_for_flags():
    # Function to prompt user for flag values in noob mode
    test_type = input("Enter the stress-test type (UDP, ICMP, TCP, or ALL): ").lower()
    target_host = input("Enter the target host IP address: ")
    num_threads = int(input("Enter the number of threads for parallel processing: "))
    # Prompt for other flags as needed

    args = argparse.Namespace(
        test_type=test_type,
        target_host=target_host,
        num_threads=num_threads,
        # Assign other flag values based on user input
    )
    return args

def print_updated_command():
    # Function to print the updated command with all provided flags and values
    args = parse_args()
    command = "python3 flood.py "

    # Convert Namespace object to dictionary
    args_dict = vars(args)

    for flag, value in args_dict.items():
        # Skip the 'noob' flag and flags with None values
        if flag == "noob" or value is None:
            continue
        elif type(value) == bool:
            # For boolean flags, add the flag name if the value is True
            if value:
                command += f"--{flag} "
        else:
            # For other flags, add the flag name and its value
            command += f"--{flag} {value} "
    if args.test_type == "http":
        if args.http_url:
                command += f"--http-url {args.http_url} "
        if args.http_requests:
                command += f"--http-requests {args.http_requests} "
        if args.http_delay:
                command += f"--http-delay {args.http_delay} "


    print(f"Updated command: {command}")

if __name__ == "__main__":
    args = parse_args()

    if args.kill == "flood":
        args.test_type = "all"
        args.num_threads = 100
        args.packet_size = 65535
        args.num_packets_udp = 5000
        args.delay = 0

    if args.noob:
        args = prompt_for_flags()

    if args.test_type == "all":
        udp_stress_test(args.target_host, args.target_port_udp, args.packet_size, args.num_packets_udp, args.delay, args.num_threads)
        parallel_ping(args.target_host, args.num_packets_icmp, args.timeout_icmp, args.num_threads)
        tcp_stress_test(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.num_threads)
        http_get_request(args.http_url, args.http_requests, args.http_delay, args.verbose)
    elif args.test_type == "http":
        http_get_request(args.http_url, args.http_requests, args.http_delay, args.verbose)
    elif args.test_type == "udp":
        udp_stress_test(args.target_host, args.target_port_udp, args.packet_size, args.num_packets_udp, args.delay, args.num_threads)
    elif args.test_type == "icmp":
        parallel_ping(args.target_host, args.num_packets_icmp, args.timeout_icmp, args.num_threads)
    elif args.test_type == "tcp":
        tcp_stress_test(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.num_threads)
    elif args.tcp_flood_handshake:
        tcp_flood_handshake(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.num_threads)

    # Print the updated command
    print_updated_command()
