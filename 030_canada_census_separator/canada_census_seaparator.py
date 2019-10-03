import argparse
import csv
import datetime
import os
import random
from multiprocessing import Process

from tqdm import tqdm


def canada_census_separator(folder=None, args=None):
    print("Canada Census Separator Program")
    print("Converts a Canada Census CSV Multiple CSV ")
    folder = "./data/" if folder is None else folder
    print(f"Finding files in folder {folder}")
    files = parse_folder(folder)
    row_info = read_csv_dict(files.get("row_info"))
    # ccs = CanadaCensusStructure()
    # ccs.read_meta_file(files.get("meta"))
    parse_data_file(files.get("data"), row_info.copy(), encoding="utf-8-sig")
    pass


def parse_data_file(file, row_info, encoding="utf-8-sig"):
    count = len(row_info)
    current_info, next_info = row_info.pop(0), row_info.pop(0)
    count *= abs(current_info["Line Number"] - next_info["Line Number"])
    tstr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    default_row = {"Line Number": float('inf')}
    with open(file, encoding=encoding) as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)
        info = []
        with tqdm(csv_reader, desc="Census Data Row", unit='line', total=count) as pbar:
            for idx, row in enumerate(pbar, start=2):
                if idx < next_info["Line Number"]:
                    row = [_try_to_numeric(element) for element in row]
                    data = dict(zip(header, row))
                    info.append(data)
                else:
                    write_output(tstr, current_info, header, info, outprocess=False)
                    current_info = next_info
                    try:
                        next_info = row_info.pop(0)
                    except IndexError:
                        next_info = default_row
                    info = []
                    row = [_try_to_numeric(element) for element in row]
                    data = dict(zip(header, row))
                    info.append(data)
                    pbar.set_postfix(GeoName=str(current_info["Geo Name"]))


def write_output(tstr, current_info, header, info, outprocess=True):
    if isinstance(outprocess, str) and outprocess.lower() in {'rand', 'random', 'r'}:
        outprocess = random.choice([True, False])
    if outprocess:
        p_args = (tstr, current_info.copy(), header.copy(), info.copy())
        Process(target=_write_output, args=p_args).start()
    else:
        _write_output(tstr, current_info, header, info)


def _write_output(tstr, current_info, header, info):
    # outfile = "D:/gis_database/canada/2016_census/dissemination_areas_data_detailed/ontario"
    outfile = f"./output/da_data_separated_{tstr}/" + \
              "{Geo Code}_{Geo Name}.csv".format(**current_info).replace('/', '-')
    _makepath(outfile)
    with open(outfile, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for outrow in info:
            writer.writerow(outrow)


def read_csv_dict(file, encoding="utf-8-sig"):
    print(f"Reading {file}")
    with open(file, encoding=encoding) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data = [{key: _try_to_numeric(val) for key, val in row.items()} for row in csv_reader]
    return data


def read_csv_list(file, encoding="utf-8-sig"):
    with open(file, encoding=encoding) as csv_file:
        csv_reader = csv.reader(csv_file)
        data = [row for row in csv_reader]
        data = [[_try_to_numeric(element) for element in row] for row in data]
    return data


def _makepath(path):
    p = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(p):
        os.makedirs(p)


def _try_to_numeric(value):
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def parse_folder(folder):
    files = os.listdir(folder)
    data = {
        "meta": None,
        "data": None,
        "row_info": None,
        "readme": None
    }
    for file in files:
        if 'zip' in file.lower():
            pass
        elif 'readme' in file.lower():
            data["readme"] = folder + file
        elif 'meta' in file.lower():
            data["meta"] = folder + file
        elif 'data' in file.lower():
            data["data"] = folder + file
        elif 'starting' in file.lower():
            data["row_info"] = folder + file
    return data


def _ccc_argparse():
    parser = argparse.ArgumentParser(description='Canada Census Converter Program')
    parser.add_argument('-folder', help="Folder", default=None)
    parser.add_argument('-zipfile', '-zf', '-zip', '-z',
                        help='If you\'re lazy and haven\'t unzipped te file.')
    return parser.parse_args()


if __name__ == '__main__':
    args = _ccc_argparse()
    folder = "/media/sean/F022FB6822FB31E8/gis_database/canada/2016_census/dissemination_areas_data_detailed/ontario/"
    canada_census_separator(folder)
