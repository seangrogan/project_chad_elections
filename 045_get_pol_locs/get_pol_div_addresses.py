import csv
import json
from collections import defaultdict, OrderedDict
from time import sleep

import geocoder
from tqdm import tqdm

from file_readers.read_csv_file import read_csv_file


class Parameters:
    # PolLocAddrs = "/media/sean/F022FB6822FB31E8/" \
    PolLocAddrs = "D:/" \
                  "gis_database/canada/polling_location_addresses/canada_polling_locations_19_10_2015_ontario.csv"
    APIKeys = "/home/sean/Desktop/prop_data/api_keys.json"


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
    addresses = get_data()
    p_bar = tqdm(total=len(addresses))
    for addr, items in addresses.items():
        p_bar.update()
        if 'osm' in items or 'arcgis' in items:
            continue
        sleep(2)
        new_addr = f"{items['addr']} {items['city']}, {items['prov']} {items['pocd']} CANADA"
        p_bar.set_postfix(ordered_dict=OrderedDict(Address=new_addr, NumFailed=len(failed)))
        g = geocoder.osm(new_addr)
        result = g.osm
        service = 'osm'
        if result is None:
            g = geocoder.arcgis(new_addr)
            result = g.json
            service = 'arcgis'
            if result is None:
                failed.append(addr)
                failed_addrs(failed)
                continue
        addresses[addr].update({service:result})
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
    main()
