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


def create_graph_from_json(file: UploadFile):
    """
    Create a graph representation from the json file.

    Args:
       json file containing conections between nodes.
        assume in the form of:
       [
           {"source":<str>, "target":<str>, "weight":<float>, "bidirectional":<bool>},
           ...
       ]
    """
    content = file.file.read()
    data = json.loads(content)
    graph = Graph()

    for row in data:
        source_id = str(row["source"])
        target_id = str(row["target"])
        weight = float(row["weight"])
        bidirectional = bool(row["bidirectional"])

        # add nodes if they don't exist
        if source_id not in graph.nodes:
            graph.add_node(Node(source_id, np.inf))
        if target_id not in graph.nodes:
            graph.add_node(Node(target_id, np.inf))

        # add edge
        graph.add_edge(graph.nodes[source_id], graph.nodes[target_id], weight, bidirectional)

    # debug print
    # graph.print()

    return graph


def create_graph_from_csv(file: UploadFile):
    """
    Create a graph representation from the csv file.

    Args:
        file (UploadFile): The uploaded file containing adjacency matrix.
        assume in the form of:
        node_id   node_id1, node_id2, ..., node_idn
        node_id1  inf     , dist12    ..., dist1n
        node_id2  dist21  , inf     , ..., dist2n
        ...       ...     , ...     , ..., ...
        node_idn  distn1  ,   distn2, ..., inf
    """
    reader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
    headers = reader.fieldnames  # get the node ids
    n = len(headers)
    # graph construction
    graph = Graph()

    # add nodes
    for i in range(1, n):
        node_id = headers[i]
        graph.add_node(Node(node_id, np.inf))

    # get the distance values and add edges
    for row in reader:
        from_node_id = row[headers[0]]
        for i in range(1, n):
            to_node_id = headers[i]
            if from_node_id != to_node_id:
                weight = float(row[to_node_id]) if row[to_node_id] != 'inf' else np.inf
                graph.add_edge(graph.nodes[from_node_id], graph.nodes[to_node_id], weight, bidirectional=True)

    # degug print
    # graph.print()

    return graph

@app.post("/upload_graph_json/")
async def create_upload_file(file: UploadFile):
    global active_graph  # <-- make sure to declare this

    # Check if the uploaded file is a JSON file
    if not file.filename.endswith(".json"):
        return {"Upload Error": "Invalid file type"}

    try:
        import json
        contents = await file.read()
        json.loads(contents)  # validate JSON

        # Build and store the graph properly
        file.file.seek(0)  # reset file pointer after .read()
        active_graph = create_graph_from_json(file)

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
    