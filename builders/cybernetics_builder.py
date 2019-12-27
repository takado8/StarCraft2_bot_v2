from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2


class CyberneticsBuilder:
    @staticmethod
    async def standard(ai):
        if ai.structures(unit.CYBERNETICSCORE).amount < 1 and not ai.already_pending(unit.CYBERNETICSCORE) and \
                ai.structures(unit.GATEWAY).ready.exists and ai.can_afford(unit.CYBERNETICSCORE):
            cybernetics_position = Point2(ai.coords['cybernetics'])
            if cybernetics_position:
                await ai.build(unit.CYBERNETICSCORE, near=cybernetics_position, placement_step=0,
                                 random_alternative=False, max_distance=0)