# Mining on MacOs

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

1. **Install Dependencies**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create a `.env` file in the project root:
   ```bash
   # Required: Your private key for mining (64 characters after 0x). You need to have some Sonic (S) balance to start mining.
   INFINITY_MINER_PRIVATE_KEY=your_private_key_here

   # Optional: RPC and WebSocket endpoints
   # INFINITY_RPC=https://rpc.soniclabs.com
   # INFINITY_WS=wss://rpc.soniclabs.com

   # Optional: Mining rewards recipient
   # INFINITY_REWARDS_RECIPIENT_ADDRESS=your_address_here

   # Optional: Logging level
   # LOGLEVEL=DEBUG
   ```

3. **Run the Miner**
   ```bash
   python3 src/main.py
   ```

## Configuration Options

- `INFINITY_MINER_PRIVATE_KEY`: Your private key for mining (required)
- `INFINITY_RPC`: Custom RPC endpoint (optional)
- `INFINITY_WS`: Custom WebSocket endpoint (optional)
- `INFINITY_REWARDS_RECIPIENT_ADDRESS`: Address to receive mining rewards (optional)
- `LOGLEVEL`: Set logging verbosity (optional)
