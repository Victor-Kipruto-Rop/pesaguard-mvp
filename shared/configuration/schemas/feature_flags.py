from __future__ import annotations

from pydantic import BaseModel, Field, constr


class FeatureFlagsSettings(BaseModel):
    enable_experimental_payments: bool = Field(False, description="Enable experimental payments flow")
    enable_service_mesh: bool = Field(True, description="Enable service mesh integration")
    enable_rate_limiting: bool = Field(True, description="Enable request rate limiting")
    enable_caching: bool = Field(True, description="Enable caching support")
    flag_overrides: dict[constr(min_length=1), bool] = Field(default_factory=dict, description="Manual feature flag overrides")
