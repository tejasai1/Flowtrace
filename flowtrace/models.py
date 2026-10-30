from dataclasses import asdict, dataclass, field

MECHANISMS = ("http_api", "database", "message_queue", "file",
              "external_service", "other")
CONFIDENCE_LEVELS = ("high", "medium", "low")
DATA_CATEGORIES = ("personal", "payment", "credentials", "business", "operational")
SENSITIVE_CATEGORIES = {"personal", "payment", "credentials"}


@dataclass
class Evidence:
    """The exact place in the code that proves a data flow exists."""
    file: str
    start_line: int
    end_line: int
    snippet: str


@dataclass
class DataFlow:
    """One movement of data from a source system to a destination system."""
    repo: str
    source: str
    destination: str
    data: str                                    # short summary of what moves
    mechanism: str
    confidence: str
    category: str = ""                           # one of DATA_CATEGORIES
    fields: list = field(default_factory=list)   # main data items sent
    evidence: list = field(default_factory=list)

    @property
    def sensitive(self):
        """Decided by FlowTrace from the category, not by the model."""
        return self.category in SENSITIVE_CATEGORIES

    def validate(self):
        """Return a list of problems; an empty list means the flow is valid."""
        problems = []
        if not self.source or not self.destination:
            problems.append("source and destination are required")
        if self.mechanism not in MECHANISMS:
            problems.append(f"unknown mechanism: {self.mechanism}")
        if self.confidence not in CONFIDENCE_LEVELS:
            problems.append(f"unknown confidence: {self.confidence}")
        if self.category not in DATA_CATEGORIES:
            problems.append(f"unknown data category: {self.category}")
        if not self.evidence:
            problems.append("no evidence: every flow must point to code")
        for e in self.evidence:
            if e.start_line < 1 or e.end_line < e.start_line:
                problems.append(f"invalid line range in {e.file}")
        return problems

    def to_dict(self):
        d = asdict(self)
        d["sensitive"] = self.sensitive
        return d

    @classmethod
    def from_dict(cls, d, repo):
        """Build a DataFlow from the model's JSON output."""
        fields = d.get("fields", [])
        if isinstance(fields, str):  # tolerate a single string instead of a list
            fields = [fields]
        return cls(
            repo=repo,
            source=d.get("source", ""),
            destination=d.get("destination", ""),
            data=d.get("data", ""),
            mechanism=d.get("mechanism", ""),
            confidence=d.get("confidence", ""),
            category=d.get("category", ""),
            fields=[str(f) for f in fields],
            evidence=[Evidence(**e) for e in d.get("evidence", [])],
        )