import pandas as pd
import os

# Define the structure for the Excel template
classes_data = [
    {"Class URI": "dcat:Dataset", "Parent Class": "dcat:Resource", "Label": "Dataset", "Description": "A collection of data, published or curated by a single agent."},
    {"Class URI": "ext:HealthDataset", "Parent Class": "dcat:Dataset", "Label": "Health Dataset", "Description": "A dataset containing health-related information."}
]

properties_data = [
    {"Property URI": "dct:title", "Domain": "dcat:Dataset", "Range": "xsd:string", "Min Count": 1, "Max Count": "", "Label": "Title", "Description": "A name given to the dataset."},
    {"Property URI": "ext:patientCount", "Domain": "ext:HealthDataset", "Range": "xsd:integer", "Min Count": 0, "Max Count": 1, "Label": "Patient Count", "Description": "Number of patients in the dataset."}
]

# Create DataFrames
df_classes = pd.DataFrame(classes_data)
df_properties = pd.DataFrame(properties_data)

# Write to Excel
output_file = "backend/ontology_definition.xlsx"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df_classes.to_excel(writer, sheet_name='Classes', index=False)
    df_properties.to_excel(writer, sheet_name='Properties', index=False)

print(f"Created template at {output_file}")
