# Agentic RAG Frontend

This is a sophisticated frontend application designed to visualize and interact with a complex Agentic AI system. It provides a user-friendly interface for chatting with the AI, exploring its architecture, and understanding its knowledge graph.

## Features

- **Multi-tab Interface**: Separate tabs for different functionalities: Chat, Architecture, Agents View, and Knowledge Graph.
- **Session Management**: Create, switch, rename, and delete chat sessions. All sessions are persisted in `localStorage`.
- **Interactive Diagrams**: Visualize the AI's architecture and agent flows using the `vis.js` library.
- **Real-time Thinking Stream**: See the AI's "thinking" process in real-time as it formulates a response.
- **Markdown Support**: Render Markdown content for detailed explanations and chat messages.
- **Knowledge Graph Visualization**: Explore the underlying Neo4j knowledge graph.
- **Common Use Cases**: A library of pre-defined prompts to demonstrate the AI's capabilities.

## Project Structure

```
Frontend/
|-- Agentic_AI/
|   |-- langgraph_agentic_ai/
|       |-- server.py               # Python backend server
|       |-- tools/
|           |-- neo4j_connector.py  # Neo4j connection logic
|-- public/
|   |-- queries.json                # Pre-defined prompts for "Common Use Cases"
|   |-- model_explanation.txt       # Text content for the Architecture tab
|-- src/
|   |-- assets/
|   |   |-- architectural-diagram.jpg # Image for the Architecture tab
|   |-- App.jsx                     # Main application component, handles routing and layout
|   |-- ArchitectureTab.jsx         # Component for the "Architecture" tab
|   |-- InteractiveDiagram.jsx      # Component to display the main architecture diagram
|   |-- SimpleFlowDiagram.jsx       # Component for the simplified "Agents View" diagram
|   |-- VisNetwork.jsx              # Reusable component for creating vis.js network graphs
|   |-- ThinkingStream.jsx          # Component to display the real-time thinking stream
|   |-- SidebarContent.jsx          # Renders markdown content in the sidebars
|   |-- main.jsx                    # Entry point of the React application
|   |-- index.css                   # Global CSS styles
|-- README.md                       # This file
|-- package.json                    # Project dependencies and scripts
|-- vite.config.js                  # Vite configuration
|-- tailwind.config.js              # Tailwind CSS configuration
```

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3.x and pip

### Installation

1.  **Frontend**:
    ```bash
    npm install
    ```

2.  **Backend**:
    ```bash
    cd Agentic_AI/langgraph_agentic_ai
    pip install -r requirements.txt # Assuming a requirements.txt file exists
    ```

### Running the Application

1.  **Start the Backend Server**:
    ```bash
    cd Agentic_AI/langgraph_agentic_ai
    python server.py
    ```

2.  **Start the Frontend Development Server**:
    In the root `Frontend` directory:
    ```bash
    npm run dev
    ```

The application will be available at `http://localhost:5173`.

## Tabs Explained

### 1. Chat Tab

This is the main interaction point with the Agentic AI.

- **Chat Interface**: A standard chat interface where you can send messages to the AI and receive responses.
- **Session Management**: On the left sidebar, you can manage your chat sessions.
    - **New Session**: Start a new conversation.
    - **Switch Sessions**: Click on a session to load its history.
    - **Rename Sessions**: Double-click on a session name to rename it.
    - **Delete Sessions**: Click the 'x' button to delete a session (with a confirmation prompt).
- **Thinking Stream**: On the right sidebar, you can see the AI's internal "thinking" process as it generates a response. This provides insight into the steps it takes.
- **Common Use Cases**: A list of pre-defined questions that you can click to send to the AI. This is populated from `public/queries.json`.

### 2. Architecture Tab

This tab provides a high-level overview of the entire AI system's architecture.

- **Main Diagram**: An interactive diagram (`InteractiveDiagram.jsx`) showing the major components and workflows of the system. This is a static image (`src/assets/architectural-diagram.jpg`).
- **Explanation**: A detailed explanation of the architecture, loaded from `public/model_explanation.txt` and displayed in the right sidebar.

### 3. Agents View Tab

This tab offers a more detailed, interactive look at the flow between different AI agents.

- **Simplified Flow Diagram**: A `vis.js` powered diagram (`SimpleFlowDiagram.jsx`) that visualizes the sequence of agents involved in processing a request.
    - Nodes are color-coded: blue for inputs, green for agents, and yellow for data stores.
    - The layout is sequential and fixed from top to bottom.
- **Detailed Descriptions**: Clicking on a node in the diagram displays detailed information about that agent or data store in the sidebars. The content for these descriptions is defined in `src/SimpleFlowData.js`.

### 4. Knowledge Graph Tab

This tab provides a direct visualization of the Neo4j knowledge graph that the AI uses.

- **Graph Visualization**: Uses `VisNetwork.jsx` to render the graph, showing nodes and relationships.
- **Layout**: The graph uses a physics-based layout engine to organize the nodes. The layout stabilizes and then freezes to make it easier to explore.

## Key Components

- **`App.jsx`**: The root component that manages the application's state, including the active tab and session management logic (`useSessionManager` hook). It lays out the main UI structure.
- **`VisNetwork.jsx`**: A generic and reusable component that wraps the `vis-network` library. It's used by the Knowledge Graph and the old Architecture tab to render network diagrams. It's configured to disable the physics engine after stabilization to prevent the layout from constantly changing.
- **`SimpleFlowDiagram.jsx`**: A specialized component for the "Agents View" tab. It uses hardcoded coordinates from `SimpleFlowData.js` to create a clean, top-to-bottom flow diagram.
- **`InteractiveDiagram.jsx`**: A simple component used in the "Architecture" tab to display the main architectural image.
- **`SidebarContent.jsx`**: A component responsible for rendering Markdown content in the sidebars, used across multiple tabs. It uses `react-markdown` and `remark-gfm`.
- **`useSessionManager` hook (in `App.jsx`)**: A custom hook that encapsulates all the logic for session management, including creating, switching, renaming, and deleting sessions, and persisting them to `localStorage`.

## Backend Server (`server.py`)

The backend is a Python server (likely using Flask or FastAPI) that exposes an API for the frontend to communicate with the Agentic AI.

- **`/chat` endpoint**: The primary endpoint for sending user messages to the AI and receiving a streamed response.
- **`/get_graph` endpoint**: An endpoint to fetch data for the Knowledge Graph visualization.
- **`neo4j_connector.py`**: A module that handles the connection to the Neo4j database. 