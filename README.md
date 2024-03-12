# Proxy - goodies

Scripts and tools for proxy quick-fixes and testing.

## [Mitmproxy](https://docs.mitmproxy.org/stable/)

Versatile proxy, allows Python-scripting and pip-install.

### Install
  
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install mitmproxy
```

### Reverse proxy ing

Mitmdump will skip the interactive console and just dump the requests and responses to the console.

```bash
mitmdump -s <script.py> -m  reverse:<host>@<listen_host> 
```

`<host>` should be a url consisting of protocol, domain-name and port, e.g. `http://localhost:11434`

`<listen_host>` can consist of the same 3 parts but is fully optional and defaults to `http://0.0.0.0:8080`

Other usefull flags are:
- ssl insecure: `-k`
- proxy-auth: `--proxyauth`
- certs: `--certs`

### Python scripting

Mitmproxy allows for Python scripting, which can be used to modify everything in TCP sessions and HTTP flows.

Can be added to the proxy with the `-s` flag.
Features hot-reload for the passed file (not the imports).

Add your hacq with an Addon class.

For editing the HTTP flow, e.g. enable/disable streaming override the `requestheaders()`/`responseheaders()` function.

For messing with the Request/Response override `request()`/`response()`

> Much fun `(:`