from sc2.ids.unit_typeid import UnitTypeId as unit


class StargateBuilder:
    def __init__(self, ai):
        self.ai = ai

    async def carrier_madness(self):
        stargates = self.ai.structures(unit.STARGATE)
        beacon = self.ai.structures(unit.FLEETBEACON)
        if self.ai.vespene > 400:
            amount = 6
        elif beacon.exists:
            amount = 3
        else:
            amount = 1

        if not beacon.exists and stargates.ready.exists:
            await self.ai.build(unit.FLEETBEACON,near=self.ai.get_proper_pylon())
        elif self.ai.structures(unit.CYBERNETICSCORE).ready.exists \
                and self.ai.can_afford(unit.STARGATE) and self.ai.already_pending(unit.STARGATE) < 1 and \
                stargates.amount < amount:
            await self.ai.build(unit.STARGATE,near=self.ai.get_proper_pylon())

    async def none(self):
        pass