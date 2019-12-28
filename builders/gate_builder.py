from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2


class GateBuilder:
    def __init__(self, ai):
        self.ai = ai

    async def two_in_lower_wall(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount
        if self.ai.structures(unit.NEXUS).amount < 2:
            gc = 1
        else:
            gc = 2
        if gates_count < gc \
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 2:
            if gates_count < 1:
                pylon = Point2(self.ai.coords['gate1'])
            else:
                pylon = Point2(self.ai.coords['gate2'])
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=0,max_distance=0,random_alternative=False)


    async def two_in_upper_plus_1(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount
        gc = 3
        if gates_count < gc \
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 2:
            if gates_count < 1:
                pylon = self.ai.main_base_ramp.protoss_wall_buildings[0]
                if pylon is not None:
                    await self.ai.build(unit.GATEWAY,near=pylon,placement_step=0,max_distance=0,
                                        random_alternative=False)
            else:
                pylon = self.ai.get_proper_pylon()
                if pylon is not None:
                    await self.ai.build(unit.GATEWAY,near=pylon,placement_step=2,max_distance=20,
                                        random_alternative=True)

    async def one_in_upper(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount
        gc = 1
        if gates_count < gc \
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 1:

            pylon = self.ai.main_base_ramp.protoss_wall_buildings[0]
            if pylon is not None:
                await self.ai.build(unit.GATEWAY,near=pylon,placement_step=0,max_distance=0,
                                    random_alternative=False)



    async def macro(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount

        if self.ai.structures(unit.NEXUS).amount < 2:
            gc = 1
        else:
            gc = 2
        if gates_count < gc \
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 2:

            if gates_count < 1:
                pylon = Point2(self.ai.coords['gate1'])
            else:
                pylon = Point2(self.ai.coords['gate2'])
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=0,max_distance=0,random_alternative=False)
        elif 1 < gates_count < 4 and self.ai.can_afford(unit.GATEWAY) and self.ai.time > 180 and \
                self.ai.already_pending(unit.GATEWAY) < 1:
            pylon = self.ai.get_proper_pylon()
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=2)
        elif 3 < gates_count < (9 if self.ai.minerals > 400 else 6) and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(
                unit.NEXUS).ready.amount > 1 and \
                self.ai.already_pending(unit.GATEWAY) < 1:
            pylon = self.ai.get_proper_pylon()
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=2)