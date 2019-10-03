from toolbox.geospatial_functions import filter_geospatial_file
from file_readers import generic_esri_reader
from zz_old_files.parameters.par_file_reader import par_file_reader
import matplotlib.pyplot as plt

from pyproj import CRS, transform






def main():
    pars = par_file_reader("./parameters/par.json")
    canada_poll_div_2015 = generic_esri_reader(pars.canada_poll_div_2015)
    ontario_poll_div_2015 = filter_geospatial_file(canada_poll_div_2015,
                                                   _key='fed_num', _filter=range(35000, 36000))

    crs1 = CRS.from_epsg(pars.input_crs)
    crs2 = CRS.from_epsg(pars.wgs84)
    for div in ontario_poll_div_2015:
        print(div.get('fed_num'))
        # center = get_center_of_mass_of_shape(div.get("shape"))
        center = (center.x, center.y)
        new_shape = [transform(crs1, crs2 , pt[0], pt[1]) for pt in div['shape'].points]
        x, y = zip(*new_shape)
        plt.plot(x, y)
        new_center = transform(crs1, crs2 ,center[0], center[1])
        plt.scatter(new_center[0], new_center[1])
        plt.title(f"{div.get('pd_num')}-{div.get('pd_nbr_sfx')}-{div.get('fed_num')} ({div.get('poll_name')})")
        plt.savefig(f"./output/centroids/{div.get('pd_num')}-{div.get('pd_nbr_sfx')}-{div.get('fed_num')}.png")
        plt.close()
    print("Fin")


if __name__ == '__main__':
    main()