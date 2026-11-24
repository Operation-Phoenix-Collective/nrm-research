"""Turn one SAS row into graph-ready values using the field ontology.

The SAS extractor does not know about studies or shared fields. This module
joins a row to field_dataset_mapping.csv and rewrites the values that can be
compared across studies: event flags become 1 or 0, day clocks become months,
and coded fields keep the dictionary label next to the raw code.
"""
import csv
import math
import re
from datetime import date, datetime
from pathlib import Path

PATIENT_IDS = ("pseudoid", "dummyid", "pseudocrid", "dummycrid", "dcrid")
CENTER_IDS = ("dummyccn", "pseudoccn", "pseudocenterid", "dccn")
EVENT_ROLES = frozenset({"event", "competing_risk"})
MONTHS_PER_DAY = 1 / 30.4375
MISSING_LABEL = re.compile(
    r"missing|unknown|not reported|not answered|\bn/?a\b", re.I
)
EVENT_LABEL = re.compile(r"^(yes|event|dead|death|relapse)$", re.I)
CENSOR_LABEL = re.compile(r"^censor|^no$|^alive$", re.I)


class Binding:
    __slots__ = ("field_id", "concept", "role", "stack", "time_unit", "labels")

    def __init__(self, field_id, concept, role, stack, time_unit, labels):
        self.field_id = field_id
        self.concept = concept
        self.role = role
        self.stack = stack
        self.time_unit = time_unit
        self.labels = labels


def load_ontology(mapping_path, ontology_path, catalog_path):
    stacks = {}
    with open(ontology_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            stacks[row["field_id"]] = row.get("stack") or ""
    titles = {}
    with open(catalog_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            titles[row["study_id"]] = {
                "title": row.get("title") or "",
                "first_author": row.get("first_author") or "",
                "start_year": row.get("start_year") or "",
            }
    by_study = {}
    with open(mapping_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            field_id = row["field_id"]
            binding = Binding(
                field_id,
                row["concept"],
                row["role"],
                stacks.get(field_id, ""),
                (row.get("time_unit") or "").lower(),
                _parse_labels(row.get("codes") or ""),
            )
            by_study.setdefault(row["study_id"], {})[row["source_variable"].lower()] = binding
    return {"by_study": by_study, "titles": titles}


def normalize_record(record, ontology):
    study_id = record.get("__study_id") or ""
    bindings = ontology["by_study"].get(study_id, {})
    columns = {
        str(name).lower(): value
        for name, value in record.items()
        if not str(name).startswith("__")
    }
    patient_id = _pick(columns, bindings, "patient_id", PATIENT_IDS)
    id_source = "patient_id"
    if patient_id is None:
        patient_id = f"{record.get('__source_file')}:{record.get('__row_index')}"
        id_source = "row"
    values = []
    seen = set()
    for name, value in columns.items():
        binding = bindings.get(name)
        if binding is None or not _present(value):
            continue
        coded = _coded_value(value, binding)
        if coded is None:
            continue
        # Two columns can share a field. Keep both; the relationship key is the source name.
        key = (binding.field_id, name)
        if key in seen:
            continue
        seen.add(key)
        item = {"field_id": binding.field_id, "source_variable": name}
        item.update({key: val for key, val in coded.items() if val not in (None, "")})
        values.append(item)
    study = ontology["titles"].get(study_id, {})
    out = {
        "study_id": study_id,
        "study_title": study.get("title", ""),
        "first_author": study.get("first_author", ""),
        "start_year": study.get("start_year", ""),
        "patient_id": patient_id,
        "id_source": id_source,
        "source_file": record.get("__source_file") or "",
        "values": values,
    }
    center_id = _pick(columns, bindings, "center_id", CENTER_IDS)
    if center_id is not None:
        out["center_id"] = center_id
    return out


def _pick(columns, bindings, concept, priority):
    rank = {name: index for index, name in enumerate(priority)}
    found = []
    for name, binding in bindings.items():
        if binding.concept != concept or name not in columns or not _present(columns[name]):
            continue
        found.append((rank.get(name, len(priority)), name, columns[name]))
    if not found:
        return None
    found.sort()
    return _as_id(found[0][2])


def _coded_value(value, binding):
    number = _number(value)
    label = binding.labels.get(_code_key(value)) if number is not None else None
    if label and MISSING_LABEL.search(label):
        return None
    if binding.role in EVENT_ROLES and label:
        bit = _event_bit(label)
        if bit is None:
            return _raw(number, label, binding)
        return {"value_num": bit, "value_text": label, "unit": ""}
    if binding.role == "time" and number is not None:
        unit = binding.time_unit
        if unit == "days":
            return {"value_num": number * MONTHS_PER_DAY, "value_text": "", "unit": "months"}
        if unit == "years":
            return {"value_num": number * 12, "value_text": "", "unit": "months"}
        return {"value_num": number, "value_text": "", "unit": unit}
    if binding.role in {"measure", "bin"} and number is not None:
        return {"value_num": number, "value_text": label or "", "unit": ""}
    if isinstance(value, (datetime, date)):
        return {"value_num": None, "value_text": value.isoformat(), "unit": ""}
    text = label or ("" if number is not None else str(value).strip())
    return {"value_num": number, "value_text": text, "unit": ""}


def _raw(number, label, binding):
    return {
        "value_num": number,
        "value_text": label or "",
        "unit": binding.time_unit,
    }


def _event_bit(label):
    text = label.strip()
    if EVENT_LABEL.match(text):
        return 1
    if CENSOR_LABEL.match(text):
        return 0
    return None


def _parse_labels(codes):
    labels = {}
    for part in codes.split("; "):
        if "=" not in part:
            continue
        raw, label = part.split("=", 1)
        labels[_code_key(raw)] = label.strip()
    return labels


def _code_key(value):
    number = _number(value) if not isinstance(value, str) else _number_string(value)
    if number is None:
        return str(value).strip()
    if number.is_integer():
        return str(int(number))
    return str(number)


def _number_string(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _number(value):
    if isinstance(value, bool) or isinstance(value, (datetime, date)):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    return None


def _as_id(value):
    number = _number(value)
    if number is not None and number.is_integer():
        return str(int(number))
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _present(value):
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def paths_from_here():
    """Default locations of the derived dictionary files, next to this repo's data/."""
    root = Path(__file__).resolve().parents[2]
    data = root / "data"
    return data / "field_dataset_mapping.csv", data / "field_ontology.csv", data / "catalog.csv"
