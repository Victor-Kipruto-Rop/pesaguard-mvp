from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any, Dict, List


class DataExporter:
    """Exports records to JSON or CSV for integration workflows."""

    @staticmethod
    def export_json(records: List[Dict[str, Any]]) -> str:
        return json.dumps(records)

    @staticmethod
    def export_csv(records: List[Dict[str, Any]]) -> str:
        if not records:
            return ""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
        return output.getvalue()


class DataImporter:
    """Imports JSON or CSV payloads into records."""

    @staticmethod
    def import_json(payload: str) -> List[Dict[str, Any]]:
        return json.loads(payload)

    @staticmethod
    def import_csv(payload: str) -> List[Dict[str, Any]]:
        reader = csv.DictReader(StringIO(payload))
        return list(reader)
