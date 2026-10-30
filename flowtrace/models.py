from dataclasses import asdict, dataclass, field

MECHANISMS = ("http_api", "database", "message_queue", "file",
              "external_service", "other")
CONFIDENCE_LEVELS = ("high", "medium", "low")


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
    data: str
    mechanism: str
    confidence: str
    evidence: list = field(default_factory=list)

    def validate(self):
        """Return a list of problems; an empty list means the flow is valid."""
        problems = []
        if not self.source or not self.destination:
            problems.append("source and destination are required")
        if self.mechanism not in MECHANISMS:
            problems.append(f"unknown mechanism: {self.mechanism}")
        if self.confidence not in CONFIDENCE_LEVELS:
            problems.append(f"unknown confidence: {self.confidence}")
        if not self.evidence:
            problems.append("no evidence: every flow must point to code")
        for e in self.evidence:
            if e.start_line < 1 or e.end_line < e.start_line:
                problems.append(f"invalid line range in {e.file}")
        return problems

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d, repo):
        """Build a DataFlow from the model's JSON output."""
        return cls(
            repo=repo,
            source=d.get("source", ""),
            destination=d.get("destination", ""),
            data=d.get("data", ""),
            mechanism=d.get("mechanism", ""),
            confidence=d.get("confidence", ""),
            evidence=[Evidence(**e) for e in d.get("evidence", [])],
        )