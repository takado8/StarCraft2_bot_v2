from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2


class PylonBuilder:
    @staticmethod
    async def next_standard(ai):
        if ai.structures(unit.PYLON).exists:
            if ai.time < 180:
                pending = 1
                left = 4
            else:
                pending = 2
                left = 6
            if ai.supply_left < left and ai.supply_cap < 200:
                if ai.can_afford(unit.PYLON) and ai.already_pending(unit.PYLON) < pending:
                    max_dist = 18
                    pl_step = 6
                    if ai.time < 180:
                        placement = await ai.find_placement(unit.PYLON, near=ai.start_location.position,
                                                              max_distance=18,
                                                              placement_step=6)
                        if ai.structures(unit.PYLON).closest_to(ai.main_base_ramp.top_center).distance_to(
                                placement) < 6:
                            return
                    elif ai.supply_cap < 100:
                        placement = ai.start_location.position
                    else:
                        placement = ai.start_location.position
                        max_dist = 40
                        pl_step = 3
                    await ai.build(unit.PYLON, near=placement, max_distance=max_dist, placement_step=pl_step)

    @staticmethod
    async def first_wall(ai):
        if ai.structures(unit.PYLON).amount < 1 and ai.can_afford(unit.PYLON) and not ai.already_pending(unit.PYLON):
            placement = Point2(ai.coords['pylon'])
            await ai.build(unit.PYLON, near=placement, placement_step=0, max_distance=0,random_alternative=False)
