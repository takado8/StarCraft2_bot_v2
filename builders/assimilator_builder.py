from sc2.ids.unit_typeid import UnitTypeId as unit


class AssimilatorBuilder:
    @staticmethod
    def max_vespene(ai):
        if not ai.can_afford(unit.ASSIMILATOR) or ai.structures(unit.NEXUS).amount > 2 \
                and ai.vespene > ai.minerals:
            return
        for nexus in ai.structures(unit.NEXUS).ready:
            vaspenes = ai.vespene_geyser.closer_than(10, nexus)
            for vaspene in vaspenes:
                worker = ai.select_build_worker(vaspene.position)
                if worker is None:
                    break
                if not ai.already_pending(unit.ASSIMILATOR) and not ai.structures(unit.ASSIMILATOR).exists or \
                        (not ai.structures(unit.ASSIMILATOR).closer_than(5, vaspene).exists):
                    ai.do(worker.build(unit.ASSIMILATOR, vaspene))

    @staticmethod
    def rush(ai):
        pass