import json
import os
from collections import namedtuple, defaultdict

from file_readers.read_csv_file import read_csv_file
from file_readers.read_json_file import read_json_file, write_json_file
from toolbox.toolbox import test_directory

infile = "../output/associate_db_with_pd/results20191003_010613.json"
da_data_folder = "../output/da_data_separated_20191002_144203/"
DB_data = "/media/sean/F022FB6822FB31E8/gis_database/canada/2016_census/dissemination_blocks_data/DB.csv"

data_key = 'Member ID: Profile of Dissemination Areas (2247)'
name_key = 'DIM: Profile of Dissemination Areas (2247)'
pop_key = 'Dim: Sex (3): Member ID: [1]: Total - Sex'
men_key = 'Dim: Sex (3): Member ID: [2]: Male'
women_key = 'Dim: Sex (3): Member ID: [3]: Female'
PolDivID = namedtuple("PolDiv", ["fed_num", "pd_num", "pd_nbr_sfx"])

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



def generate_demo_data_for_poll_div(DA_data, PolDiv, DAs,
                                    DA_population_proportions, DA_dwelling_count_proportions,
                                    DA_usual_dwelling_count_proportions,
                                    DA_area):
    demo_data = []
    census_manager = canada_census_parameters()
    for member_id, row_entry in DA_data.items():
        demo_data.append(build_row(row_entry, census_manager, PolDiv, member_id, DAs,
                                   DA_population_proportions, DA_dwelling_count_proportions,
                                   DA_usual_dwelling_count_proportions,
                                   DA_area))
    return demo_data


def build_row(row_entry, census_manager, PolDiv, member_id, DAs,
              DA_population_proportions, DA_dwelling_count_proportions,
              DA_usual_dwelling_count_proportions,
              DA_area):
    _row_to_build = dict()
    for column, col_val in row_entry.items():
        task = census_manager["census_column_manager"][column]
        if task in {"keep_one"}:  # Census year, etc...
            k, v = col_val.copy().popitem()
            _row_to_build[column] = v
        elif task in {"replace_with_geocode", "replace_geocode"}:
            _row_to_build[column] = get_poldiv_name(PolDiv)
        elif task in {"PollDiv"}:
            _row_to_build[column] = "PollDiv"
        elif task in {"max", "maximum"}:
            _row_to_build[column] = max(col_val.values())
        elif task in {"keep_all"}:
            _row_to_build[column] = ";".join(set(str(e) for e in col_val.values()))
        elif task in {"calculate"}:
            _row_to_build[column] = calculate_column(member_id, col_val, census_manager, DAs,
                                                     DA_population_proportions, DA_dwelling_count_proportions,
                                                     DA_usual_dwelling_count_proportions,
                                                     DA_area, PolDiv)
        else:
            raise RuntimeError(f"Unknown Column {column} in row {member_id}")
    return _row_to_build





def calculate_column(member_id, col_val, census_manager, DAs,
                     DA_population_proportions, DA_dwelling_count_proportions,
                     DA_usual_dwelling_count_proportions,
                     DA_area, PolDiv):
    while True:
        if all(isinstance(_, str) for _ in col_val.values()):
            return ""
        task = [_task for _task, _ids in census_manager["census_profile_manager"].items() if member_id in _ids]
        if task:
            task = task[0]
            if task in {"proportional", "proportion", "population_proportional"}:
                value = 0
                for DA in DAs:
                    value += col_val[DA] * DA_population_proportions[DA].local/DA_population_proportions[DA].total
                return value
            elif task in {"dwelling_calc"}:
                value = 0
                for DA in DAs:
                    value += col_val[DA] * DA_dwelling_count_proportions[DA].local / DA_dwelling_count_proportions[DA].total
                return value
            elif task in {"dwelling_calc_usual"}:
                value = 0
                for DA in DAs:
                    value += col_val[DA] * DA_usual_dwelling_count_proportions[DA].local / DA_usual_dwelling_count_proportions[DA].total
                return value
            elif task in {"geo_calc_1"}:
                area = get_pol_div_area(PolDiv, prov=35)
                area = area / 1_000_000
                pop, totals = zip(*DA_population_proportions.values())
                value = sum(pop)/area
                return value
            elif task in {"geo_calc_2"}:
                area = get_pol_div_area(PolDiv, prov=35)
                area = area / 1_000_000
                return area
            elif task in {"wt_avg"}:
                keys = list(col_val.keys())
                sums = 0
                wt_val = 0
                for key in keys:
                    sums += DA_population_proportions[key].local
                    wt_val += DA_population_proportions[key].local *  col_val[key]
                return wt_val/sums
            elif task in {"to_do"}:
                pass
            else:
                print("")
                input("LOL1")
        else:
            print(f"No task given for {member_id}")
            print(f"Column Vals: {col_val}")
            new_task = input("Please give me a task : ")
            census_manager["census_profile_manager"][new_task] = member_id

def get_pol_div_area(PolDiv, prov=35):
    PolDiv_areas = read_csv_file(DemoCreatorInfo.Files.PolDiv_area)
    PolDiv_areas = {PolDivID(PolDiv_area["fed_num".upper()],
                             PolDiv_area["pd_num".upper()],
                             PolDiv_area["pd_nbr_sfx".upper()]):
                        PolDiv_area["area"] for PolDiv_area in PolDiv_areas
                    if prov * 1000 <= PolDiv_area["fed_num".upper()] < (prov + 1) * 1000}
    return PolDiv_areas[PolDiv]

def canada_census_parameters(parameters=None):
    parameter_file = "./par/can_census_parameter.json"
    test_directory(parameter_file)
    if parameters is None:
        return read_json_file(parameter_file)
    else:
        write_json_file(obj=parameters, file=parameter_file)
        return parameters


def create_demographic_data_for_polldiv(PolDiv, DBs, DA_files, DB_data):
    print(f"Working on PolDiv {PolDiv.pd_num}-{PolDiv.pd_nbr_sfx} in FED {PolDiv.fed_num}")
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
    demo_data = generate_demo_data_for_poll_div(
        refactored_DA_data, PolDiv, DAs,
        DA_population_proportions, DA_dwelling_count_proportions, DA_usual_dwelling_count_proportions,
        DA_area
    )
    return demo_data


def PolDiv_demo_creator():
    DA_files, DB_data, PolDiv_DB_associations = get_files()
    PolDivs = list(PolDiv_DB_associations.keys())
    for PolDiv in PolDivs:
        create_demographic_data_for_polldiv(PolDiv, PolDiv_DB_associations[PolDiv], DA_files, DB_data)


def get_da_files(DAs, da_files):
    global da_data_folder
    relevant_da_files = [da_file for da_file in da_files if
                         any(set(da_file.replace('_', '.').split('.')).intersection(DAs))]
    return {file.replace('_', '.').split('.')[1]: read_csv_file(f"{da_data_folder}{file}") for file in
            relevant_da_files}


def get_files():
    def read_poldiv_association_file(fle):
        with open(fle) as file:
            PolDiv_DB_associations = json.load(file)
        PolDiv = namedtuple("PolDiv", ["fed_num", "pd_num", "pd_nbr_sfx"])
        PolDiv_DB = dict()
        for div, associations in PolDiv_DB_associations.items():
            div_items = div.split('-')
            div_items = [int(ele) for ele in div_items]
            PolDiv_DB[PolDiv(*div_items)] = associations
        return PolDiv_DB

    global infile
    global da_data_folder
    global DB_data
    DA_files = get_files_in_this_folder(da_data_folder)
    DB_data = read_csv_file(DB_data)
    DB_data = {entry.get("DBuid"): entry for entry in DB_data if entry.get("PRuid") == 35}
    PolDiv_DB_associations = read_poldiv_association_file(infile)
    return DA_files, DB_data, PolDiv_DB_associations


def get_DA_count(DBs, relevant_DBs, key='DBpop_2016'):
    db_pop = {int(DB): relevant_DBs.get(int(DB)).get(key) for DB in DBs}
    da_pop = defaultdict(int)
    for DB in DBs:
        DA = DB[:-3]
        da_pop[DA] += relevant_DBs.get(int(DB)).get(key)
    return da_pop


def get_files_in_this_folder(folder_path):
    return os.listdir(folder_path)


def get_poldiv_name(PolDiv):
    return f"{PolDiv.fed_num}-{PolDiv.pd_num}-{PolDiv.pd_nbr_sfx}"


def refactor_data(DA_data):
    refactored_data = defaultdict(lambda: defaultdict(dict))
    for geo_name, DA in DA_data.items():
        for entry in DA:
            for column, data in entry.items():
                refactored_data[entry.get(data_key)][column].update({geo_name: data})
    return refactored_data


def get_DA_totals(DA_data, member=None):
    DA_totals = dict()
    for DA, data in DA_data.items():
        DA_totals[DA] = data[member - 1][pop_key]
    return DA_totals


if __name__ == '__main__':
    PolDiv_demo_creator()
