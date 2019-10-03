def filter_geospatial_file(file, _key, _filter):
    if isinstance(file, list):
        filtered_data = [item for item in file if item.get(_key) in _filter]
    elif isinstance(file, dict):
        filtered_data = {k: v for k, v in file.items() if v.get(_key) in _filter}
    else:
        print("Geospatial Data is not in list or dict form... Not sure what is wrong")
        return file
    return filtered_data