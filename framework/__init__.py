"""Experimental evidence consistency kernel; callers enforce evaluator authority."""
from .kernel import identity, verify, contract_digest

__all__ = ['identity', 'verify', 'contract_digest']
