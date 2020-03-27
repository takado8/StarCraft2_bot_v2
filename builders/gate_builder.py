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

    async def proxy(self):
        pylons = self.ai.structures(unit.PYLON).ready
        if not self.ai.proxy_gate and pylons.exists and self.ai.structures(unit.CYBERNETICSCORE).ready.exists and self.ai.can_afford(unit.GATEWAY):
            pylon = pylons.further_than(40, self.ai.start_location.position)
            if pylon.ready.exists:
                pylon = pylon.furthest_to(self.ai.start_location.position)
                gates = self.ai.structures({unit.GATEWAY, unit.WARPGATE})
                if gates:
                    gates = gates.closer_than(9,pylon)
                else:
                    return
                if gates.amount < 1:
                    if not self.ai.already_pending(unit.GATEWAY):
                        worker = self.ai.units(unit.PROBE).closest_to(pylon)
                        await self.ai.build(unit.GATEWAY, near=pylon, build_worker=worker)
                else:
                    self.ai.proxy_gate = True


    async def three_standard(self):
        gates = self.ai.structures(unit.GATEWAY)
        gates.extend(self.ai.structures(unit.WARPGATE))
        gates_count = gates.amount
        if gates.ready.idle.exists:
            return
        if self.ai.structures(unit.ROBOTICSBAY).exists:
            gc = 4
        elif self.ai.structures(unit.ROBOTICSFACILITY).exists:
            gc = 3
        elif self.ai.structures(unit.CYBERNETICSCORE).exists:
            gc = 2
        else:
            gc = 1
        if gates_count < gc\
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 2:
            pylon = self.ai.get_proper_pylon()
            if pylon is not None:
                await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3,max_distance=20,
                                    random_alternative=True)

    async def three_blinkers(self):
        gates = self.ai.structures(unit.GATEWAY)
        gates.extend(self.ai.structures(unit.WARPGATE))
        gates_count = gates.amount

        if self.ai.structures(unit.TWILIGHTCOUNCIL).ready.exists:
            gc = 3
        # elif self.ai.structures(unit.CYBERNETICSCORE).exists:
        #     gc = 2
        else:
            gc = 1
        if gates_count < gc\
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 2:
            pylon = self.ai.get_proper_pylon()
            if pylon is not None:
                await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3,max_distance=20,
                                    random_alternative=True)

    async def three_rush(self):
        gates = self.ai.structures(unit.GATEWAY)
        gates.extend(self.ai.structures(unit.WARPGATE))
        if gates.exists:
            gates_count = gates.closer_than(30,self.ai.start_location).amount
        else:
            gates_count = 0
        # if gates.ready.idle.amount > 1:
        #     return
        if self.ai.structures(unit.CYBERNETICSCORE).exists:
            gc = 3
        else:
            gc = 1
        if gates_count < gc\
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 2:
            pylon = self.ai.get_proper_pylon()
            if pylon is not None:
                await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3,max_distance=20,
                                    random_alternative=True)

    async def upper_wall_plus_3(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount

        if self.ai.structures(unit.PYLON).ready.exists:
            placement = None
            if gates_count < 1 and self.ai.already_pending(unit.GATEWAY) < 1:
                placement = self.ai.main_base_ramp.protoss_wall_buildings[0]
            elif 0 < gates_count < 2:
                placement = self.ai.main_base_ramp.protoss_wall_buildings[1]
            elif 1 < gates_count < 4 and self.ai.structures(unit.CYBERNETICSCORE).exists and \
                    self.ai.already_pending(unit.GATEWAY) < 2:
                p = self.ai.get_proper_pylon()
                if p:
                    await self.ai.build(unit.GATEWAY,near=p,placement_step=3,max_distance=22,
                                        random_alternative=True)
                    return
            if placement:
                await self.ai.build(unit.GATEWAY,near=placement,placement_step=0,max_distance=0,
                                    random_alternative=False)

    async def upper_wall_plus_1(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount

        if self.ai.structures(unit.PYLON).ready.exists:
            placement = None
            if gates_count < 1 and self.ai.already_pending(unit.GATEWAY) < 1:
                placement = self.ai.main_base_ramp.protoss_wall_buildings[0]
            elif 0 < gates_count < 2:
                placement = self.ai.main_base_ramp.protoss_wall_buildings[1]
            elif 1 < gates_count < 3 and self.ai.structures(unit.CYBERNETICSCORE).exists and \
                    self.ai.already_pending(unit.GATEWAY) < 2:
                p = self.ai.get_proper_pylon()
                if p:
                    await self.ai.build(unit.GATEWAY,near=p,placement_step=3,max_distance=22,
                                        random_alternative=True)
                    return
            if placement:
                await self.ai.build(unit.GATEWAY,near=placement,placement_step=0,max_distance=0,
                                    random_alternative=False)

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

    async def one_standard(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount
        gc = 1
        pylon = self.ai.structures(unit.PYLON).ready
        if gates_count < gc \
                and self.ai.can_afford(unit.GATEWAY) and pylon.exists and \
                self.ai.already_pending(unit.GATEWAY) < 1:

            pylon = pylon.first
            if pylon is not None:
                await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3,max_distance=12,
                                    random_alternative=True)

    async def macro_lower_wall(self):
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
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3)
        elif 3 < gates_count < (9 if self.ai.minerals > 400 else 6) and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(
                unit.NEXUS).ready.amount > 1 and \
                self.ai.already_pending(unit.GATEWAY) < 1:
            pylon = self.ai.get_proper_pylon()
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3)

    async def macro(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount
        gc = 2 if self.ai.structures(unit.NEXUS).amount > 1 else 1
        if gates_count < gc \
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 1:
            pylon = self.ai.get_proper_pylon()
            if pylon is not None:
                await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3,max_distance=20,
                                    random_alternative=True)
        elif 1 < gates_count < 4 and self.ai.can_afford(unit.GATEWAY) and self.ai.time > 180 and \
                self.ai.already_pending(unit.GATEWAY) < 1:
            pylon = self.ai.get_proper_pylon()
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3)
        elif 3 < gates_count < (12 if self.ai.minerals > 400 else 6) and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(
                unit.NEXUS).ready.amount > 1 and \
                self.ai.already_pending(unit.GATEWAY) < 1:
            pylon = self.ai.get_proper_pylon()
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3)

    async def macro_colossus(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount
        gc = 2 if self.ai.structures(unit.NEXUS).amount > 1 else 0
        if gates_count < gc \
                and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(unit.PYLON).ready.exists and \
                self.ai.already_pending(unit.GATEWAY) < 1:
            pylon = self.ai.get_proper_pylon()
            if pylon is not None:
                await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3,max_distance=20,
                                    random_alternative=True)
        elif 1 < gates_count < 4 and self.ai.can_afford(unit.GATEWAY) and self.ai.time > 280 and \
                self.ai.already_pending(unit.GATEWAY) < 1 and self.ai.structures(unit.ROBOTICSFACILITY).exists:
            pylon = self.ai.get_proper_pylon()
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3)
        elif 3 < gates_count < (12 if self.ai.minerals > 400 else 7) and self.ai.can_afford(unit.GATEWAY) and self.ai.structures(
                unit.NEXUS).ready.amount > 1 and \
                self.ai.already_pending(unit.GATEWAY) < 1:
            pylon = self.ai.get_proper_pylon()
            if pylon is None:
                return
            await self.ai.build(unit.GATEWAY,near=pylon,placement_step=3, max_distance=40)