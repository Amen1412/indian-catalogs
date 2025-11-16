from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import sys
import os

# Import utils - try different paths for Vercel compatibility
try:
    from api.utils import (
        load_cache,
        to_stremio_meta,
        get_enabled_languages,
        parse_catalog_id,
    )
except ImportError:
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.utils import (
        load_cache,
        to_stremio_meta,
        get_enabled_languages,
        parse_catalog_id,
    )

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Extract catalog id (contains language + token)
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        catalog_id = query_params.get('id', [None])[0] or query_params.get('lang', [None])[0]

        if not catalog_id:
            path_parts = self.path.split('/')
            if 'movie' in path_parts:
                idx = path_parts.index('movie')
                if idx + 1 < len(path_parts):
                    catalog_id = path_parts[idx + 1].replace('.json', '')

        if not catalog_id:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"metas": [], "error": "missing_catalog_id"}).encode())
            return

        lang, token = parse_catalog_id(catalog_id)

        enabled_languages = get_enabled_languages(token)
        if lang not in enabled_languages:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"metas": []}).encode())
            return

        print(f"[INFO] Catalog requested for {lang} (token: {token[:20] if token else 'none'}...)")

        try:
            from api.utils import get_tmdb_key, fetch_movies_for_language, save_cache
            
            # Try to load from cache
            cached_movies = load_cache(lang, token)
            print(f"[INFO] Loaded {len(cached_movies)} movies from cache for {lang}")
            
            # If cache is empty, try to fetch (but limit pages to avoid timeout)
            if not cached_movies:
                print(f"[INFO] Cache empty for {lang}, fetching movies...")
                tmdb_key = get_tmdb_key(token)
                if not tmdb_key:
                    print(f"[ERROR] No TMDB API key found for {lang}")
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"metas": [], "error": "no_api_key"}).encode())
                    return
                
                try:
                    # Fetch movies (this might timeout on first request, that's ok)
                    # User should trigger /refresh endpoint to populate cache
                    print(f"[INFO] Starting fetch for {lang}...")
                    cached_movies = fetch_movies_for_language(lang, tmdb_key)
                    if cached_movies:
                        save_cache(lang, cached_movies, token)
                        print(f"[INFO] Saved {len(cached_movies)} movies to cache for {lang}")
                    else:
                        print(f"[WARNING] Fetch returned no movies for {lang}")
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Failed to fetch movies for {lang}: {traceback.format_exc()}")
                    # Return empty instead of failing - user can refresh manually
            
            # Convert to Stremio format
            metas = []
            for movie in cached_movies:
                meta = to_stremio_meta(movie)
                if meta:
                    metas.append(meta)
            
            print(f"[INFO] Returning {len(metas)} total movies for {lang} ✅")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"metas": metas}).encode())
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"[ERROR] Catalog error: {error_msg}")
            # Always return valid JSON, even on error
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"metas": []}).encode())
        return

