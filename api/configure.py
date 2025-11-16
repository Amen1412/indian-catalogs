from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json
import sys
import os

# Import utils - try different paths for Vercel compatibility
try:
    from api.utils import (
        load_config,
        save_config,
        LANGUAGE_NAMES,
        encode_config_token,
        decode_config_token,
        build_catalog_id,
    )
except ImportError:
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.utils import (
        load_config,
        save_config,
        LANGUAGE_NAMES,
        encode_config_token,
        decode_config_token,
        build_catalog_id,
    )

CONFIGURE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stremio Addon Configuration</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .checkbox-group {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 10px;
        }
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        .checkbox-item label {
            margin: 0;
            font-weight: normal;
            cursor: pointer;
            user-select: none;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        .message {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            display: none;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .help-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        a {
            color: #667eea;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .result-section {
            margin-top: 30px;
            padding: 24px;
            border: 1px solid #e4e9ff;
            border-radius: 12px;
            background: #f7f9ff;
            display: none;
        }
        .result-section h2 {
            font-size: 20px;
            margin-bottom: 12px;
            color: #333;
        }
        .result-section p {
            font-size: 14px;
            color: #555;
            margin-bottom: 16px;
        }
        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 16px;
        }
        .action-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            border: none;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .action-button.primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
        }
        .action-button.secondary {
            background: #fff;
            color: #4a4a4a;
            border: 2px solid #d9defa;
        }
        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 18px rgba(102, 126, 234, 0.35);
        }
        .action-button:active {
            transform: translateY(0);
        }
        .manifest-url {
            background: #222b45;
            color: #fff;
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
            overflow-x: auto;
            word-break: break-all;
        }
        .catalog-list {
            margin-top: 12px;
        }
        .catalog-list a {
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ Addon Configuration</h1>
        <p class="subtitle">Configure your TMDB API key and select language catalogs</p>
        
        <form id="configForm">
            <div class="form-group">
                <label for="tmdbKey">TMDB API Key *</label>
                <input type="text" id="tmdbKey" name="tmdbKey" placeholder="Enter your TMDB API key" required>
                <div class="help-text">
                    Get your API key from <a href="https://www.themoviedb.org/settings/api" target="_blank">TMDB Settings</a>
                </div>
            </div>
            
            <div class="form-group">
                <label>Select Language Catalogs</label>
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="malayalam" name="languages" value="malayalam" checked>
                        <label for="malayalam">Malayalam</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="hindi" name="languages" value="hindi">
                        <label for="hindi">Hindi</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="tamil" name="languages" value="tamil">
                        <label for="tamil">Tamil</label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="kannada" name="languages" value="kannada">
                        <label for="kannada">Kannada</label>
                    </div>
                </div>
            </div>
            
            <button type="submit">Save Configuration</button>
        </form>
        
        <div id="message" class="message"></div>
        
        <div id="resultSection" class="result-section">
            <h2>Install Your Personal Addon</h2>
            <p>Use these links to add the addon to Stremio or copy the manifest URL for later.</p>
            <div class="actions">
                <a id="stremioAppLink" class="action-button primary" href="#" target="_blank">Open in Stremio App</a>
                <a id="stremioWebLink" class="action-button secondary" href="#" target="_blank">Open in Stremio Web</a>
                <button id="copyManifest" type="button" class="action-button secondary">Copy Manifest URL</button>
            </div>
            <div class="manifest-url" id="manifestUrlDisplay"></div>
            <div class="catalog-list" id="catalogList"></div>
        </div>
    </div>
    
    <script>
        const CATALOG_SEPARATOR = '~';
        let currentToken = null;
        const params = new URLSearchParams(window.location.search);
        const initialToken = params.get('token');
        if (initialToken) {
            currentToken = initialToken;
        }

        // Load current config on page load
        const configUrl = currentToken 
            ? `/api/configure?action=get&token=${encodeURIComponent(currentToken)}`
            : '/api/configure?action=get';

        fetch(configUrl)
            .then(res => res.json())
            .then(data => {
                if (data.tmdb_api_key) {
                    document.getElementById('tmdbKey').value = data.tmdb_api_key;
                }
                if (data.enabled_languages) {
                    document.querySelectorAll('input[name="languages"]').forEach(cb => {
                        cb.checked = false;
                    });
                    data.enabled_languages.forEach(lang => {
                        const checkbox = document.getElementById(lang);
                        if (checkbox) checkbox.checked = true;
                    });
                }
                if (data.token) {
                    currentToken = data.token;
                    const manifestUrl = buildManifestUrl(currentToken);
                    renderResults({
                        manifest_url: manifestUrl,
                        stremio_app_link: buildStremioAppLink(manifestUrl),
                        stremio_web_link: buildStremioWebLink(manifestUrl),
                        catalog_urls: buildCatalogLinks(data.enabled_languages || [], currentToken),
                        enabled_languages: data.enabled_languages || []
                    });
                } else if (currentToken) {
                    const manifestUrl = buildManifestUrl(currentToken);
                    renderResults({
                        manifest_url: manifestUrl,
                        stremio_app_link: buildStremioAppLink(manifestUrl),
                        stremio_web_link: buildStremioWebLink(manifestUrl),
                        catalog_urls: buildCatalogLinks([], currentToken),
                        enabled_languages: []
                    });
                }
            })
            .catch(err => console.error('Error loading config:', err));
 
        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const tmdbKey = document.getElementById('tmdbKey').value.trim();
            const checkboxes = document.querySelectorAll('input[name="languages"]:checked');
            const languages = Array.from(checkboxes).map(cb => cb.value);
            
            if (!tmdbKey) {
                showMessage('Please enter a TMDB API key', 'error');
                return;
            }
            
            if (languages.length === 0) {
                showMessage('Please select at least one language', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/configure', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        tmdb_api_key: tmdbKey,
                        enabled_languages: languages,
                        token: currentToken
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    showMessage('Configuration saved! Your personal manifest link is ready below.', 'success');
                    if (result.token) {
                        currentToken = result.token;
                        const newUrl = `${window.location.pathname}?token=${encodeURIComponent(currentToken)}`;
                        window.history.replaceState(null, '', newUrl);
                    }
                    if (!result.enabled_languages && result.catalog_urls) {
                        result.enabled_languages = Object.keys(result.catalog_urls);
                    }
                    renderResults(result);
                } else {
                    showMessage(result.message || 'Error saving configuration', 'error');
                }
            } catch (error) {
                showMessage('Error saving configuration: ' + error.message, 'error');
            }
        });
 
        document.getElementById('copyManifest').addEventListener('click', async () => {
            const manifestUrl = document.getElementById('manifestUrlDisplay').textContent.trim();
            if (!manifestUrl) return;
            try {
                await navigator.clipboard.writeText(manifestUrl);
                showMessage('Manifest URL copied to clipboard!', 'success');
            } catch (error) {
                showMessage('Could not copy manifest URL: ' + error.message, 'error');
            }
        });

        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = text;
            messageDiv.className = 'message ' + type;
            messageDiv.style.display = 'block';
            
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }

        function renderResults(data) {
            if (!data || !data.manifest_url) {
                document.getElementById('resultSection').style.display = 'none';
                return;
            }

            document.getElementById('resultSection').style.display = 'block';
            document.getElementById('manifestUrlDisplay').textContent = data.manifest_url;

            const appLink = data.stremio_app_link || buildStremioAppLink(data.manifest_url);
            const webLink = data.stremio_web_link || buildStremioWebLink(data.manifest_url);
            document.getElementById('stremioAppLink').href = appLink;
            document.getElementById('stremioWebLink').href = webLink;

            const catalogList = document.getElementById('catalogList');
            catalogList.innerHTML = '';
            const catalogs = (data.catalog_urls && Object.keys(data.catalog_urls).length > 0)
                ? data.catalog_urls
                : buildCatalogLinks(data.enabled_languages || [], currentToken);
            const order = (data.enabled_languages && data.enabled_languages.length > 0)
                ? data.enabled_languages
                : Object.keys(catalogs);
            order.forEach(lang => {
                const url = catalogs[lang];
                if (!url) return;
                const item = document.createElement('div');
                item.innerHTML = `<strong>${lang.toUpperCase()}</strong>: <a href="${url}" target="_blank">${url}</a>`;
                catalogList.appendChild(item);
            });
        }

        function buildManifestUrl(token) {
            if (!token) return '';
            const origin = window.location.origin.replace(/\/$/, '');
            return `${origin}/manifest.json?token=${encodeURIComponent(token)}`;
        }

        function buildCatalogLinks(languages, token) {
            if (!token) return {};
            const origin = window.location.origin.replace(/\/$/, '');
            const links = {};
            languages.forEach(lang => {
                links[lang] = `${origin}/catalog/movie/${lang}${CATALOG_SEPARATOR}${token}.json`;
            });
            return links;
        }

        function buildStremioAppLink(manifestUrl) {
            return manifestUrl ? `stremio://add-addon?uri=${encodeURIComponent(manifestUrl)}` : '#';
        }

        function buildStremioWebLink(manifestUrl) {
            return manifestUrl ? `https://web.strem.io/#/addons/add?addon=${encodeURIComponent(manifestUrl)}` : '#';
        }
    </script>
</body>
</html>"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        action = query_params.get('action', [None])[0]
        token = query_params.get('token', [None])[0]
        
        if action == 'get':
            # Return current config as JSON
            config = load_config(token)
            config_response = {
                "tmdb_api_key": config.get("tmdb_api_key", ""),
                "enabled_languages": config.get("enabled_languages", ["malayalam"]),
            }
            if token:
                config_response["token"] = token
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(config_response).encode())
            return
        
        # Return HTML configuration page
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(CONFIGURE_HTML.encode())
        return
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            tmdb_key = data.get('tmdb_api_key', '').strip()
            enabled_languages = data.get('enabled_languages', [])
            existing_token = data.get('token')
            
            if not tmdb_key:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "TMDB API key is required"
                }).encode())
                return
            
            if not enabled_languages:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "At least one language must be selected"
                }).encode())
                return
            
            # Validate languages
            valid_languages = list(LANGUAGE_NAMES.keys())
            enabled_languages = [lang for lang in enabled_languages if lang in valid_languages]
            
            if not enabled_languages:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": "Invalid language selection"
                }).encode())
                return
            
            # Save configuration
            config = {
                "tmdb_api_key": tmdb_key,
                "enabled_languages": enabled_languages
            }
            save_config(config)

            token = encode_config_token(config)
            # Prefer existing token if provided and decodes to same config
            if existing_token:
                decoded = decode_config_token(existing_token)
                if decoded.get("tmdb_api_key") == tmdb_key and set(decoded.get("enabled_languages", [])) == set(enabled_languages):
                    token = existing_token

            # Note: Cache will be populated when catalog is first accessed or when /refresh is called

            protocol = self.headers.get('x-forwarded-proto', 'https')
            host = self.headers.get('host', '')
            base_url = f"{protocol}://{host}" if host else ''
            token_query = f"?token={quote(token)}" if token else ""
            manifest_path = f"/manifest.json{token_query}"
            manifest_url = f"{base_url}{manifest_path}" if base_url else manifest_path

            stremio_app_link = f"stremio://add-addon?uri={quote(manifest_url)}"
            stremio_web_link = f"https://web.strem.io/#/addons/add?addon={quote(manifest_url)}"

            catalog_urls = {
                lang: f"{base_url}/catalog/movie/{build_catalog_id(lang, token)}.json" if base_url else f"/catalog/movie/{build_catalog_id(lang, token)}.json"
                for lang in enabled_languages
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Configuration saved successfully. To populate the catalog, visit /refresh?token=YOUR_TOKEN or wait for the catalog to auto-populate on first access.",
                "token": token,
                "manifest_url": manifest_url,
                "stremio_app_link": stremio_app_link,
                "stremio_web_link": stremio_web_link,
                "catalog_urls": catalog_urls,
                "enabled_languages": enabled_languages
            }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": str(e)
            }).encode())
        return

