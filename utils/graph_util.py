# graph util
from IPython.display import Image, display


def display_graph(graph):
    try:
        display(Image(graph.get_graph(xray=True).draw_mermaid_png()))
    except Exception as e:
        # This requires some extra dependencies and is optional
        print(f"Error: {e}")
        pass

def save_graph_as_png(graph, filename="graph.png"):
    try:
        # Generate the PNG image of the graph
        png_data = graph.get_graph(xray=True).draw_mermaid_png()
        
        # Save the PNG to a file
        with open(filename, "wb") as file:
            file.write(png_data)
        
        print(f"Graph saved successfully as '{filename}'")
    except Exception as e:
        print(f"Error saving graph: {e}")

def stream_op(graph, user_input):
    for output in graph.stream(user_input):  # to stream step by step output
        for key, value in output.items():
            print(f"here is output from {key}")
            print("_______")
            print(value)
            print("\n")
