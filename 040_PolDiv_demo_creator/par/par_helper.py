from collections import defaultdict

from file_readers.read_csv_file import read_csv_file
from file_readers.read_json_file import read_json_file, write_json_file

can_census_file = "/media/sean/F022FB6822FB31E8/gis_database/canada/2016_census/dissemination_areas_data_detailed/ontario/separated_20190913_105814/35_Ontario.csv"

data = read_csv_file(can_census_file)

data_key = 'Member ID: Profile of Dissemination Areas (2247)'
name_key = 'DIM: Profile of Dissemination Areas (2247)'
pop_key = 'Dim: Sex (3): Member ID: [1]: Total - Sex'
men_key = 'Dim: Sex (3): Member ID: [2]: Male'
women_key = 'Dim: Sex (3): Member ID: [3]: Female'

def _range(start, stop=None):
    if stop is None:
        return range(start, start+1)
    return range(start, stop+1)


members = defaultdict(list)
par = 'member_assigner_v2.json'
_old = read_json_file(par)
members.update(_old)
k = sum(len(ele) for ele in members.values())
for row in data:
    if any(row[data_key] in member for member in members.values()):
        continue
    print(f"== {k:4d}/{len(data)} ==============================================")
    method = None
    k += 1
    print(f" Name = {row[name_key]}")
    print(f"   ID = {row[data_key]}")
    print(f"Total = {row[pop_key]}")
    print(f"  Men = {row[men_key]}")
    print(f"Women = {row[women_key]}")
    print(f"Current Keys {list(members.keys())}")
    if row[data_key] in _range(1, 2): # base pop row
        method = 'population_proportional'
    elif row[data_key] in _range(3): #pct inc
        method = "self_calc_pct_inc"
    elif row[data_key] in _range(4):  # dwelling section
        method = 'dwelling_calc'
    elif row[data_key] in _range(5):  # dwelling section
        method = 'dwelling_calc_usual'
    elif row[data_key] in _range(6):  # pop density
        method = "geo_calc_1"
    elif row[data_key] in _range(7):  # pop density
        method = "geo_calc_2"
    elif row[data_key] in _range(8, 33):  # age
        method = 'population_proportional'
    elif row[data_key] in _range(34, 40):  # age pct
        method = 'wt_avg'
    elif row[data_key] in _range(41, 56):  # dwelling section
        method = 'dwelling_calc'
    elif row[data_key] in _range(57):  # Number of persons in private households
        method = 'population_proportional'
    elif row[data_key] in _range(58):  # avg hh size
        method = 'wt_avg'
    elif row[data_key] in _range(59, 67):  #  Marital status for
        method = 'population_proportional'
    elif row[data_key] in _range(68, 72):  # household size
        method = 'dwelling_calc'
    elif row[data_key] in _range(73):  # household size
        method = 'wt_avg'
    elif row[data_key] in _range(74, 99):  # family size
        method = 'dwelling_calc'
    elif row[data_key] in _range(100, 110):  # Language Section
        method = 'population_proportional'
    elif row[data_key] in _range(112, 660):  # another language section
        method = 'population_proportional'
    elif row[data_key] in _range(661, 663):
        method = 'population_proportional'
    elif row[data_key] in _range(664, 871):
        if "median" in row[name_key].lower():
            method = 'wt_avg'
        elif "average" in row[name_key].lower():
            method = 'wt_avg'
        elif "percentage" in row[name_key].lower():
            method = 'wt_avg'
        else:
            method = 'population_proportional'
    elif row[data_key] in _range(872, 1134):  # another language section
        method = 'population_proportional'
    elif row[data_key] in _range(1135, 1288):  # immigration status
        method = 'population_proportional'
    elif row[data_key] in _range(1289, 1322):  # Aboriginal identity
        method = 'population_proportional'
    elif row[data_key] in _range(1323, 1616):  # Ethnicity
        method = 'population_proportional'
    elif row[data_key] in _range(1617, 1682):  # Ethnicity
        method = 'dwelling_calc'
    elif row[data_key] in _range(1683, 1864):  # Academic Achievement
        method = 'population_proportional'
    elif row[data_key] in _range(1865, 1877):  # Labor Force
        method = 'population_proportional'
    elif row[data_key] in range(1879, 1924 + 1):  # Labor Force
        method = 'population_proportional'
    elif row[data_key] in range(1925, 1949 + 1):  # Commute
        method = 'population_proportional'
    elif row[data_key] in range(1950, 2229 + 1):  # Yet another language section
        method = 'population_proportional'
    elif row[data_key] in range(2230, 2247 + 1):  # Movement
        method = 'population_proportional'
    else:
        method = input("Method?")
    if method is not None:
        members[method].append(row[data_key])
    write_json_file(dict(members), par)
for member in members.values():
    member.sort()
write_json_file(dict(members), par)
for k, v in members.items():
    print(f"{k}:{v}")
