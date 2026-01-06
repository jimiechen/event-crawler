# Stock Verify Server

Independent verification system for the Stock Monitor Backend.

## Features
- **Isolation**: Completely separate codebase and dependencies.
- **One-Click Cleanup**: Cascading delete of stock data for clean testing.
- **Simulation Engine**: Time-compressed simulation of T+1 trading days.
- **Verification**: Automated checks against Acceptance Plan 603601.
- **Web Console**: Simple UI for controlling the verification process.

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**
   Ensure `.env` matches your database configuration.
   ```
   DB_HOST=192.168.1.6
   DB_PORT=3306
   ...
   ```

3. **Run Server**
   ```bash
   python main.py
   ```
   Access the console at `http://localhost:8001`.

## Usage Guide

1. **Open Console**: Navigate to `http://localhost:8001`.
2. **Enter Stock Code**: e.g., `603601`.
3. **Clear Data**: Click "Clear Data" to reset the environment.
4. **Ingest**: Click "Trigger Ingest" to call the backend crawler.
5. **Verify**: Check status to ensure data is loaded.
6. **Simulate**: Click "Simulate T+1" to insert mock daily data.
7. **Verify Again**: Check if scoring and alerts have been triggered (requires backend scheduler to be running or manually triggered).

## Architecture

- `app/services/cleaner.py`: Handles data deletion.
- `app/services/simulator.py`: Generates mock K-line data.
- `app/services/verifier.py`: Validates database state.
- `app/services/backend_client.py`: Interacts with the main backend system.

## Security
- API endpoints support HTTPS (when deployed behind Nginx/Traefik).
- Database credentials are managed via environment variables.
