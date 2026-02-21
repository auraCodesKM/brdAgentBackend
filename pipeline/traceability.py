import pandas as pd

class TraceabilityMatrixBuilder:
    def __init__(self):
        self.requirements = []

    def log_requirement(self, req_id: str, desc: str, source_doc: str, chunk_id: str, is_conflict: bool = False, conflict_detail: str = ""):
        self.requirements.append({
            "Requirement ID": req_id,
            "Description": desc,
            "Source Document": source_doc,
            "Chunk Citation": chunk_id,
            "Conflict Flag": is_conflict,
            "Conflict Details": conflict_detail
        })

    def export_csv(self, filename: str = "traceability_matrix.csv"):
        """Exports the precise origin of every generated BRD requirement to a CSV dataset."""
        df = pd.DataFrame(self.requirements)
        df.to_csv(filename, index=False)
        return filename

traceability_builder = TraceabilityMatrixBuilder()
