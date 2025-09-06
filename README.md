# DAO GolemDB Interface

A decentralized interface for uploading, searching, and downloading files using GolemDB - a blockchain-based decentralized database.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MetaMask browser extension

### 1. Backend Setup

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Start the API server
python app.py
```

Backend will run on `http://localhost:8000`

### 2. Frontend Setup

```bash
# Install Node.js dependencies
cd frontend
npm install

# Start the development server
npm start
```

Frontend will run on `http://localhost:3000`

### 3. Configuration (Optional)

The system works with default settings. To customize:

```bash
# Copy and edit environment files
cp .env.example .env
cd frontend && cp .env.example .env
```

## Features

- **File Upload**: Drag & drop files with TTL control (5 min - 7 days)
- **Search**: Find files by annotations or metadata
- **Download**: Retrieve files directly from search results
- **MetaMask Integration**: Automatic network switching to ETH Warsaw Holesky
- **Expiration Tracking**: Visual indicators for file expiration status

## Usage

1. Open the app at `http://localhost:3000`
2. Connect MetaMask (auto-switches to ETH Warsaw Holesky)
3. Upload files with drag & drop, choose expiration time
4. Search files using the Search tab
5. Download files with the Download button in search results

## Network Configuration

- **Network**: ETH Warsaw Holesky
- **Chain ID**: 60138453033
- **RPC URL**: https://ethwarsaw.holesky.golemdb.io/rpc

MetaMask will automatically add this network when you connect.

## API Documentation

Full API docs available at: `http://localhost:8000/docs`

## Troubleshooting

**Backend won't start?**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Frontend won't start?**
```bash
cd frontend
npm install
npm start
```

**MetaMask connection issues?**
- Make sure MetaMask is installed
- Allow the site to connect to MetaMask
- The app will automatically switch to the correct network