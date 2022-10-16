from sc2.ids.unit_typeid import UnitTypeId as unit


class RoboticsBuilder:
    def __init__(self, ai):
        self.ai = ai


    async def none(self):
        pass

    async def macro(self):
        if self.ai.forge_upg_priority():
            return
        if self.ai.structures(unit.ROBOTICSFACILITY).amount < 1 and self.ai.can_afford(unit.ROBOTICSFACILITY)\
                and not self.ai.already_pending(unit.ROBOTICSFACILITY):
            pylon = self.ai.get_proper_pylon()
            if pylon:
                await self.ai.build(unit.ROBOTICSFACILITY,near=pylon,random_alternative=True,placement_step=2)

    async def double(self):
        if self.ai.structures(unit.CYBERNETICSCORE).ready.exists:
            if self.ai.structures(unit.ROBOTICSFACILITY).amount < 2 and self.ai.can_afford(unit.ROBOTICSFACILITY)\
                    and not self.ai.already_pending(unit.ROBOTICSFACILITY):
                pylon = self.ai.get_proper_pylon()
                if pylon:
                    await self.ai.build(unit.ROBOTICSFACILITY,near=pylon,random_alternative=True,placement_step=3)