import csv
import json
from collections import defaultdict, OrderedDict, Counter
from math import sqrt
from os import path
from time import sleep

import geocoder
from pyproj import Proj, transform
from tqdm import tqdm

from file_readers.read_csv_file import read_csv_file


class Parameters:
    # PolLocAddrs = "/media/sean/F022FB6822FB31E8/" \
    PolLocAddrs = "D:/" \
                  "gis_database/canada/polling_location_addresses/canada_polling_locations_19_10_2015_ontario.csv"
    APIKeys = "/home/sean/Desktop/prop_data/api_keys.json"


def make_a_CSV():
    data = get_data(file="addrs2.json")
    poldiv_centers = get_data(file="../output/center_of_pdiv/pdiv_results20191003_154557.json")
    output = []
    header = ["ed_num", "pd_pfx", 'pd_sufx', 'pd_ab',
              'pol_div_lat', 'pol_div_lon', 'pol_div_lam_x', 'pol_div_lam_y',
              'site', 'addr', 'city', 'postcode', 'prov', 'quality',
              'confidence',
              'pol_loc_lat', 'pol_loc_lon', 'lambert_x', 'lambert_y',
              'euclidean_meter', 'manhattan_meter', 'maximum_manhattan_meter'
              ]
    header += list(range(1, 2247 + 1))
    pbar = tqdm(total=len(data), desc="Running")
    for address, _info in list(data.items()):
        pbar.update()
        pbar.set_postfix_str(address[40:])
        site, addr, city, postcode, prov = _info['name'], _info['addr'], _info['city'], _info['pocd'], _info['prov']
        for poldiv in _info["PolDivs"]:
            ed_num, pd_pfx, pd_sufx, pd_ab = poldiv.split('-')
            if pd_sufx == "":
                pd_sufx = 0
            if "arcgis" in _info and f"{ed_num}-{pd_pfx}-{pd_sufx}" in poldiv_centers:
                if poldiv_centers[f"{ed_num}-{pd_pfx}-{pd_sufx}"]["pop_center"] is None:
                    pol_div_lam_x, pol_div_lam_y = poldiv_centers[f"{ed_num}-{pd_pfx}-{pd_sufx}"]["map_center"]
                else:
                    pol_div_lam_x, pol_div_lam_y = poldiv_centers[f"{ed_num}-{pd_pfx}-{pd_sufx}"]["pop_center"]
                pol_div_lon, pol_div_lat = to_wgs(pol_div_lam_x, pol_div_lam_y)
                lat, lon = _info.get("arcgis", {}).get('lat'), _info.get("arcgis", {}).get('lng')
                lambert_x, lambert_y = to_lambert(lat, lon)
                quality, confidence = _info.get("arcgis", {}).get('quality'), _info.get("arcgis", {}).get('confidence')
                euc_dist = sqrt(pow(lambert_x - pol_div_lam_x, 2) + pow(lambert_y - pol_div_lam_y, 2))
                manhattan = abs(lambert_x - pol_div_lam_x) + abs(lambert_y - pol_div_lam_y)
                max_manhattan = (euc_dist / sqrt(2))*2
            else:
                pol_div_lam_x, pol_div_lam_y, pol_div_lon, pol_div_lat, \
                lat, lon, lambert_x, lambert_y, quality, confidence, \
                euc_dist, manhattan, max_manhattan, *_ = [""] * 20

            row = dict(ed_num=ed_num, pd_pfx=pd_pfx, pd_sufx=pd_sufx, pd_ab=pd_ab,
                       pol_loc_lat=lat, pol_loc_lon=lon, quality=quality, confidence=confidence,
                       site=site, addr=addr, city=city, postcode=postcode, prov=prov,
                       lambert_x=lambert_x, lambert_y=lambert_y,
                       pol_div_lat=pol_div_lat, pol_div_lon=pol_div_lon,
                       pol_div_lam_x=pol_div_lam_x, pol_div_lam_y=pol_div_lam_y,
                       euclidean_meter=euc_dist, manhattan_meter=manhattan, maximum_manhattan_meter=max_manhattan)
            row.update(try_to_get_census_data(poldiv))
            output.append(row)
    with open("PolLocs.csv", "w", newline="", encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, header)
        writer.writeheader()
        writer.writerows(output)


def try_to_get_census_data(div):
    div = "-".join(div.split('-')[:3])
    folder = "../040_PolDiv_demo_creator/project_chad_elections/output/pol_div_demo_data/"
    file = f"{folder}{div}.csv"
    data_key = 'Dim: Sex (3): Member ID: [1]: Total - Sex'
    id_key = 'Member ID: Profile of Dissemination Areas (2247)'
    if path.exists(file):
        data = dict()
        f = read_csv_file(file)
        for row in f:
            data[row[id_key]] = row[data_key]
        return data
    else:
        return dict(zip(range(1, 2247 + 1), [""] * 2248))
    pass


def to_lambert(lat, lon=None):
    inProj = Proj(init='EPSG:4326')
    outProj = Proj(init='EPSG:3347')
    if lon is None:
        lat, lon = lat
    new_pt = transform(inProj, outProj, lon, lat)
    return new_pt


def to_wgs(lambert_x, lambert_y=None):
    outProj = Proj(init='EPSG:4326')
    inProj = Proj(init='EPSG:3347')
    if lambert_y is None:
        lambert_x, lambert_y = lambert_x
    new_pt = transform(inProj, outProj, lambert_x, lambert_y)
    return new_pt


def check_file():
    data = get_data(file="addrs.json")
    confidences, qualities = list(), list()
    relations = list()
    for address, information in data.items():
        if "arcgis" in information:
            confidence = information["arcgis"]["confidence"]
            quality = information["arcgis"]["quality"]
            if confidence < 7:
                information.pop("arcgis")
    counter1 = Counter(confidences)
    counter2 = Counter(qualities)
    counter3 = Counter(relations)
    update_file(data, "addrs2.json")
    pass


def refactor_file(file="addrs.json"):
    data1 = read_csv_file(Parameters.PolLocAddrs, encoding="utf-8-sig")
    # data = [row for row in data if row.get('type').lower() == 'ordinary']
    addresses_poldivs = defaultdict(set)
    addresses = dict()
    for row in data1:
        addresses_poldivs[make_addr(row)].add(make_pdiv_id(row))
        addresses[make_addr(row)] = make_addr_dict(row)
    with open(file) as in_file:
        data = json.load(in_file)
    print()
    new_data = dict()
    osm_elems = {'x', 'y', 'addr:country', 'addr:housenumber', 'addr:postal', 'addr:state', 'addr:street'}
    for k, v in data.items():
        osm = {item: value for item, value in v.items() if item in osm_elems}
        for item in osm_elems:
            v.pop(item, None)
        new_data[k] = v
        if osm:
            new_data[k].update({'osm': osm})
        new_data[k].update({"PolDivs": list(addresses_poldivs[k])})
        print()
    for k, v in addresses.items():
        if k not in new_data:
            new_data[k] = v
            new_data[k].update({"PolDivs": list(addresses_poldivs[k])})
    update_file(new_data, file='addrs_refactored.json')


def get_data(file="pol_div_geocoded.json"):
    with open(file) as in_file:
        data = json.load(in_file)
    return data


def update_file(data, file="addrs.json"):
    with open(file, "w", newline='') as out_file:
        json.dump(data, out_file, indent=4)


def failed_addrs(data, file="failed_addrs.csv"):
    with open(file, "w", newline='') as out_file:
        writer = csv.writer(out_file)
        for addr in data:
            writer.writerow([addr])


def main():
    print("Finding PolDiv addresses")
    headers = ["name"]
    data = read_csv_file(Parameters.PolLocAddrs, encoding="utf-8-sig")
    data = [row for row in data if row.get('type').lower() == 'ordinary']
    print(f"nLines {len(data)}")
    pol_divs = {make_pdiv_id(row): make_addr(row) for row in data}
    print(f"nPolDiv {len(pol_divs)}")
    addresses_poldivs = defaultdict(set)
    addresses = dict()
    for row in data:
        addresses_poldivs[make_addr(row)].add(make_pdiv_id(row))
        addresses[make_addr(row)] = make_addr_dict(row)
    print(f"nAddr {len(addresses_poldivs)}")
    print(f"nDivs {sum(len(val) for val in addresses_poldivs.values())}")
    failed = []
    # with open("/home/sean/Desktop/prop_data/api_keys.json") as keyfile:
    with open("D:/gis_database/api_keys/api_keys.json") as keyfile:
        BingMapsAPIKey = json.load(keyfile)["bing_maps"]
    # addresses, headers = get_file()
    # addresses = {make_addr2(row): row for row in addresses}
    addresses = get_data("addrs.json")
    p_bar = tqdm(total=len(addresses))
    for addr, items in addresses.items():
        p_bar.update()
        # if 'osm' in items or 'arcgis' in items:
        if 'arcgis' in items:
            continue
        sleep(2)
        new_addr = f"{items['addr']} {items['city']}, {items['prov']} {items['pocd']} CANADA"
        p_bar.set_postfix(ordered_dict=OrderedDict(Address=new_addr, NumFailed=len(failed)))
        result = None
        # g = geocoder.osm(new_addr)
        # result = g.osm
        # service = 'osm'
        if result is None:
            g = geocoder.arcgis(new_addr)
            result = g.json
            service = 'arcgis'
            if result is None:
                failed.append(addr)
                failed_addrs(failed)
                continue
        addresses[addr].update({service: result})
        for key in addresses[addr]:
            if key not in headers:
                headers.append(key)
        update_file(addresses)
    print(failed)

    return 0


def make_pdiv_id(row):
    row_id = f'{row.get("ed_num")}-{row.get("pd_pfx")}-{row.get("pd_sufx")}-{row.get("pd_ab")}'
    return row_id


def make_addr(row):
    row_addr = f'{row.get("site_name_en")} {row.get("addr_en")} ' \
               f'{row.get("municipality")} {row.get("province")} {row.get("postal_code")}'
    return row_addr


def make_addr2(row):
    row_addr = f'{row.get("name")} {row.get("addr")} ' \
               f'{row.get("city")} {row.get("prov")} {row.get("pocd")}'
    return row_addr


def make_addr_dict(row):
    return {
        "name": row.get("site_name_en"),
        "addr": row.get("addr_en"),
        "city": row.get("municipality"),
        "prov": row.get("province"),
        "pocd": row.get("postal_code")
    }


if __name__ == '__main__':
    # main()
    # check_file()
    make_a_CSV()
