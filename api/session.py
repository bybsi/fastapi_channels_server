import os
import json

SESSION_DIR = '/var/data/session'

def load(bs_sid: str):
    try:
        filepath = os.path.join(SESSION_DIR, bs_sid)
        with open(filepath, 'r') as fh:
            data = json.loads(fh.readline())
            if 'user_id' not in data:
                return None
            # Remove things that are not needed
            if 'expires' in data:
                del data['expires']
            if 'contact_data' in data:
                del data['contact_data']
            if 'settings_json' in data:
                del data['settings_json']
            #data['user_id'] = str(data['user_id'])
            data['user_id'] = int(data['user_id'])
            data['channel'] = None
            return data
    except IOError as exc:
        print(f"Could not open session file {filepath}")
    except Exception as exc:
        print(f"Unknown exception opening session file {filepath} {exc}")
    return None

