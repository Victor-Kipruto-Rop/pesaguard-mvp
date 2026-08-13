from __future__ import annotations

from pydantic import BaseModel, Field, constr, conint


class LoggingSettings(BaseModel):
    level: constr(pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$") = Field("INFO", description="Logging level")
    structured: bool = Field(True, description="Enable structured logging output")
    file_path: constr(min_length=1) = Field("/var/log/pesaguard/app.log", description="Application log file path")
    max_file_size_mb: int = Field(50, ge=1, description="Maximum log file size in MB")
    backup_count: int = Field(5, ge=0, description="Number of rotated log files to retain")
