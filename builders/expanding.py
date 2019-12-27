from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2


class Expanding:
    @staticmethod
    async def standard(ai):
        gates_count = ai.structures(unit.GATEWAY).amount
        gates_count += ai.structures(unit.WARPGATE).amount
        if gates_count < 1:
            return
        nexuses = ai.structures(unit.NEXUS).ready
        if nexuses.amount < 2:
            ai.proper_nexus_count = 2
            if ai.can_afford(unit.NEXUS) and not ai.already_pending(unit.NEXUS):
                await Expanding.expand_now2(ai)
        elif 3 > nexuses.amount > 1 and ai.units(
                unit.PROBE).amount >= 34 and len(ai.army) > 12:
            if ai.proper_nexus_count == 2:
                ai.proper_nexus_count = 3
            if ai.can_afford(unit.NEXUS) and not ai.already_pending(unit.NEXUS):
                await Expanding.expand_now2(ai)
        elif nexuses.amount > 2:
            totalExcess = 0
            for location,townhall in ai.owned_expansions.items():
                actual = townhall.assigned_harvesters
                ideal = townhall.ideal_harvesters
                excess = actual - ideal
                totalExcess += excess
            for g in ai.vespene_geyser:
                actual = g.assigned_harvesters
                ideal = g.ideal_harvesters
                excess = actual - ideal
                totalExcess += excess
            totalExcess += ai.units(unit.PROBE).ready.idle.amount
            if totalExcess > 2 and not ai.already_pending(unit.NEXUS):
                ai.proper_nexus_count = 4
                if ai.can_afford(unit.NEXUS):
                    await Expanding.expand_now2(ai)

    @staticmethod
    async def expand_now2(ai):
        building = unit.NEXUS
        location = await Expanding.get_next_expansion2(ai)
        if location is not None:
            await ai.build(building,near=location,max_distance=5,random_alternative=False,placement_step=1)

    @staticmethod
    async def get_next_expansion2(ai):
        closest = None
        distance = 99999

        def is_near_to_expansion(t):
            return t.position.distance_to(el) < 5

        for el in ai.expansion_locations:
            if any(map(is_near_to_expansion,ai.townhalls)):
                # already taken
                continue
            startp = ai.structures(unit.NEXUS).closest_to(ai.start_location)
            d = startp.distance_to(el)
            if d < distance:
                distance = d
                closest = el
        return closest
