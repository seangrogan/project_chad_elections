import csv
import os


def try_to_numeric(value):
    try:
        return int(value)
    except:
        try:
            return float(value)
        except:
            return value


def read_csv_file(file):
    name, ext = os.path.splitext(file)
    if ext not in {"csv", ".csv"}:
        file += ".csv"
    with open(file) as csv_file:
        reader = csv.DictReader(csv_file)
        data = [item for item in reader]
        data = [{key: try_to_numeric(val) for key, val in item.items()} for item in data]
    return data
