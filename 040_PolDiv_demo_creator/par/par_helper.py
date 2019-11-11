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

members = defaultdict(list)
par = 'member_assigner.json'
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
    if row[data_key] in range(1, 2 + 1):
        method = 'population_proportional'
    elif row[data_key] in range(4, 4 + 1):  # dwelling section
        method = 'dwelling_calc'
    elif row[data_key] in range(5, 5 + 1):  # dwelling section
        method = 'dwelling_calc_usual'
    elif row[data_key] in range(8, 33 + 1):  # age
        method = 'population_proportional'
    elif row[data_key] in range(41, 56 + 1):  # dwelling section
        method = 'dwelling_calc'
    elif row[data_key] in range(59, 67 + 1):  # marriage
        method = 'population_proportional'
    elif row[data_key] in range(68, 72 + 1):  # household size
        method = 'dwelling_calc'
    elif row[data_key] in range(74, 99 + 1):  # family size
        method = 'dwelling_calc'
    elif row[data_key] in range(100, 110 + 1):  # Language Section
        method = 'population_proportional'
    elif row[data_key] in range(112, 660 + 1):  # another language section
        method = 'population_proportional'
    elif row[data_key] in range(661, 871 + 1):
        pass
    elif row[data_key] in range(872, 1134 + 1):  # another language section
        method = 'population_proportional'
    elif row[data_key] in range(1135, 1288 + 1):  # immigration status
        method = 'population_proportional'
    elif row[data_key] in range(1289, 1322 + 1):  # Aboriginal identity
        method = 'population_proportional'
    elif row[data_key] in range(1323, 1616 + 1):  # Ethnicity
        method = 'population_proportional'
    elif row[data_key] in range(1683, 1864 + 1):  # Academic Achievement
        method = 'population_proportional'
    elif row[data_key] in range(1865, 1877 + 1):  # Labor Force
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
