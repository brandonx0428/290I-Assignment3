from fastapi import FastAPI, File, UploadFile, HTTPException
from typing_extensions import Annotated
import uvicorn
from utils import *
from dijkstra import dijkstra

# create FastAPI app
app = FastAPI()

# global variable for active graph
active_graph = None

@app.get("/")
async def root():
    return {"message": "Welcome to the Shortest Path Solver!"}


@app.post("/upload_graph_json/")
async def create_upload_file(file: UploadFile):
    # Check if the uploaded file is a JSON file
    if not file.filename.endswith(".json"):
        return {"Upload Error": "Invalid file type"}

    try:
        # Optionally read and validate the content here (if needed)
        contents = await file.read()
        # Just to confirm it's valid JSON syntax
        import json
        json.loads(contents)
        active_graph = json.loads(contents)
        # If successful
        return {"Upload Success": file.filename}

    except json.JSONDecodeError:
        return {"Upload Error": "Invalid JSON content"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/solve_shortest_path/start_node_id={start_node_id}&end_node_id={end_node_id}")
async def get_shortest_path(start_node_id: str, end_node_id: str):
    global active_graph

    # 1. Check if graph exists
    if active_graph is None:
        return {"Solver Error": "No active graph, please upload a graph first."}

    # 2. Validate node IDs
    if start_node_id not in active_graph.nodes or end_node_id not in active_graph.nodes:
        return {"Solver Error": "Invalid start or end node ID."}

    # 3. Run Dijkstra
    start_node = active_graph.nodes[start_node_id]
    dijkstra(active_graph, start_node)

    end_node = active_graph.nodes[end_node_id]

    # 4. Construct shortest path
    if np.isinf(end_node.dist):
        return {"shortest_path": None, "total_distance": None}

    path = []
    current = end_node
    while current is not None:
        path.insert(0, current.id)
        current = current.prev

    return {"shortest_path": path, "total_distance": end_node.dist}

if __name__ == "__main__":
    print("Server is running at http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
    