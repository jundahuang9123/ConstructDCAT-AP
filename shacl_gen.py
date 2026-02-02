#!/usr/bin/env python3
"""
Generate a *baseline* SHACL shapes file from a YARRRML mapping.

What it does (best-effort):
- Finds subjects (s) and emitted rdf:type triples (a, Class) -> creates sh:targetClass shapes
- Collects predicates emitted in "po" blocks
- Infers:
  - sh:nodeKind sh:IRI when object has type: iri (or value looks like a prefixed name/IRI template)
  - sh:datatype when object has datatype: xsd:...
  - sh:minCount 1 for predicates that appear in the mapping (baseline assumption)

What it does NOT do (by design / cannot infer reliably from YARRRML):
- conditional constraints (if/then), closed shapes, cardinalities beyond minCount=1,
  controlled vocabularies, uniqueness, or semantic constraints not present in the mapping.

Usage:
  python yarrrml_to_shacl.py dcat-v3.yarrrml.yml shapes.ttl

Dependencies:
  pip install pyyaml
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import yaml


@dataclass
class PropertyConstraint:
    path: str
    min_count: int = 1
    node_kind_iri: bool = False
    datatype: Optional[str] = None


@dataclass
class Shape:
    # We generate one NodeShape per target class
    target_class: str
    props: Dict[str, PropertyConstraint] = field(default_factory=dict)


IRI_TEMPLATE_RE = re.compile(r"\$\([^)]+\)")  # $(var)
PREFIXED_NAME_RE = re.compile(r"^[a-zA-Z_][\w.-]*:[\w./#-]+$")  # e.g., dcat:Dataset, ex:thing/$(id)
HTTP_IRI_RE = re.compile(r"^https?://")


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_prefixes(doc: dict) -> Dict[str, str]:
    prefixes = doc.get("prefixes", {}) or {}
    # Normalize: ensure trailing # or / isn't enforced; we just keep user-provided values
    return {k.rstrip(":"): v for k, v in prefixes.items()}


def qname_or_iri(term: str) -> str:
    # Keep whatever the mapping uses (qname or full IRI)
    return term.strip()


def is_declared_iri_object(o: dict) -> bool:
    """
    YARRRML object forms we handle:
      o:
        value: "ex:dataset/$(dataset_id)"
        type: iri
    """
    if not isinstance(o, dict):
        return False
    t = o.get("type")
    if isinstance(t, str) and t.lower() == "iri":
        return True
    # Heuristic: if value is a full IRI or prefixed name (possibly with template), treat as IRI
    val = o.get("value")
    if isinstance(val, str):
        if HTTP_IRI_RE.match(val) or PREFIXED_NAME_RE.match(val):
            return True
    return False


def extract_datatype(o: dict) -> Optional[str]:
    """
    YARRRML object datatype form:
      o:
        value: "$(issued)"
        datatype: xsd:date
    """
    if not isinstance(o, dict):
        return None
    dt = o.get("datatype")
    if isinstance(dt, str) and dt.strip():
        return dt.strip()
    return None


def extract_mapping_po_entries(mapping: dict) -> List[Tuple[str, object]]:
    """
    Returns list of (predicate, objectSpec) for a mapping.

    Handles:
      po:
        - [a, dcat:Dataset]
        - [dct:title, "$(title)"]
        - p: dcat:distribution
          o:
            value: "ex:dist/$(dist_id)"
            type: iri
    """
    out: List[Tuple[str, object]] = []
    po = mapping.get("po", []) or []
    if not isinstance(po, list):
        return out

    for entry in po:
        if isinstance(entry, list) and len(entry) == 2:
            pred, obj = entry
            out.append((str(pred), obj))
        elif isinstance(entry, dict) and "p" in entry and "o" in entry:
            out.append((str(entry["p"]), entry["o"]))
        # else ignore unknown forms (e.g., complex YARRRML)
    return out


def infer_shapes(doc: dict) -> Dict[str, Shape]:
    mappings = doc.get("mappings", {}) or {}
    if not isinstance(mappings, dict):
        raise ValueError("No 'mappings' dict found in YARRRML file.")

    # Map "subject template" -> discovered rdf:types (classes)
    subject_to_classes: Dict[str, Set[str]] = {}

    # Map (subject template, class) -> set of predicates and their inferred constraints
    constraints: Dict[Tuple[str, str], Dict[str, PropertyConstraint]] = {}

    # First pass: collect classes per mapping subject from [a, Class]
    for mname, m in mappings.items():
        if not isinstance(m, dict):
            continue
        subj = m.get("s")
        if not isinstance(subj, str) or not subj.strip():
            continue
        subj = subj.strip()

        po_entries = extract_mapping_po_entries(m)
        for pred, obj in po_entries:
            if pred == "a" and isinstance(obj, str):
                cls = obj.strip()
                subject_to_classes.setdefault(subj, set()).add(cls)

    # Second pass: collect property constraints per (subject, class)
    for mname, m in mappings.items():
        if not isinstance(m, dict):
            continue
        subj = m.get("s")
        if not isinstance(subj, str) or not subj.strip():
            continue
        subj = subj.strip()

        classes = subject_to_classes.get(subj, set())
        if not classes:
            # If no rdf:type found, we can't target a class shape reliably; skip
            continue

        po_entries = extract_mapping_po_entries(m)
        for cls in classes:
            key = (subj, cls)
            constraints.setdefault(key, {})
            for pred, obj in po_entries:
                pred = pred.strip()
                if pred == "a":
                    continue

                pc = constraints[key].get(pred)
                if pc is None:
                    pc = PropertyConstraint(path=qname_or_iri(pred))
                    constraints[key][pred] = pc

                # Infer nodeKind IRI / datatype if possible
                if isinstance(obj, dict):
                    if is_declared_iri_object(obj):
                        pc.node_kind_iri = True
                    dt = extract_datatype(obj)
                    if dt:
                        pc.datatype = dt
                else:
                    # Heuristic: object string that looks like a prefixed name or IRI template
                    if isinstance(obj, str):
                        s = obj.strip()
                        if HTTP_IRI_RE.match(s) or PREFIXED_NAME_RE.match(s):
                            pc.node_kind_iri = True
                # min_count baseline stays 1; if you want "optional", you must override manually

    # Build one Shape per target class; merge properties across subjects that produce same class
    shapes: Dict[str, Shape] = {}
    for (subj, cls), props in constraints.items():
        shape = shapes.get(cls)
        if shape is None:
            shape = Shape(target_class=cls)
            shapes[cls] = shape

        for pred, pc in props.items():
            existing = shape.props.get(pred)
            if existing is None:
                shape.props[pred] = pc
            else:
                # Merge: if any mapping says IRI, keep it; if any says datatype, keep datatype
                existing.node_kind_iri = existing.node_kind_iri or pc.node_kind_iri
                existing.min_count = min(existing.min_count, pc.min_count)  # both are 1 anyway
                if existing.datatype is None and pc.datatype is not None:
                    existing.datatype = pc.datatype

    return shapes


def turtle_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def emit_shacl_ttl(shapes: Dict[str, Shape]) -> str:
    # Minimal prefixes for SHACL output
    header = """@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

"""
    # We will not expand qnames; we keep the qnames as-is (your TTL must include needed prefixes when validating).
    # If you prefer fully expanded IRIs, do it in a post-step or extend this script.
    parts: List[str] = [header]

    # Stable ordering
    for i, (cls, shape) in enumerate(sorted(shapes.items(), key=lambda x: x[0])):
        shape_id = f":Shape_{i+1}"
        parts.append(f"{shape_id} a sh:NodeShape ;\n")
        parts.append(f"  sh:targetClass {shape.target_class} ;\n")

        # Properties
        for pred, pc in sorted(shape.props.items(), key=lambda x: x[0]):
            parts.append("  sh:property [\n")
            parts.append(f"    sh:path {pc.path} ;\n")
            parts.append(f"    sh:minCount {pc.min_count} ;\n")
            if pc.node_kind_iri:
                parts.append("    sh:nodeKind sh:IRI ;\n")
            if pc.datatype:
                parts.append(f"    sh:datatype {pc.datatype} ;\n")
            parts.append("  ] ;\n")

        # End shape
        parts.append("  .\n\n")

    # Add a reminder comment
    parts.append(
        "# NOTE: This is a baseline SHACL derived from mapping structure.\n"
        "# You likely want to refine it with profile rules (controlled vocabularies, optional fields, if/then).\n"
    )
    return "".join(parts)


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print("Usage: python yarrrml_to_shacl.py <mapping.yarrrml.yml> <out.shapes.ttl>", file=sys.stderr)
        return 2

    in_path, out_path = argv[1], argv[2]
    doc = load_yaml(in_path)
    shapes = infer_shapes(doc)
    ttl = emit_shacl_ttl(shapes)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ttl)

    print(f"Wrote {len(shapes)} NodeShapes to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
