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
        try:
            # Log the path for debugging
            print(f"[MANIFEST] Received request: {self.path}")
            print(f"[MANIFEST] Headers: {dict(self.headers)}")
            
            # Parse the path and query string
            # self.path includes query string in Vercel Python handlers
            parsed_url = urlparse(self.path)
            print(f"[MANIFEST] Parsed path: {parsed_url.path}, query: {parsed_url.query}")
            
            query_params = parse_qs(parsed_url.query)
            token = query_params.get("token", [None])[0]
            
            if token:
                print(f"[MANIFEST] Token found in query: {token[:20]}...")

            # Also check for token in path (for /manifest/<token>.json format)
            if not token and parsed_url.path.startswith("/manifest/"):
                maybe_token = os.path.splitext(os.path.basename(parsed_url.path))[0]
                if maybe_token and maybe_token != "manifest":
                    token = maybe_token
                    print(f"[MANIFEST] Token found in path: {token[:20]}...")

            # When no token is provided (direct /manifest.json), fall back to default config.
            try:
                config = load_config(token)
                enabled_languages = config.get("enabled_languages", ["malayalam"])
            except Exception as e:
                print(f"[WARNING] Error loading config: {e}")
                enabled_languages = ["malayalam"]
            
            # Ensure we have at least one language
            if not enabled_languages or not isinstance(enabled_languages, list):
                enabled_languages = ["malayalam"]

            catalogs = []
            for lang in enabled_languages:
                if lang in LANGUAGE_NAMES:
                    catalogs.append({
                        "type": "movie",
                        "id": build_catalog_id(lang, token),
                        "name": LANGUAGE_NAMES[lang]
                    })
            
            # Ensure we have at least one catalog
            if not catalogs:
                catalogs = [{
                    "type": "movie",
                    "id": build_catalog_id("malayalam", token),
                    "name": "Malayalam"
                }]

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

            manifest_json = json.dumps(manifest, indent=None, separators=(',', ':'))
            print(f"[MANIFEST] Sending manifest with {len(catalogs)} catalogs")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()
            self.wfile.write(manifest_json.encode('utf-8'))
            self.wfile.flush()
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] Manifest error: {error_trace}")
            # Return a minimal valid manifest even on error
            error_manifest = {
                "id": "org.indian.catalog",
                "version": "2.0.0",
                "name": "Indian Movies OTT",
                "description": "Latest Indian Movies on OTT Platforms",
                "resources": ["catalog"],
                "types": ["movie"],
                "catalogs": [{
                    "type": "movie",
                    "id": "malayalam",
                    "name": "Malayalam"
                }],
                "idPrefixes": ["tt"]
            }
            try:
                error_json = json.dumps(error_manifest, indent=None, separators=(',', ':'))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', '*')
                self.end_headers()
                self.wfile.write(error_json.encode('utf-8'))
                self.wfile.flush()
            except Exception as send_error:
                print(f"[ERROR] Failed to send error response: {send_error}")
        return
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        return

