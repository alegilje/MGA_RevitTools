# encoding: utf-8
import requests
import webbrowser
import os
import time
import json
import tempfile
import clr
clr.AddReference('System')
from System import DateTime
from System import TimeZoneInfo

class OAuthClient:
    def __init__(self, textblock_auth, textblock_print):
        self.textblock_print = textblock_print
        self.textblock = textblock_auth
        self.client_id = "0sgcI3BxtmdIIQoYtGe9xFkp72upFGpv"
        self.client_secret = "awUwBBGaDcOz9GpN"
        self.redirect_uri = "https://oauth.pstmn.io/v1/callback"
        self.auth_url = "https://developer.api.autodesk.com/authentication/v2/authorize"
        self.token_url = "https://developer.api.autodesk.com/authentication/v2/token"
        self.scope = "data:read data:write"
        self.state = "some_state"
        self.token_cache_file = os.path.join(tempfile.gettempdir(), "auth_token_cache.json")
        self.auth_code_cache_file = os.path.join(tempfile.gettempdir(), "auth_code_cache.json")
    
        self.temp_url = None
        
        self.auth_code = None
        self.auth_token = None

        # Last inn en cachet auth_code hvis den finnes
        auth_code = self.auth_code_load_cached()

        # Sjekke om det er en cached auth_code. Hvis det er se etter auth_token
        if auth_code:
            self.auth_code = auth_code
            self.auth_token = self.auth_token_get()
            return self.auth_token
        else:
            return None
    def auth_code_output(self):
        """
        Returns the authorization code stored by the client.

        :return: The authorization code (a string)
        """
        return self.auth_code
    
    def auth_token_output(self):
        return self.auth_token
    
    # Step 1: Get Authorization Code open browser
    def auth_code_open_browser(self):

        """
        Opens a web browser to get a new authorization code.

        The URL is constructed by using the authorization URL, client ID, redirect URI, scope and state.
        The user is expected to click "Allow" to give access to the client (this addon).

        :return: None
        """
        auth_request_url = "{}?response_type=code&client_id={}&redirect_uri={}&scope={}&state={}".format(
            self.auth_url, self.client_id, self.redirect_uri, self.scope, self.state)

        self.textblock.Text +=("Opening web browser to get new auth code. URL: {}\n".format(auth_request_url))
        webbrowser.open(auth_request_url)

        
    def auth_token_get(self):
        
        """
        Returns an access token to be used for API calls.

        First, this method checks if there is a cached token. If there is, it is returned.

        Second, this method checks if there is an authorization code. If there is not, it returns None.

        Third, this method uses the authorization code to get a new token. If the request is successful, the token is saved to cache and returned.

        :return: The access token (a string) or None if the authorization failed
        """
        # Første sjekk: Finnes en cached token?
        cached_token = self.auth_token_load_cached()

        if cached_token:
            self.textblock.Text +=("Using cached token\n")
            return cached_token

        # Andre sjekk: Finnes det en auth_code? Hvis ikke, hent en ny
        if self.auth_code is None:
            self.textblock.Text +=("Authorization failed. Could not obtain authorization code.\n")
            return None

        # Bruk auth_code til å få en token
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": self.auth_code  
        }

        response = requests.post(self.token_url, data=token_data)
        token_response = response.json()

        if response.status_code == 200:
            self.auth_token = 'Bearer {}'.format(token_response['access_token'])
            expires_in = token_response.get('expires_in', 3600)#3600
            self.auth_token_save(self.auth_token, expires_in)
            
            return self.auth_token
        else:
            self.textblock.Text +=("Failed to get access token")
            self.textblock.Text +=("Response:", token_response)
            return None

    def url_get(self,url = None):
        temp_url = url.strip()

        if temp_url:
            self.textblock.Text += ("URL entered: {}\n".format(url))
            return temp_url
        else:
            self.textblock.Text += ("No URL provided\n")
            return None        

    def parse_url(self, url):
        if "://" in url:
            scheme, rest = url.split("://", 1)
        else:
            scheme, rest = '', url

        if '/' in rest:
            netloc, path_query = rest.split('/', 1)
        else:
            netloc, path_query = rest, ''

        if '?' in path_query:
            path, query = path_query.split('?', 1)
        else:
            path, query = path_query, ''

        return {
            'scheme': scheme,
            'netloc': netloc,
            'path': '/' + path if path else '',
            'query': query
        }

    def parse_query(self, query):
        params = query.split('&')
        result = {}
        for param in params:
            if '=' in param:
                key, value = param.split('=', 1)
                if key in result:
                    result[key].append(value)
                else:
                    result[key] = [value]
        return result


    def auth_code_get(self,temp_url):
        parsed_url = self.parse_url(temp_url)
        query_params = self.parse_query(parsed_url['query'])

        self.auth_code = query_params.get('code', [None])[0]

        if self.auth_code is None:
            self.textblock.Text +=("Authorization code not found.\n")
        else:
            self.textblock.Text +=("Authorization code received.\n")
            self.auth_code_save(self.auth_code)  # Lagre auth_code for fremtidig bruk
            return self.auth_code
        
# Cached
    def auth_code_load_cached(self):
        if os.path.exists(self.auth_code_cache_file):
                
            with open(self.auth_code_cache_file, 'r') as f:
                auth_code_data = json.load(f)
                    
                if time.time() < auth_code_data['expiry']:
                    self.textblock.Text += ("Cached auth_code is valid.\n")
                    return auth_code_data['auth_code'] 
                else:
                    self.textblock.Text += ("Cached auth_code has expired.\n")
            return None       
    
    def auth_token_load_cached(self):
        if os.path.exists(self.token_cache_file):
            with open(self.token_cache_file, 'r') as f:
                token_data = json.load(f)
                
                if time.time() < token_data['expiry']:
                    self.textblock.Text +=("Cached token is valid.\n")
                    self.textblock.Text +=str(token_data['expiry'])
                    
                    return token_data['token']
                else:
                    self.textblock.Text +=("Cached token has expired.\n")
        return None

    def auth_code_save(self, auth_code):
        auth_code_data = {
            'auth_code': auth_code,
            'expiry': time.time() + 300 # 5 minutter, som angitt i dokumentasjonen
        }
        with open(self.auth_code_cache_file, 'w') as f:
            json.dump(auth_code_data, f)
        self.textblock.Text +=("Auth code has been cached.\n")
    
    def auth_token_save(self, token, expires_in):
        token_data = {
            'token': token,
            'expiry': time.time() + expires_in
        }
        with open(self.token_cache_file, 'w') as f:
            json.dump(token_data, f)
        self.textblock.Text +=("Token has been cached.\n")

