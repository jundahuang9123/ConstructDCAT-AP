import sys
from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, Namespace

def generate_mermaid(ttl_file: Path) -> str:
    g = Graph()
    g.parse(ttl_file, format="turtle")
    
    classes = set()
    relationships = []
    
    # Collect Classes
    for s, p, o in g.triples((None, RDF.type, OWL.Class)):
        classes.add(s)
    for s, p, o in g.triples((None, RDF.type, RDFS.Class)):
        classes.add(s)

    # Collect SubClassOf
    for s, o in g.subject_objects(RDFS.subClassOf):
        if s in classes and o in classes:
            relationships.append((o, s, " <|-- ")) # Inheritance

    # Collect Properties (symbolic)
    # This is a simplification. DCAT-AP has many properties. 
    # We'll just graph relationships between known classes.
    for s, p, o in g:
        if s in classes and o in classes:
            # s -> o relationship
            label = p.split('#')[-1].split('/')[-1]
            relationships.append((s, o, f" --o : {label} "))

    # Generate Mermaid Syntax
    lines = ["classDiagram"]
    
    # Add Nodes
    for cls in classes:
        name = cls.split('#')[-1].split('/')[-1]
        # Sanitize name
        name = name.replace('-', '_').replace('.', '_')
        lines.append(f"    class {name}")
        # Optionally add label if available
        # string_label = g.value(cls, RDFS.label)
        # if string_label: lines.append(f"    {class_name} : {string_label}")

    # Add Edges
    for s, o, rel in relationships:
        s_name = s.split('#')[-1].split('/')[-1].replace('-', '_').replace('.', '_')
        o_name = o.split('#')[-1].split('/')[-1].replace('-', '_').replace('.', '_')
        if s_name != o_name:
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
        
    diagram = generate_mermaid(input_file)
    print(diagram)
