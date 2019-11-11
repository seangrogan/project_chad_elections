import json
import os


def read_json_file(file):
    name, ext = os.path.splitext(file)
    if ext not in {"json", ".json"}:
        file += ".json"
    with open(file) as json_file:
        data = json.load(json_file)
    return data


def write_json_file(obj, file):
    name, ext = os.path.splitext(file)
    if ext not in {"json", ".json"}:
        file += ".json"
    with open(file, "w") as json_file:
        data = json.dump(obj, json_file, indent=4, )
    return data
