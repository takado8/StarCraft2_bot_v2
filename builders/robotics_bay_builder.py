from sc2.ids.unit_typeid import UnitTypeId as unit


class RoboticsBayBuilder:
    def __init__(self, ai):
        self.ai = ai

    async def standard(self):
        if not self.ai.structures(unit.ROBOTICSBAY).exists and\
                self.ai.structures(unit.ROBOTICSFACILITY).ready.exists and self.ai.can_afford(unit.ROBOTICSBAY) and not\
                self.ai.already_pending(unit.ROBOTICSBAY):
            await self.ai.build(unit.ROBOTICSBAY, near=self.ai.get_proper_pylon(), placement_step=3)

    async def none(self):
        pass