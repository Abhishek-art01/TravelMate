from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObservabilityConfig:
    service_name: str = "travelmate-api"
    otlp_endpoint: str = "http://localhost:4318"
    environment: str = "development"

    @property
    def otel_headers(self) -> dict[str, str]:
        return {
            "service.name": self.service_name,
            "deployment.environment": self.environment,
        }


def get_observability_config(service_name: str, otlp_endpoint: str, environment: str) -> ObservabilityConfig:
    return ObservabilityConfig(
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        environment=environment,
    )
