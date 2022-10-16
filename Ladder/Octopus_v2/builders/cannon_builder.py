from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2 import BotAI


class CannonBuilder:
    def __init__(self, ai: BotAI):
        self.ai = ai

    async def double_per_nex(self):
        if self.ai.structures(unit.FORGE).ready.exists and self.ai.minerals > 150:
            for nex in self.ai.structures(unit.NEXUS).ready:
                cannons =self.ai.structures(unit.PHOTONCANNON)
                if cannons.amount < 2 or cannons.closer_than(11, nex).amount < 2:
                    spot = self.ai.mineral_field.closer_than(11,nex).center.towards(nex,-3)
                    pylon = self.ai.structures(unit.PYLON).ready.closer_than(5, spot)
                    if not pylon.exists and not self.ai.already_pending(unit.PYLON):
                        await self.ai.build(unit.PYLON,spot)
                    elif not self.ai.already_pending(unit.PHOTONCANNON):
                        await self.ai.build(unit.PHOTONCANNON, spot)
