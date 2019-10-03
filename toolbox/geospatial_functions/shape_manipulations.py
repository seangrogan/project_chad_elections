from shapely.geometry import Polygon, MultiPolygon, Point

def get_multipolygon(shape_entry):
    points = shape_entry['shape'].points
    parts = list(shape_entry['shape'].parts) + [-1]
    polygons = MultiPolygon([Polygon(points[i:j]) for i, j in zip(parts, parts[1:])])
    return polygons


def point_inside_shapefile(point, shape_entry):
    points = shape_entry['shape'].points
    parts = list(shape_entry['shape'].parts) + [-1]
    polygons = MultiPolygon([Polygon(points[i:j]) for i, j in zip(parts, parts[1:])])
    return polygons.contains(Point(point))


def point_inside_polygon(point, polygons):
    return polygons.contains(Point(point))


def get_center(shapefile_entry):
    points = shapefile_entry["shape"].points
    parts = list(shapefile_entry["shape"].parts) + [-1]
    if len(parts) == 1:
        poly = Polygon(points)
        return poly.centroid
    polygons = [Polygon(points[i:j]) for i, j in zip(parts, parts[1:])]
    polygons = MultiPolygon(polygons)
    return polygons.centroid
