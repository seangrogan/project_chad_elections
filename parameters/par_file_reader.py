import json
import os
from argparse import Namespace


def par_file_reader(file_name=None, as_namespace=True):
    if file_name is None:
        file_name = "../parameters/par.json"
    name, ext = os.path.splitext(file_name)
    if ext not in {"json", ".json"}:
        file_name += ".json"
    with open(file_name) as json_file:
        parameters = json.load(json_file)
    if as_namespace:
        return Namespace(**parameters)
    return parameters


def get_prov_associations(file_name=None):
    if file_name is None:
        file_name = "./parameters/province_association_file.json"
    with open(file_name) as json_file:
        data = json.load(json_file)
    prov_association_file = {v.lower(): val for key, val in data.items() for k, v in val.items() if k not in {"region"}
                             if isinstance(v, str)}
    prov_association_file.update(
        {v.replace('.', ''): val for key, val in data.items() for k, v in val.items() if k not in {"region"}
         if isinstance(v, str)})
    prov_association_file.update({v: val for key, val in data.items() for k, v in val.items() if k not in {"region"}})
    return prov_association_file


if __name__ == '__main__':
    get_prov_associations("./province_association_file.json")
