#!/usr/bin/env python3
from __future__ import annotations

from gradeplotter_v2.web import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
