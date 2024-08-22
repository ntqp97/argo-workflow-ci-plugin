import re

def custome_response( phase: str, message: str) -> object:
    resp = {
        "node": {
            "phase": phase,
            "message": message
        }
    }
    return resp

def get_value(dictionary, key):
    value = dictionary.get(key, '')
    if value and isinstance(value, str) and value.isdigit():
        return int(value)
    return value

def is_version_string(string):
    pattern = r'^v?\d+\.\d+\.\d+$'
    return bool(re.match(pattern, string))

def get_branch_name(ref):
    if ref.startswith('refs/heads/'):
        return ref[len('refs/heads/'):]
    elif ref.startswith('refs/tags/'):
        return ref[len('refs/tags/'):]
    else:
        return ref
