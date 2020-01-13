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
                left = 8
            if self.ai.supply_left < left and self.ai.supply_cap < 200 or (pylons.amount < 2 and
                                                                           self.ai.structures(unit.GATEWAY).exists):
                if self.ai.can_afford(unit.PYLON) and self.ai.already_pending(unit.PYLON) < pending:
                    max_dist = 40
                    pl_step = 5

                    await self.ai.build(unit.PYLON, near=self.ai.start_location.position.towards(self.ai.main_base_ramp.top_center,5), max_distance=max_dist, placement_step=pl_step)

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
            step = 9
        else:
            pending = 2
            left = 8
            step = 5
        if self.ai.supply_left < left and self.ai.supply_cap < 200 or (pylons.amount < 2 and
                                                                       self.ai.structures(unit.GATEWAY).exists):
            if self.ai.can_afford(unit.PYLON) and self.ai.already_pending(unit.PYLON) < pending:
                await self.ai.build(unit.PYLON,max_distance=40, placement_step=step,
                        near=self.ai.start_location.position.towards(self.ai.main_base_ramp.top_center,5))

    async def proxy(self):
        pylons = self.ai.structures(unit.PYLON)
        if pylons.exists and self.ai.structures(unit.CYBERNETICSCORE).exists:
            if pylons.further_than(40, self.ai.start_location.position).amount == 0 and not\
                self.ai.already_pending(unit.PYLON):
                pos = Point2(self.ai.coords['proxy'])
                c = 0
                placement = None
                while placement is None and c < 10:
                    c += 1
                    placement = await self.ai.find_placement(unit.PYLON, near=pos, max_distance=2, placement_step=2,
                                                     random_alternative=False)
                if placement is not None:
                    worker = self.ai.units(unit.PROBE).closest_to(placement)
                    await self.ai.build(unit.PYLON, near=placement, build_worker=worker)
                    self.ai.do(worker.hold_position(queue=True))
