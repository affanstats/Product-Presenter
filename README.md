# Project Setup and Running Instructions

This project consists of three main components: Frontend, Backend (Agent), and Backend (API).

## Prerequisites

- Node.js and npm installed
- Python installed
- uv package manager
- LiveKit

## Setup Instructions

### 1. Frontend Setup
```bash
cd frontend
```

1. Edit environment variables
2. Install dependencies:
```bash
npm i
```
3. Run the frontend:
```bash
npm run dev
```

### 2. Backend (Agent) Setup
```bash
cd backend
```

1. Install uv and LiveKit (refer to documentation)
2. Edit environment variables:
```bash
lk app env -w
```
3. Download required files:
```bash
uv run main.py download-files
```
4. Run the agent:
```bash
uv run main.py dev
```

### 3. Backend (API) Setup
```bash
cd backend
```

Run the API server:
```bash
uv run api.py
```

## Running the Full Application

1. Start the Frontend (in one terminal)
2. Start the Backend Agent (in another terminal)
3. Start the Backend API (in a third terminal)

All three components need to be running simultaneously for the application to work properly.