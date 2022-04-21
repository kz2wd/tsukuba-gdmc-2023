from typing import Dict, Tuple, Set

import numpy as np
from gdpc import geometry as GEO
from gdpc import interface as INTF

import random
import time

from build_area import Plot
from utils import Coordinates, Block


class ConstructionPlot(Plot):
    _WORST_SCORE = 100_000_000

    def __init__(self, x: int, z: int, size: Tuple[int, int], construction_roof: int = 200):
        super().__init__(x, z, size)

        self.construction_roof = construction_roof
        self.occupied_coords: Set[Coordinates] = set()
        self._construction_heightmap: np.array = None
        self.foundation_blocks: Dict[Coordinates, Block] = dict()

    def _build_foundation_blocks(self) -> None:
        surface_blocks = dict()
        self._construction_heightmap = self.get_heightmap("MOTION_BLOCKING_NO_LEAVES")

        for x, rest in enumerate(self._construction_heightmap):
            for z, h in enumerate(rest):
                coordinates = Coordinates(self.start.x + x, h - 1, self.start.z + z)

                if coordinates in self.occupied_coords:
                    continue

                block = self.get_block_at(*coordinates)

                # We don't want to be on water or too high in the sky
                if not block.is_one_of(["water"]) and block.coordinates.y < self.construction_roof:

                    surface_blocks[coordinates] = self.get_block_at(*coordinates)

        self.foundation_blocks = surface_blocks

    def get_construction_spot(self, size: Tuple[int, int], speed: int = None) -> Coordinates:
        """Return the best coordinates to place a building of a certain size, minimizing its score.
            Score is defined by get_score function.

            heightmap
            """
        if speed is None:
            # Auto speed depends on structure size, and is at least 1
            # Todo : Should depend on plot size too
            # speed = max(max(size[0], size[1]) // 5, 1)
            # print(f"Auto determined speed {speed} for house of size {size}")
            speed = 1

        # This will update the foundation_block dict, as well as the _construction_heightmap
        self._build_foundation_blocks()

        # DEBUG
        print(len(self.occupied_coords))

        for coord in self.foundation_blocks:
            INTF.placeBlock(*coord, 'red_wool')
        INTF.sendBlocks()
        input("Press a key to continue")
        # END DEBUG

        keys_list = list(self.foundation_blocks.keys())

        # >Get the minimal score in the coordinate list
        min_score = ConstructionPlot._WORST_SCORE
        best_spot = keys_list[0]
        for coord in keys_list[::speed]:
            coord_score = self._get_score(coord, size)
            if coord_score < min_score:
                best_spot = coord
                min_score = coord_score

        print(f'Best score : {min_score}')

        return best_spot

    def _get_score(self, coord: Coordinates, size: Tuple[int, int]) -> float:
        """Return a score evaluating the fitness of a building in an area.
            The lower the score, the better it fits

            Score is calculated as follows :
            malus depending on the distance from the center of the area +
            Sum of all differences in the y coordinate
            """
        # apply malus to score depending on the distance to the 'center'
        # Todo : Maybe improve this notation, quite not beautiful, set center as a coordinate ? Would be great
        score = coord.with_y(0).distance(Coordinates(self.center[0], 0, self.center[1])) * .1

        # Score = sum of difference between the first point's altitude and the other
        for x in range(size[0]):
            for z in range(size[1]):
                try:
                    current = coord.shift(x, 0, z)
                    if current in self:
                        score += abs(coord.y - self._get_y(current.x, current.y))
                    else:
                        # Out of bound :3
                        return ConstructionPlot._WORST_SCORE
                except KeyError:
                    # Out of bound :3
                    return ConstructionPlot._WORST_SCORE
        return score

    def occupy_area(self, origin: Coordinates, size: Tuple[int, int], padding: int = 0) -> None:
        """Set all the coordinates in the size given, starting from the origin, and in the padding, as occupied, and so
        unusable as foundations for other constructions"""
        for x in range(-padding, size[0] + padding):
            for z in range(-padding, size[1] + padding):
                self.occupied_coords.add(origin.shift(size[0] + x, 0, size[1] + z).with_y(0))

    def _get_y(self, x: int, z: int) -> int:
        relative_x = x - self.start.x
        relative_z = z - self.start.z
        return self._construction_heightmap[relative_x, relative_z]


def build_simple_house(main_bloc: str, start: Coordinates, size: tuple[int, int, int]):
    """Build a 'house' of the main_bloc given, with north-west bottom corner as starting point, with the given size"""
    # Todo : finish the simple houses
    # body
    GEO.placeCuboid(start.x, start.y, start.z, start.x + size[0] - 1, start.y + size[1] - 1, start.z + size[2] - 1,
                    main_bloc, hollow=True)
    INTF.sendBlocks()
    # Todo : add direction
    # Door
    INTF.placeBlock(start.x + size[0] // 2, start.y + 1, start.z, "oak_door")
    INTF.placeBlock(start.x + size[0] // 2, start.y + 2, start.z, "oak_door[half=upper]")




