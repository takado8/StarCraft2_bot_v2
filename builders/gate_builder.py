from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.player import Bot, Computer
from sc2.units import Units
from sc2.ids.buff_id import BuffId as buff
from sc2.ids.upgrade_id import UpgradeId as upgrade
from sc2.position import Point2


class GateBuilder:
    @staticmethod
    async def carrier_madness(ai):
        gates_count = ai.structures(unit.GATEWAY).amount
        gates_count += ai.structures(unit.WARPGATE).amount
        if ai.structures(unit.NEXUS).amount < 2:
            gc = 1
        else:
            gc = 2
        if gates_count < gc \
                and ai.can_afford(unit.GATEWAY) and ai.structures(unit.PYLON).ready.exists and \
                ai.already_pending(unit.GATEWAY) < 2:
            if gates_count < 1:
                pylon = Point2(ai.coords['gate1'])
            else:
                pylon = Point2(ai.coords['gate2'])
            if pylon is None:
                return
            await ai.build(unit.GATEWAY,near=pylon,placement_step=0,max_distance=0,random_alternative=False)