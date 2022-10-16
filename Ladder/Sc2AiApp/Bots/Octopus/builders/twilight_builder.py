from sc2.ids.unit_typeid import UnitTypeId as unit


class TwilightBuilder:
    def __init__(self,ai):
        self.ai = ai

    async def none(self):
        pass



    async def standard(self):
        if self.ai.structures(unit.CYBERNETICSCORE).ready.exists and self.ai.time > 220:
            if not self.ai.structures(unit.TWILIGHTCOUNCIL).exists \
                    and not self.ai.already_pending(unit.TWILIGHTCOUNCIL) and self.ai.can_afford(unit.TWILIGHTCOUNCIL):
                pylon = self.ai.get_proper_pylon()
                await self.ai.build(unit.TWILIGHTCOUNCIL,near=pylon.position,
                                 random_alternative=True,placement_step=3)

    async def early(self):
        if self.ai.structures(unit.CYBERNETICSCORE).ready.exists:
            if not self.ai.structures(unit.TWILIGHTCOUNCIL).exists \
                    and not self.ai.already_pending(unit.TWILIGHTCOUNCIL) and self.ai.can_afford(unit.TWILIGHTCOUNCIL):
                pylon = self.ai.get_proper_pylon()
                await self.ai.build(unit.TWILIGHTCOUNCIL,near=pylon.position,
                                 random_alternative=True,placement_step=3)