from flask import Flask, render_template, request, redirect, url_for, jsonify
from markupsafe import Markup
from SPARQLWrapper import SPARQLWrapper, JSON
from pyvis.network import Network
import networkx as nx
from rapidfuzz import process, fuzz

app = Flask(__name__)

DBPEDIA_SPARQL_ENDPOINT = "https://dbpedia.org/sparql"

NODE_COLORS = {
    "Person": "#1f78b4",
    "Place": "#33a02c",
    "Event": "#e31a1c",
    "Thing": "#ff7f00",
    "Default": "#6a3d9a"
}

def query_dbpedia_for_person_fuzzy(name):
    sparql = SPARQLWrapper(DBPEDIA_SPARQL_ENDPOINT)
    sparql.setQuery(f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?person ?label ?rank WHERE {{
      ?person a dbo:Person ;
              rdfs:label ?label .
      OPTIONAL {{ ?person dbo:wikiPageRank ?rank }}
      FILTER (langMatches(lang(?label), "EN"))
      FILTER (CONTAINS(LCASE(?label), LCASE("{name}")))
    }}
    ORDER BY DESC(?rank)
    LIMIT 200
    """)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
    except Exception as e:
        print("SPARQL error:", e)
        return [], "Wystąpił błąd podczas przetwarzania zapytania."

    all_people = []
    for r in results["results"]["bindings"]:
        all_people.append({
            "uri": r["person"]["value"],
            "label": r["label"]["value"]
        })

    best_matches = process.extract(name, [p["label"] for p in all_people], limit=20, scorer=fuzz.partial_ratio)

    matched = []
    for match, score, idx in best_matches:
        if score > 60:
            matched.append(all_people[idx])

    return matched, None

def query_dbpedia_relations_with_types(resource_uri):
    sparql = SPARQLWrapper(DBPEDIA_SPARQL_ENDPOINT)
    sparql.setQuery(f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?property ?value ?valueLabel ?type WHERE {{
      <{resource_uri}> ?property ?value .
      OPTIONAL {{
        ?value rdf:type ?type .
        FILTER(?type IN (dbo:Person, dbo:Place, dbo:Event, dbo:Thing))
      }}
      OPTIONAL {{
        ?value rdfs:label ?valueLabel .
        FILTER (langMatches(lang(?valueLabel), "EN"))
      }}
    }} LIMIT 50
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    relations = []
    for r in results["results"]["bindings"]:
        prop = r["property"]["value"].split('/')[-1]
        val_uri = r["value"]["value"]
        val_label = r.get("valueLabel", {}).get("value", val_uri.split('/')[-1].replace('_', ' '))
        val_type = "Default"
        if "type" in r:
            t = r["type"]["value"]
            if "Person" in t:
                val_type = "Person"
            elif "Place" in t:
                val_type = "Place"
            elif "Event" in t:
                val_type = "Event"
            elif "Thing" in t:
                val_type = "Thing"
        relations.append((prop, val_label, val_uri, val_type))
    return relations

def build_knowledge_graph(root_uri, root_label):
    G = nx.DiGraph()
    G.add_node(root_uri, label=root_label, type="Person")
    nodes_to_expand = [(root_uri, 0)]
    max_nodes = 50
    max_edges = 100
    edges_count = 0

    while nodes_to_expand and len(G.nodes) < max_nodes and edges_count < max_edges:
        current_uri, level = nodes_to_expand.pop(0)
        if level >= 2:
            continue
        relations = query_dbpedia_relations_with_types(current_uri)
        for prop, val_label, val_uri, val_type in relations:
            if len(G.nodes) >= max_nodes or edges_count >= max_edges:
                break
            if val_uri not in G.nodes:
                G.add_node(val_uri, label=val_label, type=val_type)
                if level + 1 < 2:
                    nodes_to_expand.append((val_uri, level + 1))
            G.add_edge(current_uri, val_uri, label=prop)
            edges_count += 1
    return G

def generate_pyvis_graph(G, physics=True):
    net = Network(height="600px", width="100%", directed=True, notebook=False)
    net.barnes_hut()
    for node, data in G.nodes(data=True):
        node_type = data.get("type", "Default")
        color = NODE_COLORS.get(node_type, NODE_COLORS["Default"])
        net.add_node(node, label=data.get("label", node), color=color)
    for source, target, data in G.edges(data=True):
        net.add_edge(source, target, label=data.get("label", ""))
    net.set_options("""
    var options = {
      "physics": {
        "enabled": %s,
        "barnesHut": { "gravitationalConstant": -8000, "springLength": 250 }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """ % ("true" if physics else "false"))
    return net.generate_html()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("query")
        results, error = query_dbpedia_for_person_fuzzy(name)
        return render_template("index.html", results=results, error=error)
    return render_template("index.html")

@app.route("/details/")
def details():
    resource = request.args.get("resource")
    if not resource:
        return redirect(url_for("index"))
    label = resource.split('/')[-1].replace('_', ' ')
    G = build_knowledge_graph(resource, label)
    graph_html = generate_pyvis_graph(G)
    return render_template("details.html", graph_html=Markup(graph_html))

@app.route("/node_description", methods=["GET"])
def node_description():
    node_uri = request.args.get("node_uri")
    if not node_uri:
        return jsonify({"error": "Missing node_uri"}), 400

    sparql = SPARQLWrapper(DBPEDIA_SPARQL_ENDPOINT)
    sparql.setQuery(f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    SELECT ?abstract WHERE {{
      <{node_uri}> dbo:abstract ?abstract .
      FILTER (langMatches(lang(?abstract), "EN"))
    }} LIMIT 1
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if results["results"]["bindings"]:
        abstract = results["results"]["bindings"][0]["abstract"]["value"]
    else:
        abstract = "No description available."

    return jsonify({"description": abstract})

if __name__ == "__main__":
    app.run(debug=True)