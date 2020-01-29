from sc2 import UnitTypeId as unit


class DarkShrineBuilder:
    def __init__(self,ai):
        self.ai = ai

    async def none(self):
        pass

    async def standard(self):
        if self.ai.structures(unit.TWILIGHTCOUNCIL).ready.exists:
            if not self.ai.structures(unit.DARKSHRINE).exists \
                    and not self.ai.already_pending(unit.DARKSHRINE):
                pylon = self.ai.get_proper_pylon()
                await self.ai.build(unit.DARKSHRINE,near=pylon.position,
                                    random_alternative=True,placement_step=3)