from pyproj import Transformer


class ConvertCRS:
    _from, _to = None, None
    transformer = None

    def __init__(self, _from, _to, always_xy=True):
        self._from, self._to = _from, _to
        self.transformer = Transformer.from_crs(_from, _to, always_xy=always_xy)

    def convert_crs(self, point):
        assert len(point) == 2
        return self.transformer.transform(point[0], point[1])

    def convert_crs_polygon(self, polygon):
        new_polygon = [self.convert_crs(point) for point in polygon]
        return new_polygon
