import datetime
import json
from collections import defaultdict


from tqdm import tqdm

from file_readers.generic_esri_reader import generic_esri_reader
from parameters.par_file_reader import par_file_reader
from toolbox.geospatial_functions.filter_geospatial_file import filter_geospatial_file
from toolbox.geospatial_functions.shape_manipulations import get_multipolygon, point_inside_polygon
from toolbox.toolbox import test_directory


def associate_db_with_pd(province=35, parfile=None, outfile=None):
    print("Associating DissBlocks with PollDivs")
    pars = par_file_reader(parfile)
    canada_poll_div_2015 = generic_esri_reader(pars.canada_poll_div_2015)
    dissemination_block_cartographic = generic_esri_reader(pars.db_cartographic)
    print("\tDone Reading Files")
    print("Filtering Files")
    poll_div = filter_geospatial_file(canada_poll_div_2015,
                                      _key='fed_num', _filter=range(province * 1000, (province + 1) * 1000))
    poll_div = filter_geospatial_file(poll_div, _key="pd_type", _filter={"N", "n"})
    diss_block = filter_geospatial_file(dissemination_block_cartographic,
                                        _key="pruid", _filter=str(province))
    print("\tDone Filtering Files")
    print("Centroid-ing the DBs")
    db_centroids = {block.get("dbuid"): (block.get('dbrplamx'), block.get('dbrplamy')) for block in diss_block}
    print("\tDone Getting DB Centroids")
    print("Finding DBs inside each PD")
    results = defaultdict(list)
    with tqdm(poll_div, desc="PD", postfix={"n_dbs": len(db_centroids)}) as pd:
        for div in pd:
            pd.set_postfix(n_dbs=len(db_centroids))
            k = f"{div['fed_num']}-{div['pd_num']}-{div['pd_nbr_sfx']}"
            polygons = get_multipolygon(div)
            results[k] = [db for db, centroid in db_centroids.items()
                          if point_inside_polygon(centroid, polygons)]
            for item in results[k]:
                db_centroids.pop(item, None)
    print("\t Done Finding DBs inside each PD")
    if outfile is None:
        outfile = f"./output/associate_db_with_pd/results{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    test_directory(outfile)
    with open(outfile, "w") as result_file:
        json.dump(results, result_file, indent=4)
    print("fin")




if __name__ == '__main__':
    associate_db_with_pd(35)
