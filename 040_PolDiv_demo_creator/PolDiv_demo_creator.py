import json
import os
from collections import namedtuple, defaultdict

from file_readers.read_csv_file import read_csv_file
from file_readers.read_json_file import read_json_file, write_json_file
from toolbox.toolbox import test_directory


def PolDiv_demo_creator():
    infile = "../output/associate_db_with_pd/results20191003_010613.json"
    da_data_folder = "../output/da_data_separated_20191002_144203/"
    DB_data = "/media/sean/F022FB6822FB31E8/gis_database/canada/2016_census/dissemination_blocks_data/DB.csv"
    PolDiv_DB_associations = read_poldiv_association_file(infile)
    da_files = get_files_in_this_folder(da_data_folder)
    PolDivs = PolDiv_DB_associations.keys()
    DB_datafile = read_csv_file(DB_data)
    DB_datafile = {entry.get("DBuid"): entry for entry in DB_datafile if entry.get("PRuid") == 35}
    for PolDiv in PolDivs:
        poldiv_da_data = get_associated_da_files(PolDiv, PolDiv_DB_associations, da_data_folder, da_files)
        convert_da_to_poldiv_data(PolDiv, set(DB[:-3] for DB in PolDiv_DB_associations[PolDiv]),
                                  PolDiv_DB_associations[PolDiv], DB_datafile, poldiv_da_data)
    pass


def get_associated_da_files(PolDiv, PolDiv_DB_associations, da_data_folder, da_files):
    print(f"Working on PolDiv {PolDiv.pd_num}-{PolDiv.pd_nbr_sfx} in FED {PolDiv.fed_num}")
    DBs = PolDiv_DB_associations[PolDiv]
    DAs = set(DB[:-3] for DB in DBs)
    relevant_da_files = [da_file for da_file in da_files if
                         any(set(da_file.replace('_', '.').split('.')).intersection(DAs))]
    return {file.replace('_', '.').split('.')[1]: read_csv_file(f"{da_data_folder}{file}") for file in
            relevant_da_files}
    # convert_da_to_poldiv_data(DBs, DAs, da_data)


def convert_da_to_poldiv_data(PolDiv, DAs, DBs, DB_datafile, DA_data):
    def make_da_pop(DBs, relevant_DBs):
        db_pop = {int(DB): relevant_DBs.get(int(DB)).get('DBpop_2016') for DB in DBs}
        da_pop = defaultdict(int)
        for DB in DBs:
            DA = DB[:-3]
            da_pop[DA] += relevant_DBs.get(int(DB)).get('DBpop_2016')
        return da_pop

    def make_demo_data(DA_pop, DA_data):
        def refactor_data():
            refactored_data = defaultdict(dict)
            for geo_name, DA in DA_data.items():
                for entry in DA:
                    refactored_data[entry.get(data_key)][geo_name] = Entry(
                        entry=entry,
                        local_pop=DA_pop[geo_name],
                        total_pop=DA_data[geo_name][0][pop_key]
                    )
            return refactored_data

        def get_task(_item):
            print(f"Unknown item {_item}")
            assert False

        def get_census_line_calculation(_DATA_ENTRY_ID, _entry, _census_entry_values):
            print(f"Unknown item DATA_ENTRY_ID = {_DATA_ENTRY_ID}")
            for _row in _entry.values() :
                print(f"         Census Entry Name = {_row.entry[name_key]}")
                break
            for _v in _census_entry_values:
                print(f"                      Data = {_v}")
            method = input("What Method Do You want to use?")
            parameters["census_demographic_manager"][method].append(_DATA_ENTRY_ID)
            canada_census_parameters(parameters)

        data_key = 'Member ID: Profile of Dissemination Areas (2247)'
        name_key = 'DIM: Profile of Dissemination Areas (2247)'
        pop_key = 'Dim: Sex (3): Member ID: [1]: Total - Sex'
        men_key = 'Dim: Sex (3): Member ID: [2]: Male'
        women_key = 'Dim: Sex (3): Member ID: [3]: Female'
        parameters = canada_census_parameters()
        Entry = namedtuple("Entry", ['entry', 'local_pop', 'total_pop'])
        refactored_data = refactor_data()
        new_demo_data = []
        for key, DA_entries in refactored_data.items():
            refactored_row = defaultdict(list)
            for entry, local_pop, total_pop in DA_entries.values():
                for entry_key, value in entry.items():
                    refactored_row[entry_key].append(Entry(value, local_pop, total_pop))
                pass
            new_row = dict()
            for census_entry_name, census_entry_values in refactored_row.items():
                if census_entry_name not in parameters["census_entry_manager"]:
                    get_task(census_entry_name)
                TASK = parameters["census_entry_manager"][census_entry_name]
                if TASK in {'keep'}:
                    new_row[census_entry_name] = census_entry_values[0].entry
                elif TASK in {'PollDiv'}:
                    new_row[census_entry_name] = "PollDiv"
                elif TASK in {'replace_geocode'}:
                    new_row[census_entry_name] = f"{PolDiv.fed_num}-{PolDiv.pd_num}-{PolDiv.pd_nbr_sfx}"
                elif TASK in {'max'}:
                    entries, local_pop, total_pop = zip(*census_entry_values)
                    new_row[census_entry_name] = max(entries)
                elif TASK in {'keep_all'}:
                    entries, local_pop, total_pop = zip(*census_entry_values)
                    entries = set(str(e) for e in entries)
                    new_row[census_entry_name] = ";".join(entries)
                elif TASK in {'calculate'}:
                    e, l, t = zip(*census_entry_values)
                    if all(isinstance(_, str) for _ in e):
                        new_row[census_entry_name] = ""
                    else:
                        CALCULATIONS = parameters["census_demographic_manager"]
                        DATA_ENTRY_ID = refactored_row[data_key][0].entry
                        calculated_value = 0
                        if DATA_ENTRY_ID in CALCULATIONS["sum"]:
                            for e, l, t in census_entry_values:
                                calculated_value += e * l / t
                        else:
                            get_census_line_calculation(DATA_ENTRY_ID, DA_entries, census_entry_values)
                        new_row[census_entry_name] = calculated_value
                    pass
                else:
                    print(f"{TASK} UNKNOWN")
                    assert False
                pass
            pass
            new_demo_data.append(new_row)
        pass

    relevant_DBs = {dbuid: entry for dbuid, entry in DB_datafile.items()}
    da_pop = make_da_pop(DBs, relevant_DBs)
    make_demo_data(da_pop, DA_data)
    pass


def canada_census_parameters(parameters=None):
    parameter_file = "./par/can_census_parameter.json"
    test_directory(parameter_file)
    if parameters is None:
        return read_json_file(parameter_file)
    else:
        write_json_file(obj=parameters, file=parameter_file)
        return parameters


def get_files_in_this_folder(folder_path):
    return os.listdir(folder_path)


def read_poldiv_association_file(infile):
    with open(infile) as file:
        PolDiv_DB_associations = json.load(file)
    PolDiv = namedtuple("PolDiv", ["fed_num", "pd_num", "pd_nbr_sfx"])
    PolDiv_DB = dict()
    for div, associations in PolDiv_DB_associations.items():
        div_items = div.split('-')
        div_items = [int(ele) for ele in div_items]
        PolDiv_DB[PolDiv(*div_items)] = associations
    return PolDiv_DB


if __name__ == '__main__':
    PolDiv_demo_creator()
