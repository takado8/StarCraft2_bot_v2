from sc2.ids.unit_typeid import UnitTypeId as unit


class Expander:
    def __init__(self, ai):
        self.ai = ai

    async def standard(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount
        # if gates_count < 1:
        #     return
        nexuses = self.ai.structures(unit.NEXUS).ready
        if nexuses.amount < 2:
            self.ai.proper_nexus_count = 2
            if self.ai.can_afford(unit.NEXUS) and not self.ai.already_pending(unit.NEXUS):
                await self._expand_now2()
        elif 3 > nexuses.amount > 1 and self.ai.units(
                unit.PROBE).amount >= 34 and (len(self.ai.army) > 12 or self.ai.minerals > 600):
            if self.ai.proper_nexus_count == 2:
                self.ai.proper_nexus_count = 3
            if self.ai.can_afford(unit.NEXUS) and not self.ai.already_pending(unit.NEXUS):
                await self._expand_now2()
        elif nexuses.amount > 2:
            totalExcess = 0
            for location,townhall in self.ai.owned_expansions.items():
                actual = townhall.assigned_harvesters
                ideal = townhall.ideal_harvesters
                excess = actual - ideal
                totalExcess += excess
            for g in self.ai.vespene_geyser:
                actual = g.assigned_harvesters
                ideal = g.ideal_harvesters
                excess = actual - ideal
                totalExcess += excess
            totalExcess += self.ai.units(unit.PROBE).ready.idle.amount
            if totalExcess > 2 and not self.ai.already_pending(unit.NEXUS):
                self.ai.proper_nexus_count = 4
                if self.ai.can_afford(unit.NEXUS):
                    await self._expand_now2()

    async def void_rays(self):
        cyber = self.ai.structures(unit.CYBERNETICSCORE)
        if cyber.amount < 1:
            return
        nexuses = self.ai.structures(unit.NEXUS).ready
        if nexuses.amount < 2:
            self.ai.proper_nexus_count = 2
            if self.ai.can_afford(unit.NEXUS) and not self.ai.already_pending(unit.NEXUS):
                await self._expand_now2()
        elif 3 > nexuses.amount > 1 and self.ai.units(
                unit.PROBE).amount >= 34 and len(self.ai.army) > 12:
            if self.ai.proper_nexus_count == 2:
                self.ai.proper_nexus_count = 3
            if self.ai.can_afford(unit.NEXUS) and not self.ai.already_pending(unit.NEXUS):
                await self._expand_now2()
        elif nexuses.amount > 2:
            totalExcess = 0
            for location,townhall in self.ai.owned_expansions.items():
                actual = townhall.assigned_harvesters
                ideal = townhall.ideal_harvesters
                excess = actual - ideal
                totalExcess += excess
            for g in self.ai.vespene_geyser:
                actual = g.assigned_harvesters
                ideal = g.ideal_harvesters
                excess = actual - ideal
                totalExcess += excess
            totalExcess += self.ai.units(unit.PROBE).ready.idle.amount
            if totalExcess > 2 and not self.ai.already_pending(unit.NEXUS):
                self.ai.proper_nexus_count = 4
                if self.ai.can_afford(unit.NEXUS):
                    await self._expand_now2()

    async def two_bases(self):
        gates_count = self.ai.structures(unit.GATEWAY).amount
        gates_count += self.ai.structures(unit.WARPGATE).amount
        cybernetics_count = self.ai.structures(unit.CYBERNETICSCORE).amount
        if gates_count < 1 or cybernetics_count < 1:
            return
        nexuses = self.ai.structures(unit.NEXUS).ready
        if nexuses.amount < 2:
            self.ai.proper_nexus_count = 2
            if self.ai.can_afford(unit.NEXUS) and not self.ai.already_pending(unit.NEXUS):
                await self._expand_now2()
        # elif nexuses.amount < 3:
        #     if self.ai.first_attack:
        #         self.ai.proper_nexus_count = 3
        #         await self._expand_now2()

    async def none(self):
        pass


    async def _expand_now2(self):
        building = unit.NEXUS
        location = await self.ai.get_next_expansion()#await self._get_next_expansion2()
        if location is not None:
            await self.ai.build(building,near=location,max_distance=5,random_alternative=False,placement_step=1)

    async def _get_next_expansion2(self):
        closest = None
        distance = 99999

        def is_near_to_expansion(t):
            return t.position.distance_to(el) < 5

        for el in self.ai.expansion_locations:
            if any(map(is_near_to_expansion,self.ai.townhalls)):
                # already taken
                continue
            startp = self.ai.structures(unit.NEXUS).closest_to(self.ai.start_location)
            d = startp.distance_to(el)
            if d < distance:
                distance = d
                closest = el
        return closest
