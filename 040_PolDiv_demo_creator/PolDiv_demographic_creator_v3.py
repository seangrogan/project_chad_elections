import os
from collections import namedtuple, defaultdict

from file_readers.read_csv_file import read_csv_file
from file_readers.read_json_file import read_json_file


class DemoCreatorInfo:
    class Files:
        PolDiv_shape = "/media/sean/F022FB6822FB31E8/gis_database/" \
                       "canada/polling_divisions_boundaries_2015_shp/poll_div_bounds_2015.shp"
        PolDiv_area = "/home/sean/PycharmProjects/project_chad_elections/output/pol_div_area.csv"
        PolDiv_DB_association = "../output/associate_db_with_pd/results20191003_010613.json"
        DB_data = "/media/sean/F022FB6822FB31E8/gis_database/" \
                  "canada/2016_census/dissemination_blocks_data/DB.csv"
        DA_data_folder = "../output/da_data_separated_20191002_144203/"

    data_key = 'Member ID: Profile of Dissemination Areas (2247)'
    name_key = 'DIM: Profile of Dissemination Areas (2247)'
    pop_key = 'Dim: Sex (3): Member ID: [1]: Total - Sex'
    men_key = 'Dim: Sex (3): Member ID: [2]: Male'
    women_key = 'Dim: Sex (3): Member ID: [3]: Female'


def get_poldiv_name(PolDiv):
    return f"{PolDiv.fed_num}-{PolDiv.pd_num}-{PolDiv.pd_nbr_sfx}"


def get_files_in_this_folder(folder_path):
    return os.listdir(folder_path)


def get_DA_count(DBs, relevant_DBs, key='DBpop_2016'):
    db_pop = {int(DB): relevant_DBs.get(int(DB)).get(key) for DB in DBs}
    da_pop = defaultdict(int)
    for DB in DBs:
        DA = DB[:-3]
        da_pop[DA] += relevant_DBs.get(int(DB)).get(key)
    return da_pop


def get_DA_totals(DA_data, member=None):
    DA_totals = dict()
    for DA, data in DA_data.items():
        DA_totals[DA] = data[member - 1][DemoCreatorInfo.pop_key]
    return DA_totals


def refactor_data(DA_data):
    refactored_data = defaultdict(lambda: defaultdict(dict))
    for geo_name, DA in DA_data.items():
        for entry in DA:
            for column, data in entry.items():
                refactored_data[entry.get(DemoCreatorInfo.data_key)][column].update({geo_name: data})
    return refactored_data


def create_demographic_file(PolDiv, DA_files, PolDiv_areas, DBs, DB_data):
    print(f"Working on PolDiv {get_poldiv_name(PolDiv)}")
    DAs = set(DB[:-3] for DB in DBs)
    DA_data = get_da_files(DAs, DA_files)
    DA_population_count = get_DA_count(DBs, DB_data)
    DA_dwelling_count = get_DA_count(DBs, DB_data, key='DBtdwell_2016')
    DA_usual_dwelling_count = get_DA_count(DBs, DB_data, key='DBurdwell_2016')
    DA_area = get_DA_count(DBs, DB_data, key='DBarea')

    DA_pop_totals = get_DA_totals(DA_data, member=1)
    DA_dwelling_count_totals = get_DA_totals(DA_data, member=4)
    DA_usual_dwelling_count_totals = get_DA_totals(DA_data, member=5)

    Proportions = namedtuple("Proportions", ["local", "total"])
    DA_population_proportions = {DA: Proportions(
        local=DA_population_count[DA], total=DA_pop_totals[DA]) for DA in DAs}
    DA_dwelling_count_proportions = {DA: Proportions(
        local=DA_dwelling_count[DA], total=DA_dwelling_count_totals[DA]) for DA in DAs}
    DA_usual_dwelling_count_proportions = {DA: Proportions(
        local=DA_usual_dwelling_count[DA], total=DA_usual_dwelling_count_totals[DA]) for DA in DAs}

    refactored_DA_data = refactor_data(DA_data)
    demo_data = generate_demo_data_for_poll_div()
    return True


def generate_demo_data_for_poll_div(*args, **kwargs):
    pass


def PolDiv_demo_creator(prov=35):
    print("Creating Poll Demographic Data")
    PolDiv = namedtuple("PolDiv", ["fed_num", "pd_num", "pd_nbr_sfx"])
    PolDiv_DB_associations = read_json_file(DemoCreatorInfo.Files.PolDiv_DB_association)
    PolDiv_DB_associations = {PolDiv(*name.split("-")): val for name, val in PolDiv_DB_associations.items()}
    DB_data = read_csv_file(DemoCreatorInfo.Files.DB_data)
    PolDiv_areas = read_csv_file(DemoCreatorInfo.Files.PolDiv_area)
    PolDiv_areas = {PolDiv(PolDiv_area["fed_num".upper()],
                           PolDiv_area["pd_num".upper()],
                           PolDiv_area["pd_nbr_sfx".upper()]):
                        PolDiv_area["area"] for PolDiv_area in PolDiv_areas
                    if prov * 1000 <= PolDiv_area["fed_num".upper()] < (prov + 1) * 1000}
    PolDivs = list(PolDiv_DB_associations.keys())
    DA_files = get_files_in_this_folder(DemoCreatorInfo.Files.DA_data_folder)
    print()
    for PolDiv in PolDivs:
        create_demographic_file(PolDiv, DA_files, PolDiv_areas, PolDiv_DB_associations[PolDiv], DB_data)
    pass


def get_da_files(DAs, da_files):
    da_data_folder = DemoCreatorInfo.Files.DA_data_folder
    relevant_da_files = [da_file for da_file in da_files if
                         any(set(da_file.replace('_', '.').split('.')).intersection(DAs))]
    return {file.replace('_', '.').split('.')[1]: read_csv_file(f"{da_data_folder}{file}") for file in
            relevant_da_files}


if __name__ == '__main__':
    PolDiv_demo_creator()
