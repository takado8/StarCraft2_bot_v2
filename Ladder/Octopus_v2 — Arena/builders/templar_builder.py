from sc2.ids.unit_typeid import UnitTypeId as unit


class TemplarArchivesBuilder:
    def __init__(self,ai):
        self.ai = ai

    async def none(self):
        pass

    async def standard(self):
        if self.ai.structures(unit.TWILIGHTCOUNCIL).ready.exists and not self.ai.structures(unit.TEMPLARARCHIVE).exists\
            and self.ai.can_afford(unit.TEMPLARARCHIVE) and not self.ai.already_pending(unit.TEMPLARARCHIVE):
                await self.ai.build(unit.TEMPLARARCHIVE, near=self.ai.get_proper_pylon())

    async def after_immortal(self):
        if self.ai.structures(unit.TWILIGHTCOUNCIL).ready.exists and not self.ai.structures(unit.TEMPLARARCHIVE).exists\
            and self.ai.can_afford(unit.TEMPLARARCHIVE) and not self.ai.already_pending(unit.TEMPLARARCHIVE) and\
                self.ai.army(unit.IMMORTAL).amount > 0:
                await self.ai.build(unit.TEMPLARARCHIVE, near=self.ai.get_proper_pylon())