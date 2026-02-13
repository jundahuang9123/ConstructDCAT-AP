import sys
from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, Namespace, BNode

def generate_mermaid(ttl_file: Path) -> str:
    g = Graph()
    g.parse(ttl_file, format="turtle")
    
    classes = set()
    relationships = []
    
    # Collect Classes
    for s, p, o in g.triples((None, RDF.type, OWL.Class)):
        if not isinstance(s, BNode):
            classes.add(s)
    for s, p, o in g.triples((None, RDF.type, RDFS.Class)):
        if not isinstance(s, BNode):
            classes.add(s)

    # Collect SubClassOf
    for s, o in g.subject_objects(RDFS.subClassOf):
        if not isinstance(s, BNode) and not isinstance(o, BNode):
            if s in classes and o in classes:
                relationships.append((o, s, " <|-- ", "")) # Inheritance

    # Collect Properties (Relationship between classes)
    # We look for ObjectProperties or just usage in the graph
    # To avoid graph explosion, we only show properties where both domain and range are known classes
    # OR where we can infer from usage that s and o are classes we know.
    
    # Let's iterate over all triples. If s and o are in our 'classes' set, we draw a link.
    for s, p, o in g:
        if s in classes and o in classes:
            if p == RDF.type or p == RDFS.subClassOf:
                continue
            
            # Label
            label = p.split('#')[-1].split('/')[-1]
            relationships.append((s, o, " ..> ", label))

    # Generate Mermaid Syntax
    lines = ["classDiagram"]
    lines.append("    %% Styles")
    lines.append("    classDef dcat fill:#f9f,stroke:#333,stroke-width:2px;")
    
    # Add Nodes
    for cls in classes:
        name = cls.split('#')[-1].split('/')[-1]
        name = name.replace('-', '_').replace('.', '_')
        lines.append(f"    class {name}")
        
    # Add Edges (deduplicated)
    seen_edges = set()
    for s, o, rel, label in relationships:
        s_name = s.split('#')[-1].split('/')[-1].replace('-', '_')
        o_name = o.split('#')[-1].split('/')[-1].replace('-', '_')
        
        # Self loops can be messy
        if s_name == o_name:
            continue
            
        edge_key = (s_name, o_name, rel, label)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)
        
        if label:
            lines.append(f"    {s_name}{rel}{o_name} : {label}")
        else:
            lines.append(f"    {s_name}{rel}{o_name}")

    return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python viz_gen.py <ttl_file>")
        sys.exit(1)
        
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"File not found: {input_file}")
        sys.exit(1)
        
    try:
        diagram = generate_mermaid(input_file)
        print(diagram)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
