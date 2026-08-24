#!/usr/bin/env python3
"""
Cross-Platform Minecraft Crossplay Server Automated Setup & Launcher
Supports: Windows, Linux (Ubuntu, Debian, Fedora, Arch, CentOS, etc.), and macOS.
"""

import os
import sys
import platform
import subprocess
import shutil
import urllib.request
import json
import re
import socket
import time

# --- Color Constants for Terminal Output ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}=== {msg} ==={Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}[✓] {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKBLUE}[i] {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}[!] {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}[✗] {msg}{Colors.ENDC}")

# --- Helper Functions ---

def run_command(cmd, check=False, capture_output=True, shell=False):
    """Run shell command and return CompletedProcess."""
    try:
        if isinstance(cmd, str) and not shell:
            import shlex
            cmd_args = shlex.split(cmd)
        else:
            cmd_args = cmd
        res = subprocess.run(
            cmd_args,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            shell=shell
        )
        if check and res.returncode != 0:
            print_error(f"Command failed: {cmd}\nError: {res.stderr}")
        return res
    except Exception as e:
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr=str(e))

def detect_os():
    """Detect operating system details."""
    system = platform.system()
    distro = ""
    if system == "Linux":
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.strip().split("=")[1].strip('"')
                        break
        elif shutil.which("lsb_release"):
            res = run_command("lsb_release -si")
            distro = res.stdout.strip().lower()
    return system, distro

def get_total_ram_gb():
    """Detect total system RAM in Gigabytes."""
    system = platform.system()
    try:
        if system == "Linux":
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if "MemTotal" in line:
                            parts = line.split()
                            kb = int(parts[1])
                            return round(kb / (1024 * 1024), 2)
        elif system == "Windows":
            res = run_command("powershell -Command \"(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize\"", shell=True)
            if res.returncode == 0 and res.stdout.strip().isdigit():
                kb = int(res.stdout.strip())
                return round(kb / (1024 * 1024), 2)
        elif system == "Darwin":
            res = run_command("sysctl -n hw.memsize")
            if res.returncode == 0 and res.stdout.strip().isdigit():
                b = int(res.stdout.strip())
                return round(b / (1024 ** 3), 2)
    except Exception:
        pass
    return 8.0  # Safe fallback estimate

def get_free_disk_space_gb(path="."):
    """Get free disk space in GB for given path."""
    try:
        usage = shutil.disk_usage(os.path.abspath(path))
        return round(usage.free / (1024 ** 3), 2)
    except Exception:
        return 50.0  # Fallback

def parse_memory_input(user_input, default_gb=4.0):
    """Parse user memory input (e.g. '4G', '4000M', '4', '4.5G') to normalized string format like '4G' or '4000M'."""
    val = user_input.strip().upper()
    if not val:
        return f"{int(default_gb)}G" if default_gb.is_integer() else f"{default_gb}G"
    
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([MG])?B?$", val)
    if match:
        num = float(match.group(1))
        unit = match.group(2) if match.group(2) else "G"
        if unit == "G":
            return f"{int(num)}G" if num.is_integer() else f"{num}G"
        else:
            return f"{int(num)}M"
    return f"{int(default_gb)}G"

def parse_memory_to_mb(mem_str):
    """Convert memory string like '4G' or '512M' to megabytes int."""
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([MG])?$", mem_str.upper())
    if not match:
        return 4096
    num = float(match.group(1))
    unit = match.group(2) if match.group(2) else "G"
    if unit == "G":
        return int(num * 1024)
    return int(num)

def check_command_exists(cmd):
    """Check if binary or subcommand exists."""
    return shutil.which(cmd) is not None

def check_docker_compose():
    """Check if 'docker compose' or 'docker-compose' works."""
    res1 = run_command("docker compose version")
    if res1.returncode == 0:
        return "docker compose"
    res2 = run_command("docker-compose version")
    if res2.returncode == 0:
        return "docker-compose"
    return None

def install_system_dependencies(system, distro):
    """Attempt auto-installation of missing dependencies (Docker, Java, etc.) on unprepared systems."""
    print_header("Checking & Installing System Requirements")
    
    docker_ok = check_command_exists("docker")
    compose_cmd = check_docker_compose()
    java_ok = check_command_exists("java")
    
    if docker_ok and compose_cmd:
        print_success("Docker & Docker Compose are installed.")
        return compose_cmd
    
    print_warning("Required tools (Docker/Docker Compose) were not found on this machine.")
    print_info("Attempting automated dependency installation...")
    
    if system == "Linux":
        print_info(f"Detected Linux distribution: {distro or 'generic'}")
        is_sudo = os.geteuid() == 0 if hasattr(os, "geteuid") else False
        sudo_prefix = "" if is_sudo else "sudo "
        
        # Package manager installation
        if distro in ["ubuntu", "debian", "pop", "mint"]:
            cmd = f"{sudo_prefix}apt-get update && {sudo_prefix}apt-get install -y docker.io docker-compose-v2 curl openjdk-21-jre-headless"
            print_info(f"Running: {cmd}")
            subprocess.run(cmd, shell=True)
        elif distro in ["fedora", "rhel", "centos", "rocky", "alma"]:
            cmd = f"{sudo_prefix}dnf install -y docker docker-compose curl java-21-openjdk"
            print_info(f"Running: {cmd}")
            subprocess.run(cmd, shell=True)
            subprocess.run(f"{sudo_prefix}systemctl enable --now docker", shell=True)
        elif distro in ["arch", "manjaro"]:
            cmd = f"{sudo_prefix}pacman -S --noconfirm docker docker-compose curl openjdk-src"
            print_info(f"Running: {cmd}")
            subprocess.run(cmd, shell=True)
            subprocess.run(f"{sudo_prefix}systemctl enable --now docker", shell=True)
        else:
            # Fallback official docker script
            print_info("Using official Docker installation script (get.docker.com)...")
            subprocess.run(f"curl -fsSL https://get.docker.com | {sudo_prefix}sh", shell=True)
        
        # Add user to docker group
        user = os.getenv("USER") or os.getenv("LOGNAME")
        if user and not is_sudo:
            subprocess.run(f"{sudo_prefix}usermod -aG docker {user}", shell=True)
            subprocess.run(f"{sudo_prefix}systemctl enable --now docker 2>/dev/null", shell=True)
            
    elif system == "Darwin":
        if check_command_exists("brew"):
            print_info("Installing Docker & Java via Homebrew...")
            subprocess.run("brew install --cask docker", shell=True)
            subprocess.run("brew install docker-compose openjdk", shell=True)
        else:
            print_error("Homebrew not found. Please install Docker Desktop for macOS from: https://www.docker.com/products/docker-desktop/")
            
    elif system == "Windows":
        if check_command_exists("winget"):
            print_info("Installing Docker Desktop via Winget...")
            subprocess.run("winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements", shell=True)
        else:
            print_error("Winget not found. Please download Docker Desktop for Windows: https://www.docker.com/products/docker-desktop/")

    compose_cmd = check_docker_compose()
    if not compose_cmd:
        print_error("Docker is still not accessible. If you just installed Docker, you may need to restart your terminal or log out and back in.")
        sys.exit(1)
        
    return compose_cmd

def get_public_ip():
    """Fetch public WAN IP address using reliable IP services."""
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://ipinfo.io/ip"
    ]
    for url in services:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                ip = response.read().decode('utf-8').strip()
                if ip and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                    return ip
        except Exception:
            continue
    return "YOUR_PUBLIC_IP"

def get_local_ip():
    """Get LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

# --- Main Program Logic ---

def cleanup_server():
    """Stop container, remove docker volumes, and delete minecraft directory to free up space."""
    print_header("Cleaning Up Minecraft Server & Freeing Space")
    compose_cmd = check_docker_compose() or "docker compose"
    base_dir = os.path.abspath(os.path.dirname(__file__))
    minecraft_dir = os.path.join(base_dir, "minecraft")
    
    if os.path.exists(minecraft_dir):
        print_info("Stopping container and removing volumes...")
        subprocess.run(f"{compose_cmd} down -v", cwd=minecraft_dir, shell=True)
        print_info("Deleting minecraft server folder...")
        shutil.rmtree(minecraft_dir, ignore_errors=True)
    
    creds_file = os.path.join(base_dir, "Join_Credentials.txt")
    if os.path.exists(creds_file):
        os.remove(creds_file)
        
    print_success("Cleanup complete! All server containers, data, and allocated disk space have been freed.")

def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["--cleanup", "-c", "cleanup"]:
        cleanup_server()
        return

    print(f"{Colors.BOLD}{Colors.OKGREEN}")
    print(r"""
  __  __ _                              __ _    _____                         
 |  \/  (_)                            / _| |  / ____|                        
 | \  / |_ _ __   ___  ___ _ __ __ _ _| |_| |_| (___   ___ _ __ v ___ _ __    
 | |\/| | | '_ \ / _ \/ __| '__/ _` |_   _| __|\___ \ / _ \ '__/ | / _ \ '__|  
 | |  | | | | | |  __/ (__| | | (_| | | | | |_ ____) |  __/ |  | |  __/ |     
 |_|  |_|_|_| |_|\___|\___|_|  \__,_| |_|  \__|_____/ \___|_|  |_|\___|_|     
    """)
    print(f"       >>> Java & Bedrock Crossplay Server Auto-Installer <<<{Colors.ENDC}\n")

    # 1. OS & Specs Detection
    system, distro = detect_os()
    total_ram = get_total_ram_gb()
    free_disk = get_free_disk_space_gb()

    print_header("System Environment Detected")
    print_info(f"Operating System  : {system} ({distro if distro else platform.release()})")
    print_info(f"Total System RAM  : {total_ram} GB")
    print_info(f"Free Disk Space   : {free_disk} GB")

    # 2. Check & Install System Dependencies
    compose_cmd = install_system_dependencies(system, distro)

    # 3. Interactive User Prompts
    print_header("Server Resource Allocation")
    
    # Calculate recommended RAM
    rec_ram = max(2.0, round(total_ram * 0.5, 1))
    if rec_ram > 8.0:
        rec_ram = 8.0

    print(f"{Colors.OKCYAN}How much RAM would you like to allocate for the Minecraft server?{Colors.ENDC}")
    print(f"  [Default: {int(rec_ram)}G | System Total: {total_ram}GB]")
    ram_input = input(f"{Colors.BOLD}Enter RAM amount (e.g., 2G, 4G, 8G) [{int(rec_ram)}G]: {Colors.ENDC}").strip()
    allocated_ram_str = parse_memory_input(ram_input, default_gb=rec_ram)
    ram_mb = parse_memory_to_mb(allocated_ram_str)
    
    # Init memory calculation (75% of max)
    init_mb = int(ram_mb * 0.75)
    init_ram_str = f"{init_mb}M"

    print_success(f"Allocated Max RAM : {allocated_ram_str} (Init RAM: {init_ram_str})")

    print(f"\n{Colors.OKCYAN}How much Disk Space (max storage) allocation would you like to reserve?{Colors.ENDC}")
    print(f"  [Default: 20G | Available Free Disk: {free_disk}GB]")
    disk_input = input(f"{Colors.BOLD}Enter Disk Space limit (e.g., 10G, 20G, 50G) [20G]: {Colors.ENDC}").strip()
    allocated_disk_str = disk_input.upper() if disk_input else "20G"
    
    print_success(f"Reserved Disk Limit: {allocated_disk_str}")

    # 4. Folder Setup
    base_dir = os.path.abspath(os.path.dirname(__file__))
    minecraft_dir = os.path.join(base_dir, "minecraft")
    data_dir = os.path.join(minecraft_dir, "data")
    
    os.makedirs(data_dir, exist_ok=True)
    print_success(f"Created Minecraft server directory: {minecraft_dir}")

    # 5. Environment & Docker Compose Generation
    env_content = f"""# Automatically Generated Minecraft Server Environment Config
INIT_MEMORY={init_ram_str}
MAX_MEMORY={allocated_ram_str}
CONTAINER_MAX_MEMORY={allocated_ram_str}
JAVA_PORT=25565
BEDROCK_PORT=19132
SERVER_TYPE=PURPUR
MINECRAFT_VERSION=1.20.4
MAX_PLAYERS=20
MOTD=§a§lCrossplay Server §7| §eJava §6& §eBedrock
"""
    env_file_path = os.path.join(minecraft_dir, ".env")
    with open(env_file_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    print_success("Generated .env configuration file.")

    # Copy docker-compose.yml to minecraft folder
    template_compose = os.path.join(base_dir, "docker-compose.yml")
    target_compose = os.path.join(minecraft_dir, "docker-compose.yml")
    shutil.copyfile(template_compose, target_compose)
    print_success("Copied optimized docker-compose.yml to server directory.")

    # 6. Launch Server
    print_header("Launching Minecraft Server Container")
    print_info("Starting container via Docker Compose... (Downloading images & plugins on first boot)")
    
    launch_res = subprocess.run(
        f"{compose_cmd} up -d",
        cwd=minecraft_dir,
        shell=True
    )

    if launch_res.returncode != 0:
        print_error("Failed to launch Docker container. Check Docker service status.")
        sys.exit(1)

    print_success("Minecraft Server container launched successfully in detached mode!")

    # 7. Network Credentials & Public Login Info
    print_info("Fetching public IP and connection details...")
    public_ip = get_public_ip()
    local_ip = get_local_ip()

    credentials_card = f"""
====================================================================
               MINECRAFT CROSSPLAY SERVER CREDENTIALS
====================================================================

  [★] JAVA EDITION (PC / Mac / Linux)
      - Supported Versions : 1.8.x through Latest (1.20.x+)
      - Server Address     : {public_ip}
      - Default Port       : 25565

  [★] BEDROCK EDITION (Android / iOS / Windows Bedrock / Consoles)
      - Server Address     : {public_ip}
      - Server Port        : 19132

  [i] LOCAL LAN ADDRESS (For devices on same home network)
      - LAN IP Address     : {local_ip}

--------------------------------------------------------------------
  [🔑] ADMIN OPERATOR PERMISSION (RCON):
      Run the following command to give yourself OP / Admin:
      
      cd minecraft
      {compose_cmd} exec minecraft-server rcon-cli op <YourMinecraftUsername>
--------------------------------------------------------------------
  [📋] LOGS & MANAGEMENT:
      - View live logs     : {compose_cmd} logs -f
      - Stop server        : {compose_cmd} down
      - Easy Cleanup       : python run.py --cleanup
====================================================================
"""

    # Print Card to Terminal
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}{credentials_card}{Colors.ENDC}")

    # Save Credentials File inside minecraft directory and parent directory
    creds_file_1 = os.path.join(minecraft_dir, "Join_Credentials.txt")
    creds_file_2 = os.path.join(base_dir, "Join_Credentials.txt")
    
    with open(creds_file_1, "w", encoding="utf-8") as f:
        f.write(credentials_card)
    with open(creds_file_2, "w", encoding="utf-8") as f:
        f.write(credentials_card)
        
    print_success(f"Connection credentials saved to: {creds_file_1}")
    print_success("Sharing is ready! Paste the address and port above to invite your friends!")
    print_info("To completely remove the server & delete allocated files later, run: python run.py --cleanup")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
