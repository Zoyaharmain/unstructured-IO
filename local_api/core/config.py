"""Environment configuration, shared by HTTP and direct callers."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_upload_bytes: int = 25 * 1024 * 1024

    def __post_init__(self):
        if self.max_upload_bytes <= 0:
            raise ValueError('MAX_UPLOAD_BYTES must be positive')

    @classmethod
    def from_env(cls):
        return cls(max_upload_bytes=int(os.getenv('MAX_UPLOAD_BYTES', str(25 * 1024 * 1024))))
