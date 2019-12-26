from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2


class StargateBuilder:
    @staticmethod
    async def carrier_madness(ai):
        stargates = ai.structures(unit.STARGATE)
        beacon = ai.structures(unit.FLEETBEACON)
        if ai.vespene > 400:
            amount = 6
        elif beacon.exists:
            amount = 3
        else:
            amount = 1
        if stargates.ready.idle.exists and ai.structures(unit.FLEETBEACON).ready.exists and \
                ai.can_afford(unit.CARRIER):
            ai.train(unit_type=unit.CARRIER)
        elif not beacon.exists and stargates.ready.exists:
            await ai.build(unit.FLEETBEACON,near=ai.get_proper_pylon())
        elif ai.structures(unit.CYBERNETICSCORE).ready.exists \
                and ai.can_afford(unit.STARGATE) and ai.already_pending(unit.STARGATE) < 1 and \
                stargates.amount < amount:
            await ai.build(unit.STARGATE,near=ai.get_proper_pylon())

    @staticmethod
    async def rush(ai):
        pass