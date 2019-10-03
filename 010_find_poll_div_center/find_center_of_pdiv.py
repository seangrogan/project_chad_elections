import datetime
import json
import statistics
import time

import numpy as np
from tqdm import tqdm

from file_readers.generic_esri_reader import generic_esri_reader
from file_readers.read_csv_file import read_csv_file
from file_readers.read_json_file import read_json_file
from parameters.par_file_reader import par_file_reader
from toolbox.geospatial_functions.filter_geospatial_file import filter_geospatial_file
from toolbox.geospatial_functions.shape_manipulations import get_multipolygon
from toolbox.toolbox import test_directory
import matplotlib.pyplot as plt

def find_map_center(div):
    polygons = get_multipolygon(div)
    centroid = polygons.centroid
    center = (centroid.x, centroid.y)
    return center


def find_pop_center(div, db_pd_association, db_data, db_centroids, center_type='mean'):
    k = f"{div['fed_num']}-{div['pd_num']}-{div['pd_nbr_sfx']}"
    dbs = db_pd_association.get(k)
    if dbs is None:
        return None
    population = dict()
    for db in dbs:
        try:
            pop = db_data.get(int(db)).get('DBpop_2016')
        except:
            pop = db_data.get(str(db)).get('DBpop_2016')
        try:
            cen = db_centroids.get(str(db))
        except:
            cen = db_centroids.get(int(db))
        population[db] = dict(pop=pop, center=cen)
    if center_type.lower() in {'mean', 'mean center', 'mean_center'}:
        center = _mean_center(population)
    elif center_type.lower() in {'median', 'median center', 'median_center'}:
        center = _median_center(population)
    elif center_type.lower() in {'geometric_center', 'geometric', 'geometric center'}:
        center = _geometric_center(population)
    else:
        return None
    return center


def _mean_center(population):
    try:
        centers, pop = [], []
        for db, val in population.items():
            centers.append(val.get('center'))
            pop.append(val.get('pop'))
        x, y = zip(*centers)
        _x = sum(i * j for i, j in zip(x, pop)) / sum(pop)
        _y = sum(i * j for i, j in zip(y, pop)) / sum(pop)
        center = (_x, _y)
    except:
        return None
    return center


def _median_center(population):
    try:
        centers = []
        for db, val in population.items():
            pop = val.get('pop')
            for i in range(pop):
                centers.append(val.get('center'))
        x, y = zip(*centers)
        center = (statistics.median(x), statistics.median(y))
    except:
        return None
    return center


def __plot_movement(population, centers):
    try:
        x, y, p = [],[],[]
        for db, val in population.items():
            x.append(val.get('center')[0])
            y.append(val.get('center')[1])
            p.append(val.get('pop'))
        c, d = zip(*centers)
        plt.scatter(x, y)
        for i, l in enumerate(p):
            plt.text(x[i], y[i], str(p[i]))
        plt.plot(c, d, color="red", marker="o")
        mean = _mean_center(population)
        median = _median_center(population)
        plt.plot(*mean, color="green", marker="o")
        plt.plot(*median, color="orange", marker="o")
        plt.plot(*centers[-1], color="purple", marker="o")
        plt.show()
        plt.close()
    except:
        pass


def _geometric_center(population, init_center=None, max_time=120, epsilon=0.1, max_iter=1000):
    try:
        if init_center is None:
            init_center = _mean_center(population)
        people = [val.get('center') for db, val in population.items() for _ in range(val.get('pop'))]
        y = [init_center]
        t0, i = time.time(), 0
        while (time.time() - t0) < max_time and i < max_iter:
            i += 1
            numerator = __compute_numerator(x=people, y_i=y[-1])
            denominator = __compute_denominator(x=people, y_i=y[-1])
            if denominator == 0:
                break
            _y = tuple(e / denominator for e in numerator)
            y.append(_y)
            if euclidean_dist(y[-1], y[-2]) < epsilon:
                break
        __plot_movement(population, y)
        return y[-1]
    except:
        return None


def __compute_numerator(x, y_i):
    _x = []
    for x_j in x:
        _x.append(tuple(e/euclidean_dist(x_j, y_i) for e in x_j))
    i, j = zip(*_x)
    _x = (sum(i), sum(j))
    return _x


def __compute_denominator(x, y_i):
    return sum((1/euclidean_dist(x_j, y_i)) for x_j in x)


def find_center_of_pdiv(parfile=None, province=35, outfile=None):
    print("Finding Centers of PollDivs")
    pars = par_file_reader(parfile)
    canada_poll_div_2015 = generic_esri_reader(pars.canada_poll_div_2015)
    db_pd_association = read_json_file(pars.db_pd_association)
    dissemination_block_cartographic = generic_esri_reader(pars.db_cartographic)
    db_data = read_csv_file(pars.db_data)
    db_data = {db.get("DBuid"): db for db in db_data}
    print("\tDone Reading Files")
    print("Filtering Files")
    diss_block = filter_geospatial_file(dissemination_block_cartographic,
                                        _key="pruid", _filter=str(province))
    db_centroids = {block.get("dbuid"): (block.get('dbrplamx'), block.get('dbrplamy')) for block in diss_block}
    poll_div = filter_geospatial_file(canada_poll_div_2015,
                                      _key='fed_num', _filter=range(province * 1000, (province + 1) * 1000))
    poll_div = filter_geospatial_file(poll_div, _key="pd_type", _filter={"N", "n"})
    print("\tDone Filtering Files")
    print("Finding Centers")
    results = dict()
    for div in tqdm(poll_div):
        map_center = find_map_center(div)
        pop_center = find_pop_center(div, db_pd_association, db_data, db_centroids)
        k = f"{div['fed_num']}-{div['pd_num']}-{div['pd_nbr_sfx']}"
        results[k] = dict(map_center=map_center, pop_center=pop_center,
                          diff=euclidean_dist(map_center, pop_center))
    print("\tDone Finding Centers")
    if outfile is None:
        outfile = f"../output/center_of_pdiv/pdiv_results{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    test_directory(outfile)
    with open(outfile, "w") as result_file:
        json.dump(results, result_file, indent=4)
    pass


def euclidean_dist(p1, p2):
    if p1 is None or p2 is None:
        return None
    dist = np.linalg.norm(np.array(p1) - np.array(p2))
    return dist


if __name__ == '__main__':
    find_center_of_pdiv()
