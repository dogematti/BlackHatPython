#!/usr/bin/env python3

import socket
import argparse
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from scapy.all import send  # Importing the send function from Scapy
from scapy.layers.inet import IP, ICMP  # Importing IP and ICMP

def parallel_http_get_request(target_url, num_requests, delay, num_threads, verbose=False):
    """
    Sends HTTP GET requests in parallel to the specified target URL.
    """
    def single_request():
        try:
            response = requests.get(target_url)
            if verbose:
                print(f"HTTP GET request to {target_url} returned status code: {response.status_code}")
            time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(f"Failed to send HTTP GET request to {target_url}: {e}")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(lambda _: single_request(), range(num_requests))

def parallel_send_udp_packet(target_host, target_port, packet_size, num_packets, num_threads, verbose=False):
    """
    Sends UDP packets in parallel to the specified target host and port.
    """
    def single_udp_packet():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            data = b'X' * packet_size
            udp_socket.sendto(data, (target_host, target_port))
            if verbose:
                print(f"Sent UDP packet to {target_host}:{target_port} (size: {packet_size} bytes)")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(lambda _: single_udp_packet(), range(num_packets))

def tcp_flood_handshake(target_host, target_port, num_connections, verbose=False):
    """
    Attempts to establish multiple TCP connections to the target host and port.
    """
    for _ in range(num_connections):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                tcp_socket.connect((target_host, target_port))
                if verbose:
                    print(f"Established TCP connection to {target_host}:{target_port}")
        except socket.error as e:
            print(f"Failed to establish TCP connection to {target_host}:{target_port}: {e}")

def send_icmp_packet(target_host, num_packets, timeout, verbose=False):
    """
    Sends ICMP packets (like ping requests) to the specified target host.
    """
    packet = IP(dst=target_host)/ICMP()
    for _ in range(num_packets):
        send(packet, timeout=timeout, verbose=verbose)

def tcp_test(target_host, target_port, num_connections, verbose=False):
    """
    Opens TCP connections to the target host and port, optionally sending data.
    """
    for _ in range(num_connections):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                tcp_socket.connect((target_host, target_port))
                # Optionally send data here
                if verbose:
                    print(f"Connected to TCP {target_host}:{target_port}")
        except socket.error as e:
            print(f"TCP test failed for {target_host}:{target_port}: {e}")

def parse_args():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Python3 program for stress-testing a target host using various methods. By Dogematti")
    parser.add_argument("test_type", choices=['udp', 'icmp', 'tcp', 'all', 'http'], help="Stress-test type")
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
    parser.add_argument("--http-url", help="Target URL for HTTP GET requests")
    parser.add_argument("--http-requests", type=int, default=100, help="Number of HTTP GET requests to send")
    parser.add_argument("--http-delay", type=float, default=0.1, help="Delay between HTTP GET requests (seconds)")
    return parser.parse_args()

def execute_all_tests(args):
    """
    Executes all types of tests (HTTP, UDP, ICMP, TCP) on the target.
    """
    parallel_http_get_request(args.http_url, args.http_requests, args.http_delay, args.num_threads, args.verbose)
    parallel_send_udp_packet(args.target_host, args.target_port_udp, args.packet_size, args.num_packets_udp, args.num_threads, args.verbose)
    send_icmp_packet(args.target_host, args.num_packets_icmp, args.timeout_icmp, args.verbose)
    tcp_test(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.verbose)

def main():
    """
    Main function to execute the stress tests based on the provided arguments.
    """
    args = parse_args()

    if args.kill == "flood":
        args.num_threads = 10
        # Set other parameters to their maximum values as needed

    # Executing stress tests based on the chosen test type
    if args.test_type == "all":
        execute_all_tests(args)
    elif args.test_type == "http":
        parallel_http_get_request(args.http_url, args.http_requests, args.http_delay, args.num_threads, args.verbose)
    elif args.test_type == "udp":
        parallel_send_udp_packet(args.target_host, args.target_port_udp, args.packet_size, args.num_packets_udp, args.num_threads, args.verbose)
    elif args.test_type == "icmp":
        send_icmp_packet(args.target_host, args.num_packets_icmp, args.timeout_icmp, args.verbose)
    elif args.test_type == "tcp":
        tcp_test(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.verbose)
    elif args.tcp_flood_handshake:
        tcp_flood_handshake(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.verbose)

if __name__ == "__main__":
    main()
