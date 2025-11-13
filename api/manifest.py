from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import sys
import os

# Import utils - try different paths for Vercel compatibility
try:
    from api.utils import (
        get_enabled_languages,
        LANGUAGE_NAMES,
        build_catalog_id,
        load_config,
    )
except ImportError:
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.utils import (
        get_enabled_languages,
        LANGUAGE_NAMES,
        build_catalog_id,
        load_config,
    )

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        token = query_params.get("token", [None])[0]

        if not token and parsed_url.path.startswith("/manifest/"):
            maybe_token = os.path.splitext(os.path.basename(parsed_url.path))[0]
            if maybe_token:
                token = maybe_token

        # When no token is provided (direct /manifest.json), fall back to default config.
        config = load_config(token)
        enabled_languages = config.get("enabled_languages", ["malayalam"])

        catalogs = []
        for lang in enabled_languages:
            if lang in LANGUAGE_NAMES:
                catalogs.append({
                    "type": "movie",
                    "id": build_catalog_id(lang, token),
                    "name": LANGUAGE_NAMES[lang]
                })

        if token:
            manifest_id = f"org.indian.catalog.{token[:8]}"
        else:
            manifest_id = "org.indian.catalog"

        manifest = {
            "id": manifest_id,
            "version": "2.0.0",
            "name": "Indian Movies OTT",
            "description": "Latest Indian Movies on OTT Platforms",
            "resources": ["catalog"],
            "types": ["movie"],
            "catalogs": catalogs,
            "idPrefixes": ["tt"]
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(manifest).encode())
        return

