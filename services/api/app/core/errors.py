from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiError:
    code: str
    message: str

    def as_response(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}
