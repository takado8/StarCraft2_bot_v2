from sc2.ids.unit_typeid import UnitTypeId as unit


class ForgeBuilder:
    def __init__(self, ai):
        self.ai = ai

    async def none(self):
        pass

    async def double(self):
        if self.ai.time > 160:
            if self.ai.structures(unit.FORGE).amount < 1 and not self.ai.already_pending(unit.FORGE) and self.ai.can_afford(
                    unit.FORGE):
                if self.ai.structures(unit.PYLON).ready.exists:
                    placement = self.ai.get_proper_pylon()
                    if placement:
                        await self.ai.build(unit.FORGE,near=placement,placement_step=3)
            elif self.ai.structures(unit.FORGE).ready.exists:
                if self.ai.time > 480 and self.ai.structures(unit.FORGE).amount < 2 and not self.ai.already_pending(
                        unit.FORGE) and self.ai.can_afford(unit.FORGE):
                    placement = self.ai.get_proper_pylon()
                    if placement:
                        await self.ai.build(unit.FORGE,near=placement,placement_step=3)

    async def single(self):
        if self.ai.time > 160:
            if self.ai.structures(unit.FORGE).amount < 1 and not self.ai.already_pending(
                    unit.FORGE) and self.ai.can_afford(
                    unit.FORGE):
                if self.ai.structures(unit.PYLON).ready.exists:
                    placement = self.ai.get_proper_pylon()
                    if placement:
                        await self.ai.build(unit.FORGE,near=placement,placement_step=3)

    async def double_late(self):
        if self.ai.time > 160:
            if self.ai.time > 600:
                am = 2
            else:
                am = 1
            if self.ai.structures(unit.FORGE).amount < am and not self.ai.already_pending(unit.FORGE):
                if self.ai.structures(unit.PYLON).ready.exists:
                    placement = self.ai.get_proper_pylon()
                    if placement:
                        await self.ai.build(unit.FORGE,near=placement,placement_step=3)