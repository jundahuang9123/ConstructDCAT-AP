import pandas as pd
from rdflib import Graph, RDF, RDFS, OWL, Namespace
import os

def run():
    print("Loading base ontology from backend/dcat3.ttl...")
    base_ttl = "backend/dcat3.ttl"
    output_file = "backend/ontology_definition.xlsx"
    
    if not os.path.exists(base_ttl):
        print(f"Error: Base file {base_ttl} not found.")
        return

    g = Graph()
    g.parse(base_ttl, format="turtle")
    
    # Namespaces for prefixing
    namespaces = {n: p for p, n in g.namespaces()}
    
    def get_curie(uri):
        uri_str = str(uri)
        for ns, prefix in namespaces.items():
            if uri_str.startswith(str(ns)):
                return f"{prefix}:{uri_str[len(str(ns)):]}"
        return uri_str

    def get_label(node):
        # Try english label first
        for label in g.objects(node, RDFS.label):
            if label.language == 'en':
                return str(label)
        # Fallback to any label
        for label in g.objects(node, RDFS.label):
            return str(label)
        return ""

    def get_comment(node):
        for comment in g.objects(node, RDFS.comment):
            if comment.language == 'en':
                return str(comment)
        for comment in g.objects(node, RDFS.comment):
            return str(comment)
        return ""

    # --- Extract Classes ---
    classes_data = []
    classes_set = set()
    
    for s, p, o in g.triples((None, RDF.type, None)):
        if o in (OWL.Class, RDFS.Class):
            if s in classes_set: continue
            classes_set.add(s)
            
            parent = ""
            for p_class in g.objects(s, RDFS.subClassOf):
                parent = get_curie(p_class)
                break # Just take the first one for the simple excel
            
            classes_data.append({
                "Class URI": get_curie(s),
                "Parent Class": parent,
                "Label": get_label(s),
                "Description": get_comment(s)
            })
            
    # Add dummy Construction examples (commented out or just appended)
    classes_data.append({
        "Class URI": "ext:ConstructionProject", 
        "Parent Class": "dcat:Resource", 
        "Label": "Construction Project", 
        "Description": "A project related to the construction domain (Example)."
    })

    # --- Extract Properties ---
    properties_data = []
    props_set = set()
    
    for s, p, o in g.triples((None, RDF.type, None)):
        if o in (RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty):
            if s in props_set: continue
            props_set.add(s)
            
            domain = ""
            for d in g.objects(s, RDFS.domain):
                domain = get_curie(d)
                break
                
            range_val = ""
            for r in g.objects(s, RDFS.range):
                range_val = get_curie(r)
                break

            properties_data.append({
                "Property URI": get_curie(s),
                "Domain": domain,
                "Range": range_val,
                "Min Count": "", # Not in DCAT3 base usually
                "Max Count": "",
                "Label": get_label(s),
                "Description": get_comment(s)
            })

    # Create DataFrames
    df_classes = pd.DataFrame(classes_data)
    df_properties = pd.DataFrame(properties_data)

    # Sort for better readability
    df_classes = df_classes.sort_values(by="Class URI")
    df_properties = df_properties.sort_values(by="Property URI")

    # Write to Excel
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_classes.to_excel(writer, sheet_name='Classes', index=False)
        df_properties.to_excel(writer, sheet_name='Properties', index=False)

    print(f"Created template at {output_file} with {len(df_classes)} classes and {len(df_properties)} properties.")

if __name__ == "__main__":
    run()
