# pyroriskclient

Tiny Python client for the [Pyronear risk API](https://github.com/MateoLostanlen/pyro-risk-api).

## Install

```bash
pip install "git+https://github.com/MateoLostanlen/pyro-risk-api.git#subdirectory=client"
```

## Usage

```python
from pyroriskclient import Client

api = Client(
    host="https://riskapi.pyronear.org",
    username="admin",
    password="...",
)

api.health()                                    # {"status": "ok"}
api.list_cameras()                              # [{"id": 1, "name": "...", "fwi": 0.0, ...}, ...]
api.get_camera(1)                               # {"id": 1, ...}
api.get_scores(start="2026-05-01")              # all cameras, 2026-05-01 → today (UTC)
api.get_scores(start="2026-05-01", camera_id=1) # one camera, range
```

All methods return parsed JSON. Errors (4xx/5xx) raise
`requests.HTTPError`.
