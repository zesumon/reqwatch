# reqwatch

A lightweight HTTP request monitor that logs and diffs API responses over time to detect unannounced breaking changes.

---

## Installation

```bash
pip install reqwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/reqwatch.git && cd reqwatch && pip install .
```

---

## Usage

Define the endpoints you want to monitor in a `reqwatch.yaml` file:

```yaml
endpoints:
  - name: user-api
    url: https://api.example.com/users
    interval: 60  # seconds
  - name: product-feed
    url: https://api.example.com/products
    interval: 300
```

Then start watching:

```bash
reqwatch start
```

reqwatch will poll each endpoint at the defined interval, store snapshots of the responses, and print a diff whenever a change is detected:

```
[2024-03-15 10:42:01] CHANGE DETECTED: user-api
- {"status": "active", "version": "1.0"}
+ {"status": "active", "version": "1.1", "deprecated": true}
```

View the full response history for an endpoint:

```bash
reqwatch history user-api
```

Export a diff report between two timestamps:

```bash
reqwatch diff user-api --from "2024-03-14" --to "2024-03-15"
```

---

## Features

- Automatic response diffing with human-readable output
- Configurable polling intervals per endpoint
- Local snapshot storage for historical comparison
- Supports headers and authentication tokens
- Lightweight — no external database required

---

## License

MIT © 2024 youruser