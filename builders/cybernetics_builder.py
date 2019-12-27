from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2


class CyberneticsBuilder:
    def __init__(self, ai):
        self.ai = ai

    async def lower_wall(self):
        if self.ai.structures(unit.CYBERNETICSCORE).amount < 1 and not self.ai.already_pending(unit.CYBERNETICSCORE) and \
                self.ai.structures(unit.GATEWAY).ready.exists and self.ai.can_afford(unit.CYBERNETICSCORE):
            cybernetics_position = Point2(self.ai.coords['cybernetics'])
            if cybernetics_position:
                await self.ai.build(unit.CYBERNETICSCORE, near=cybernetics_position, placement_step=0,
                                 random_alternative=False, max_distance=0)