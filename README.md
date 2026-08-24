# Minecraft Crossplay Server Setup Guide

## What `docker-compose.yml` Does

When you run `docker compose up -d`, Docker will automatically:
1. **Download & Run Purpur 1.20.4**: High-performance Paper fork optimized for low-resource environments.
2. **Configure Memory & Flags**: Restricts JVM memory to `750M` and applies **Aikar's Garbage Collection Flags** to prevent lag spikes on 1 GB instances.
3. **Open Dual Ports**:
   - `25565 TCP` for **Java Edition** players.
   - `19132 UDP` for **Bedrock Edition** players (iOS, Android, Windows Bedrock, Xbox/PS/Switch).
 4. **Auto-Install Essential Plugins**:
    - **Geyser & Floodgate**: Enables Bedrock players to join without needing Java Minecraft accounts.
    - **BlueMap**: Live 3D interactive web map accessible at `http://your-ip:8100`.
    - **Simple Voice Chat**: Proximity voice chat support (`24454 UDP`).
    - **Playit.gg**: Zero-port-forwarding tunnel for players behind CGNAT / home routers.
    - **DriveBackupV2**: Automated world backups to Google Drive, OneDrive, or Dropbox.
    - **SkinRestorer**: Crossplay skin rendering fix for Bedrock & Java players.
    - **GriefPrevention**: Easy land claiming with a golden shovel.
    - **ViaVersion & ViaBackwards**: Allows players on older (1.8 - 1.19) or newer (1.20.x+) versions to connect.
    - **WorldGuard & WorldEdit**: Used to make spawn cities and build zones protected.
    - **EssentialsX + EssentialsXSpawn**: Manages `/spawn`, `/setspawn`, and player commands.
    - **LuckPerms**: Permission manager for admin/player ranks.
    - **Chunky**: World pre-generator to eliminate chunk-loading lag.
    - **Spark**: Real-time server performance and TPS profiler.

---

## Quick Start: One-Command Automated Setup (`run.py`)

Simply run the universal launcher in your terminal:

```bash
python run.py
```

### What `run.py` Does Automatically:
1. **Detects Environment**: Identifies OS (Windows, Linux distros, macOS), CPU architecture, system RAM, and free disk space.
2. **Auto-Installs Dependencies**: If Docker, Docker Compose, or Java are missing on a clean machine, `run.py` automatically installs them using your system package manager (`apt`, `dnf`, `pacman`, `winget`, `brew`, or `get.docker.com`).
3. **Hardware Auto-Tuning**: Auto-tunes game settings (`VIEW_DISTANCE`, `SIMULATION_DISTANCE`, `MAX_PLAYERS`) based on allocated RAM.
4. **Interactive Prompts**: Asks how much RAM and Disk space you want to allocate for the server, and whether to enable Cloud Backups.
5. **Container Health Monitoring**: Includes automated health checks (`mc-health`) that auto-restart the container if the JVM freezes.
6. **Deploys Minecraft Server**: Creates `./minecraft/`, populates `.env` and `docker-compose.yml`, and starts the container in detached mode.
7. **Prints Connection Credentials**: Fetches public WAN IP and formats a shareable connection card.

### CLI Quick Management Commands:
```bash
python run.py --op <username>   # Instantly grant Operator/Admin to a player
python run.py --status          # View real-time container health & RAM/CPU usage
python run.py --logs            # Stream live server console logs
python run.py --backup          # Create a local timestamped zip backup of your world
python run.py --cleanup         # Stop container, erase data, and free disk space
```

---

## Running on Android Phones (Termux Setup)

You can run this Minecraft Crossplay server directly on Android devices (6–12 GB RAM recommended):

1. **Install Termux** on your Android phone (from [F-Droid](https://f-droid.org/packages/com.termux/)).
2. **Install Java & Python** in Termux:
   ```bash
   pkg update -y && pkg install -y openjdk-21 python git curl
   ```
3. **Clone & Launch**:
   ```bash
   git clone https://github.com/Zcross091/Public-SMP.git
   cd Public-SMP
   python run.py
   ```
   *`run.py` detects Termux, downloads Purpur 1.20.4 + Geyser & Floodgate, auto-tunes RAM for your phone's processor, and launches native Java mode!*

---




## 2. Setting Up the City Spawn & Trading Stations

### A. Making the City Unbreakable
1. Join the server as an operator:
   ```bash
   docker compose exec minecraft-server rcon-cli op <YourMinecraftUsername>
   ```
2. Select the city perimeter with the WorldEdit wand (`//wand`) or by standing at two diagonal corners:
   ```text
   //pos1
   //pos2
   //expand vert
   ```
3. Create the protected region and apply flags:
   ```text
   /rg define spawn_city
   /rg flag spawn_city build deny
   /rg flag spawn_city block-break deny
   /rg flag spawn_city block-place deny
   /rg flag spawn_city pvp deny
   /rg flag spawn_city mob-spawning deny
   /rg flag spawn_city creeper-explosion deny
   /rg flag spawn_city interact allow
   /rg flag spawn_city use allow
   ```
4. Set the world and essentials spawn inside your town hall:
   ```text
   /setworldspawn
   /setspawn
   ```

### B. Creating Custom Villager Traders
1. Look at the spot inside the trading stall where you want the villager:
   ```text
   /shopkeeper villager
   ```
2. Shift + Right-click the newly spawned villager with an empty hand (or a bone) to open the **Trade Editor GUI**.
3. Place the currency / requested items in the top rows and the reward item in the bottom row.
4. Close the inventory. The villager is now locked, invincible, and ready for players to trade.

---

## 3. Pre-generating the World (Prevents Lag)
To avoid lag spikes when players explore new areas:
```text
/chunky radius 3000
/chunky start
```
