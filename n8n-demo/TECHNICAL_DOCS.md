# n8n Professional Editor - Technical Documentation

## 1. Project Overview
This project provides a professional-grade, visual workflow editor that replicates the core functionality and user experience of the official n8n platform. It is designed to run in resource-constrained environments (like restricted Docker containers) by leveraging a lightweight, no-build architecture while delivering a rich Single Page Application (SPA) experience.

## 2. Architecture

### 2.1 Frontend Architecture
*   **Framework**: React 18 (via Local Assets) for component-based UI.
*   **Flow Engine**: React Flow (via Local Assets) for the node-graph interaction, providing robust drag-and-drop, zooming, and connection logic.
*   **Styling**: Tailwind CSS (via Local Assets) for rapid, modern, utility-first styling that mimics the n8n dark theme.
*   **Build System**: **None**. The application uses native ES Modules and Babel Standalone (in-browser) to allow for sophisticated JSX development without requiring a heavy `npm install` or build step (Webpack/Vite), avoiding disk space issues.
*   **Asset Delivery**: All static libraries (React, ReactDOM, Babel, Tailwind, ReactFlow, Lucide) are cached locally in `public/pro/libs` to ensure reliability for users in China and offline environments, eliminating dependency on external CDNs.

### 2.2 Backend Architecture
*   **Runtime**: Node.js
*   **Server**: Express.js
*   **API Endpoints**:
    *   `GET /api/workflow`: Retrieves the current workflow JSON.
    *   `POST /api/workflow`: Saves workflow changes.
    *   `POST /api/run`: Executes the workflow by spawning the verification script.
*   **Persistence**: File-system based (JSON files).

## 3. Installation & Deployment Guide

### 3.1 Prerequisites
*   Node.js v14+
*   npm

### 3.2 Installation
1.  Navigate to the project directory:
    ```bash
    cd /path/to/project
    ```
2.  Install minimal backend dependencies:
    ```bash
    npm install express axios cheerio cors
    ```
    *(Note: This project is optimized to use minimal disk space (~50MB))*

### 3.3 Running the Server
Start the backend server which serves the frontend:
```bash
node server.js
```
The application will be available at `http://localhost:3000`.

## 4. User Operation Manual

### 4.1 Interface Overview
The editor consists of three main areas:
1.  **Canvas (Center)**: The main workspace where you build your workflow.
2.  **Node Palette (Left)**: A list of available nodes (Start, HTTP Request, etc.).
3.  **Properties Panel (Right)**: Appears when a node is selected, allowing you to configure its settings.

### 4.2 Building a Workflow
1.  **Add Node**: Drag a node type from the **Node Palette** onto the **Canvas**.
2.  **Connect Nodes**: Click and drag from the handle (dot) on the right of one node to the handle on the left of another.
3.  **Configure Node**: Click a node to open the **Properties Panel**.
    *   *HTTP Request*: Enter the URL to fetch.
    *   *Code*: (Advanced) View the JavaScript logic (read-only in this demo version).

### 4.3 Execution
1.  Click the **Execute Workflow** button in the top toolbar.
2.  The workflow status will change to "Running".
3.  Once complete, the **Execution Results** panel will appear at the bottom, showing the data passed through the workflow.

### 4.4 Data Management
*   **Import/Export**: Use the standard JSON format compatible with n8n. (Feature integrated into the save/load mechanism).
*   **Undo/Redo**: Use the buttons in the bottom-left of the canvas to revert changes.

## 5. Compatibility
*   **Browser**: Optimized for Google Chrome (Latest).
*   **Resolution**: Best viewed on 1920x1080 or higher.
