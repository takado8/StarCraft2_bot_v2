from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2


class PylonBuilder:
    def __init__(self, ai):
        self.ai = ai

    async def none(self):
        pass

    async def next_standard(self):
        pylons = self.ai.structures(unit.PYLON)
        if pylons.exists:
            if self.ai.time < 180:
                pending = 1
                left = 4
            else:
                pending = 2
                left = 6
            if self.ai.supply_left < left and self.ai.supply_cap < 200 or (pylons.amount < 2 and
                                                                           self.ai.structures(unit.GATEWAY).exists):
                if self.ai.can_afford(unit.PYLON) and self.ai.already_pending(unit.PYLON) < pending:
                    max_dist = 18
                    pl_step = 6
                    if self.ai.time < 180:
                        placement = await self.ai.find_placement(unit.PYLON, near=self.ai.start_location.position,
                                                              max_distance=18,
                                                              placement_step=6)
                        if self.ai.structures(unit.PYLON).closest_to(self.ai.main_base_ramp.top_center).distance_to(
                                placement) < 6:
                            return
                    elif self.ai.supply_cap < 100:
                        placement = self.ai.start_location.position
                    else:
                        placement = self.ai.start_location.position
                        max_dist = 40
                        pl_step = 3
                    await self.ai.build(unit.PYLON, near=placement, max_distance=max_dist, placement_step=pl_step)

    async def first_in_lower_wall(self):
        if self.ai.structures(unit.PYLON).amount < 1 and self.ai.can_afford(unit.PYLON) and not self.ai.already_pending(unit.PYLON):
            placement = Point2(self.ai.coords['pylon'])
            await self.ai.build(unit.PYLON, near=placement, placement_step=0, max_distance=0,random_alternative=False)

    async def first_in_upper_wall(self):
        if self.ai.structures(unit.PYLON).amount < 1 and self.ai.can_afford(unit.PYLON) and not self.ai.already_pending(unit.PYLON):
            placement = self.ai.main_base_ramp.protoss_wall_pylon

            await self.ai.build(unit.PYLON, near=placement, placement_step=0, max_distance=0,random_alternative=False)

    async def first_and_next_standard(self):
        pylons = self.ai.structures(unit.PYLON)
        if self.ai.time < 180:
            pending = 1
            left = 4
        else:
            pending = 2
            left = 6
        if self.ai.supply_left < left and self.ai.supply_cap < 200 or (pylons.amount < 2 and
                                                                       self.ai.structures(unit.GATEWAY).exists):
            if self.ai.can_afford(unit.PYLON) and self.ai.already_pending(unit.PYLON) < pending:
                # if self.ai.time < 180:
                # placement = await self.ai.find_placement(unit.PYLON,max_distance=24, placement_step=6,
                #     near=self.ai.start_location.position.towards(self.ai.main_base_ramp.top_center,6))

                # if pylons.exists and self.ai.structures(unit.PYLON).closest_to(self.ai.main_base_ramp.top_center).distance_to(
                #         placement) < 6:
                #     return
            # elif self.ai.supply_cap < 100:
            #     placement = self.ai.start_location.position
            # else:
            #     placement = self.ai.start_location.position
            #     max_dist = 40
            #     pl_step = 3
                await self.ai.build(unit.PYLON,max_distance=40, placement_step=7,
                        near=self.ai.start_location.position.towards(self.ai.main_base_ramp.top_center,6))


    async def proxy(self):
        pylons = self.ai.structures(unit.PYLON)
        if pylons.exists and self.ai.structures(unit.CYBERNETICSCORE).ready.exists:
            if pylons.further_than(40, self.ai.start_location.position).amount == 0 and not\
                self.ai.already_pending(unit.PYLON):
                pos = self.ai.game_info.map_center.position.towards(self.ai.enemy_start_locations[0], 25)
                c = 0
                placement = None
                while placement is None and c < 10:
                    c += 1
                    placement = await self.ai.find_placement(unit.PYLON, near=pos, max_distance=20, placement_step=2,
                                                     random_alternative=False)
                if placement is not None:
                    await self.ai.build(unit.PYLON, near=placement)