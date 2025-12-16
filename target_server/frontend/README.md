# Target Server Frontend

React + Vite frontend for the Universal AI Ops Engineer target server monitoring dashboard.

## Features

- **Real-time Health Monitoring**: Connects to FastAPI backend to display system health
- **Interactive Dashboard**: Clean UI with Mantine components
- **Auto-refresh**: Automatic data updates every 30 seconds on dashboard, 10 seconds on health monitor
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Graceful handling of backend connection issues

## Tech Stack

- **React 18** - Modern React with hooks
- **Vite** - Fast build tool and dev server
- **Mantine** - Modern React component library
- **Axios** - HTTP client for API calls
- **React Router** - Client-side routing

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- FastAPI backend running on `http://localhost:8000`

### Installation

1. Install dependencies:

```bash
cd target_server/frontend
npm install
```

2. Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   │   └── Header.jsx      # Navigation header
│   ├── pages/              # Page components
│   │   ├── Dashboard.jsx   # Main dashboard
│   │   └── HealthMonitor.jsx # Detailed health monitoring
│   ├── services/           # API services
│   │   └── api.js          # Axios configuration and API calls
│   ├── App.jsx             # Main app component with routing
│   ├── main.jsx            # React entry point
│   └── index.css           # Global styles
├── package.json
├── vite.config.js          # Vite configuration with proxy
└── README.md
```

## API Integration

The frontend connects to the FastAPI backend with the following endpoints:

- `GET /healthz` - Simple health check
- `GET /api/v1/health` - Detailed health with system metrics

Vite is configured with a proxy to forward API requests to the backend during development.

## Development

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build locally

### Development Setup

1. Start the FastAPI backend:

```bash
cd target_server/backend
uvicorn main:app --reload
```

2. Start the React frontend:

```bash
cd target_server/frontend
npm run dev
```

Both servers will be running:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Production Deployment

Build the frontend for production:

```bash
npm run build
```

The built files will be in the `dist/` directory, ready for deployment to any static hosting service.

## Features Overview

### Dashboard

- Overall system health status
- Database connection status
- System metrics (CPU, memory, disk usage)
- API information and uptime

### Health Monitor

- Raw API responses from both health endpoints
- Auto-refresh toggle
- Connection status information
- JSON-formatted response data
