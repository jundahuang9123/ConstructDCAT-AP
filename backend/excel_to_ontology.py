import pandas as pd
from rdflib import Graph, Literal, BNode, Namespace, RDF, RDFS, OWL, XSD
from rdflib.namespace import DCAT, DCTERMS, FOAF, SKOS
import sys
import os

# Define Namespaces
EXT = Namespace("http://example.org/ns/dcat-ap-ext#")
SH = Namespace("http://www.w3.org/ns/shacl#")

def clean_uri(uri_str, namespaces):
    """
    Expands a CURIE (e.g., 'dcat:Dataset') to a full URI using the provided namespaces.
    If it's already a full URI or unknown prefix, returns as is (or handled by rdflib).
    """
    if not isinstance(uri_str, str):
        return None
    if ":" in uri_str and not uri_str.startswith("http"):
        prefix, local = uri_str.split(":", 1)
        if prefix in namespaces:
            return namespaces[prefix][local]
        # Keep as string if prefix unknown, but ideally should be known
        return uri_str 
    return uri_str

def safe_literal(val, datatype=None):
    if pd.isna(val) or val == "":
        return None
    if datatype:
        return Literal(val, datatype=datatype)
    return Literal(val)

def run():
    print("Loading base ontology from backend/dcat3.ttl...")
    base_ttl = "backend/dcat3.ttl"
    excel_file = "backend/ontology_definition.xlsx"
    
    if not os.path.exists(base_ttl):
        print(f"Error: Base file {base_ttl} not found.")
        return
    if not os.path.exists(excel_file):
        print(f"Error: Excel file {excel_file} not found.")
        return

    # Initialize Graphs
    g = Graph()
    g.parse(base_ttl, format="turtle")
    
    # Bind common prefixes
    g.bind("ext", EXT)
    g.bind("dcat", DCAT)
    g.bind("dct", DCTERMS)
    
    # SHACL Graph
    sg = Graph()
    sg.bind("sh", SH)
    sg.bind("ext", EXT)
    sg.bind("dcat", DCAT)
    sg.bind("dct", DCTERMS)

    # Helper dict for namespaces to expand strict CURIEs
    ns_map = {
        "dcat": DCAT,
        "dct": DCTERMS,
        "foaf": FOAF,
        "skos": SKOS,
        "ext": EXT,
        "xsd": XSD,
        "rdfs": RDFS,
        "owl": OWL,
        "sh": SH
    }

    print("Reading Excel...")
    df_classes = pd.read_excel(excel_file, sheet_name="Classes")
    df_props = pd.read_excel(excel_file, sheet_name="Properties")

    # --- Process Classes ---
    print(f"Processing {len(df_classes)} classes...")
    for _, row in df_classes.iterrows():
        class_uri_str = row.get("Class URI")
        if pd.isna(class_uri_str): continue
        
        class_node = clean_uri(class_uri_str, ns_map)
        parent_node = clean_uri(row.get("Parent Class"), ns_map)
        label = row.get("Label")
        desc = row.get("Description")

        # Definition
        g.add((class_node, RDF.type, OWL.Class))
        g.add((class_node, RDF.type, RDFS.Class))
        
        if label and not pd.isna(label):
            g.add((class_node, RDFS.label, Literal(label, lang="en")))
        if desc and not pd.isna(desc):
            g.add((class_node, RDFS.comment, Literal(desc, lang="en")))
        
        # Subclass
        if parent_node:
            g.add((class_node, RDFS.subClassOf, parent_node))

    # --- Process Properties & SHACL ---
    print(f"Processing {len(df_props)} properties...")
    
    # Group properties by Domain to create NodeShapes
    shapes_by_domain = {}

    for _, row in df_props.iterrows():
        prop_uri_str = row.get("Property URI")
        if pd.isna(prop_uri_str): continue

        prop_node = clean_uri(prop_uri_str, ns_map)
        domain_node = clean_uri(row.get("Domain"), ns_map)
        range_node = clean_uri(row.get("Range"), ns_map)
        min_count = row.get("Min Count")
        max_count = row.get("Max Count")
        label = row.get("Label")
        desc = row.get("Description")

        # 1. Ontology Definition (RDF/OWL)
        g.add((prop_node, RDF.type, RDF.Property))
        if label and not pd.isna(label):
            g.add((prop_node, RDFS.label, Literal(label, lang="en")))
        if desc and not pd.isna(desc):
            g.add((prop_node, RDFS.comment, Literal(desc, lang="en")))
        
        # We don't strictly enforce rdfs:domain/range in the ontology graph 
        # as it can infer too much, but let's add them if they are explicit.
        if domain_node:
            g.add((prop_node, RDFS.domain, domain_node))
        if range_node:
            g.add((prop_node, RDFS.range, range_node))

        # 2. SHACL Shape Definition
        if domain_node:
            if domain_node not in shapes_by_domain:
                shapes_by_domain[domain_node] = []
            
            # Create a property shape structure
            p_shape = BNode()
            sg.add((p_shape, SH.path, prop_node))
            
            # Constraints
            if not pd.isna(min_count) and str(min_count).strip() != "":
                sg.add((p_shape, SH.minCount, Literal(int(min_count))))
            if not pd.isna(max_count) and str(max_count).strip() != "":
                sg.add((p_shape, SH.maxCount, Literal(int(max_count))))
            
            # Datatype or Class constraint
            if range_node:
                # Heuristic: if range starts with xsd, it's a datatype, else class
                # This is a bit loose but works for simple Excel input
                range_str = str(range_node)
                if "xml" in range_str.lower() or "xsd" in range_str.lower():
                    sg.add((p_shape, SH.datatype, range_node))
                else:
                    sg.add((p_shape, SH.class_, range_node))
            
            if desc and not pd.isna(desc):
                sg.add((p_shape, SH.description, Literal(desc, lang="en")))
                
            shapes_by_domain[domain_node].append(p_shape)

    # Build NodeShapes in SHACL graph
    for domain_node, properties in shapes_by_domain.items():
        # Create a NodeShape for this domain
        # Name it based on the class name (e.g. DatasetShape)
        local_name = str(domain_node).split("#")[-1].split("/")[-1].split(":")[-1]
        shape_uri = EXT[f"{local_name}Shape"]
        
        sg.add((shape_uri, RDF.type, SH.NodeShape))
        sg.add((shape_uri, SH.targetClass, domain_node))
        
        for p_shape in properties:
            sg.add((shape_uri, SH.property, p_shape))

    # --- Save Outputs ---
    
    # 1. Ontology
    out_ttl = "backend/ontology/constructDCAT.ttl"
    g.serialize(out_ttl, format="turtle")
    print(f"Generated Ontology: {out_ttl}")
    
    # 2. SHACL
    out_shacl = "backend/shacl/constructDCAT_shacl.ttl"
    sg.serialize(out_shacl, format="turtle")
    print(f"Generated SHACL: {out_shacl}")

if __name__ == "__main__":
    run()
