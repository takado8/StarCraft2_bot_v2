from sc2.ids.unit_typeid import UnitTypeId as unit


class StargateBuilder:
    def __init__(self, ai):
        self.ai = ai

    async def carrier_madness(self):
        stargates = self.ai.structures(unit.STARGATE)
        beacon = self.ai.structures(unit.FLEETBEACON)
        if stargates.idle.exists and beacon.exists:
            return
        if self.ai.vespene > 450:
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

    async def proxy(self):
        pylons = self.ai.structures(unit.PYLON).ready
        if pylons.exists and self.ai.structures(unit.CYBERNETICSCORE).ready.exists:
            pylon = pylons.further_than(40, self.ai.start_location.position)
            if pylon.exists:
                pylon = pylon.furthest_to(self.ai.start_location.position)
                stargates = self.ai.structures(unit.STARGATE)

                if not stargates.idle.exists and self.ai.can_afford(unit.STARGATE) and not\
                        self.ai.already_pending(unit.STARGATE) and (self.ai.vespene > 250 or not
                        stargates.exists):
                    worker = self.ai.units(unit.PROBE).closest_to(pylon)
                    await self.ai.build(unit.STARGATE, near=pylon, build_worker=worker)
                    self.ai.do(worker.hold_position(queue=True))

    async def none(self):
        pass