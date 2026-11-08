"""Redacted evaluator failure categories shared by the CLI and runner."""

class EvaluationError(RuntimeError):
    """Fixed diagnostics only: never expose candidate stderr or host configuration."""
    def __init__(self, code, stage, message, completed_checks=()):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.completed_checks = list(completed_checks)

