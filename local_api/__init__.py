"""Local HTTP interface to the installed Unstructured package."""
import os

# Keep upstream optional telemetry off by default for local document processing.
os.environ.setdefault('DO_NOT_TRACK', 'true')
