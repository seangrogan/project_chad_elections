import csv
import json
from collections import defaultdict, Counter

import geocoder
from tqdm import tqdm

from file_readers.read_csv_file import read_csv_file


class Parameters:
    PolLocAddrs = "/media/sean/F022FB6822FB31E8/" \
                  "gis_database/canada/polling_location_addresses/canada_polling_locations_19_10_2015_ontario.csv"
    APIKeys = "/home/sean/Desktop/prop_data/api_keys.json"


def main():
    print("Finding PolDiv addresses")
    data = read_csv_file(Parameters.PolLocAddrs, encoding="utf-8-sig")
    data = [row for row in data if row.get('type').lower() == 'ordinary']
    print(f"nLines {len(data)}")
    pol_divs = {make_pdiv_id(row): make_addr(row) for row in data}
    print(f"nPolDiv {len(pol_divs)}")
    addresses_poldivs = defaultdict(set)
    addresses = dict()
    for row in data:
        addresses_poldivs[make_addr(row)].add(make_pdiv_id(row))
        addresses[make_addr(row)]=make_addr_dict(row)
    print(f"nAddr {len(addresses_poldivs)}")
    print(f"nDivs {sum(len(val) for val in addresses_poldivs.values())}")
    failed = []
    with open("/home/sean/Desktop/prop_data/api_keys.json") as keyfile:
        BingMapsAPIKey = json.load(keyfile)["bing_maps"]
    for addr, split in tqdm(addresses.items()):
        new_addr = f"{split['addr']} {split['city']}, {split['prov']} {split['pocd']} CANADA"
        g = geocoder.osm(new_addr)
        result = g.osm
        if result is None:
            failed.append(addr)
            continue
        addresses[addr].update(result)
    print(failed)

    with open("addrs.csv", "w") as out_file:
        key, val = addresses.copy().popitem()
        header = list(val.keys())
        writer = csv.DictWriter(out_file, header)
        writer.writeheader()
        for addr in addresses.values():
            writer.writerow(addr)
    return 0


def make_pdiv_id(row):
    row_id = f'{row.get("ed_num")}-{row.get("pd_pfx")}-{row.get("pd_sufx")}-{row.get("pd_ab")}'
    return row_id


def make_addr(row):
    row_addr = f'{row.get("site_name_en")} {row.get("addr_en")} ' \
               f'{row.get("municipality")} {row.get("province")} {row.get("postal_code")}'
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
