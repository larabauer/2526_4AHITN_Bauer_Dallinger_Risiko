import xml.etree.ElementTree as ET
from svgpathtools import parse_path

from map_data import MapData
from territory import Territory, svg_to_screen


class MapLoader:
    CONTINENT_COLORS = {
        # Australien
        "eastern_australia": (200, 100, 50),
        "western_australia": (200, 100, 50),
        "new_guinea":        (200, 100, 50),
        "indonesia":         (200, 100, 50),
        # Nordamerika
        "alaska":                  (100, 180, 100),
        "ontario":                 (100, 180, 100),
        "northwest_territory":     (100, 180, 100),
        "quebec":                  (100, 180, 100),
        "eastern_united_states":   (100, 180, 100),
        "western_united_states":   (100, 180, 100),
        "central_america":         (100, 180, 100),
        "alberta":                 (100, 180, 100),
        "greenland":               (100, 180, 100),
        # Südamerika
        "venezuela": (220, 180, 50),
        "brazil":    (220, 180, 50),
        "peru":      (220, 180, 50),
        "argentina": (220, 180, 50),
        # Europa
        "iceland":          (150, 200, 220),
        "great_britain":    (150, 200, 220),
        "scandinavia":      (150, 200, 220),
        "northern_europe":  (150, 200, 220),
        "western_europe":   (150, 200, 220),
        "southern_europe":  (150, 200, 220),
        "ukraine":          (150, 200, 220),
        # Afrika
        "north_africa": (220, 160, 80),
        "egypt":        (220, 160, 80),
        "east_africa":  (220, 160, 80),
        "congo":        (220, 160, 80),
        "south_africa": (220, 160, 80),
        "madagascar":   (220, 160, 80),
        # Asien
        "ural":        (180, 120, 200),
        "siberia":     (180, 120, 200),
        "yakutsk":     (180, 120, 200),
        "kamchatka":   (180, 120, 200),
        "irkutsk":     (180, 120, 200),
        "mongolia":    (180, 120, 200),
        "china":       (180, 120, 200),
        "afghanistan": (180, 120, 200),
        "middle_east": (180, 120, 200),
        "india":       (180, 120, 200),
        "siam":        (180, 120, 200),
        "japan":       (180, 120, 200),
    }

    @staticmethod
    def load_territories() -> list[Territory]:
        tree = ET.parse("risk_map.svg")
        root = tree.getroot()

        valid_names = set(MapData.get_country_names())  # ← MapData statt initialCountries
        territories = []

        for elem in root.iter("{http://www.w3.org/2000/svg}path"):
            name = elem.get("id", "")
            if name not in valid_names:
                continue

            d = elem.get("d", "")
            if not d:
                continue

            try:
                path = parse_path(d)
            except Exception:
                continue

            points = [svg_to_screen(seg.start.real, seg.start.imag) for seg in path]
            if len(points) < 3:
                continue


            neighbors = MapData.get_country_neighbours(name)

            color = MapLoader.CONTINENT_COLORS.get(name, (180, 180, 180))
            territories.append(Territory(name, points, color, neighbors))


        print(f"Territorien geladen: {len(territories)}")
        return territories