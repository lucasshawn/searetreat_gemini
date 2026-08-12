import urllib.request
import urllib.parse
import json
import os

def load_env(env_path: str = '.env'):
    """Load all key-value pairs from .env file into os.environ if missing."""
    if not os.path.exists(env_path):
        root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(root_env):
            env_path = root_env

    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"\'')
                    if k and not os.environ.get(k):
                        os.environ[k] = v

def load_pat(env_path: str = '.env') -> str:
    """Load Hospitable PAT from environment or .env file."""
    load_env(env_path)
    return os.environ.get('HOSPITABLE_PAT', '')

def fetch_reservations(start_date: str, end_date: str, property_id: str = "ae163eb2-66be-43b4-af71-2bfa6a2cf854", pat: str = None) -> list:
    """Fetch reservations from Hospitable API with pagination."""
    if not pat:
        pat = load_pat()

    all_reservations = []
    page = 1
    while True:
        params = urllib.parse.urlencode([
            ('properties[]', property_id),
            ('start_date', start_date),
            ('end_date', end_date),
            ('date_query', 'checkout'),
            ('include', 'financials,guest,listings,notes'),
            ('page', page)
        ])

        url = f'https://public.api.hospitable.com/v2/reservations?{params}'
        req = urllib.request.Request(url, headers={
            'Authorization': f'Bearer {pat}',
            'Accept': 'application/json',
            'User-Agent': 'Python/3.11'
        })

        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            res_list = data.get('data', [])
            all_reservations.extend(res_list)
            meta = data.get('meta', {})
            if meta.get('current_page', page) >= meta.get('last_page', page) or not res_list:
                break
            page += 1

    return all_reservations
