from datetime import datetime


def convert_datetime_to_str(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def convert_object_datetime_keys_to_str(obj):
    if isinstance(obj, dict):
        return {
            str(k): convert_datetime_to_str(v) for k, v in obj.items()
        }
    return obj