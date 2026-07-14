"""Boot Streamlit after binding the Prometheus metrics port (same process)."""
from __future__ import annotations

import sys

from src.observability.metrics import start_metrics_server


def main() -> None:
    port = start_metrics_server()
    print(f"Prometheus metrics listening on :{port}/metrics", flush=True)
    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        "application.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
