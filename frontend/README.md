# Frontend Documentation: Clinical Trial Flow UI

This is the React-based frontend for the Clinical Trial Insights platform. It provides a premium, responsive dashboard for clinical operations teams.

## Tech Stack
- **Framework**: React 18+ with Vite for fast bundling.
- **Styling**: Tailwind CSS for utility-first design and responsive layouts.
- **Animations**: Framer Motion for smooth transitions and modal effects.
- **Icons**: Lucide-React for a clean, consistent icon set.
- **Charts**: Recharts for data visualization (Area charts, Bar charts).

## Folder Structure

### `src/components/`
Contains reusable UI components and layout wrappers:
- **`AppLayout.jsx`**: The core shell with sidebar, header, and themes.
- **`ChatInterface.jsx`**: The AI Copilot side-drawer/floating interface.
- **`Modal.jsx`**: Base component for all dialog boxes.
- **`CommentModal.jsx` & `SiteDetailsModal.jsx`**: Specialized modals for site-specific data.

### `src/pages/`
Main view components rendered within the layout:
- **`Overview.jsx`**: The high-level dashboard with KPIs and trends.
- **`RiskMonitor.jsx`**: Real-time site surveillance table with sorting/filtering.
- **`DataIngestion.jsx`**: Pipeline management UI for uploading new datasets.
- **`Reports.jsx`**: (Mocked) View for managing generated PDF reports.

## Features
- **Real-time AI Copilot**: Integration with the backend chat agent.
- **Dark Mode**: Support for a premium dark theme.
- **Responsive Tables**: Sortable and filterable data grids.
- **Interactive Charts**: Hoverable and dynamic data visualizations.

## Development
To run the frontend locally:
1. Navigate to the `frontend` folder.
2. Run `npm install`.
3. Run `npm run dev`.
4. Ensure the backend is running on `http://localhost:8000`.
