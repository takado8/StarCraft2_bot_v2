from sc2.ids.unit_typeid import UnitTypeId as unit


class AssimilatorBuilder:
    def __init__(self, ai):
        self.ai = ai

    def max_vespene(self):
        if self.ai.can_afford(unit.ASSIMILATOR) and self.ai.structures(unit.PYLON).exists:

            for nexus in self.ai.structures(unit.NEXUS):
                vaspenes = self.ai.vespene_geyser.closer_than(12, nexus)
                for vaspene in vaspenes:
                    if not self.ai.structures(unit.ASSIMILATOR).exists or not self.ai.structures(unit.ASSIMILATOR).closer_than(5, vaspene).exists:
                        if not self.ai.already_pending(unit.ASSIMILATOR):
                            worker = self.ai.select_build_worker(vaspene.position)
                            if worker is None:
                                break
                            self.ai.do(worker.build(unit.ASSIMILATOR, vaspene))

    def more_vespene(self):
        if self.ai.structures(unit.GATEWAY).exists or self.ai.structures(unit.WARPGATE).exists:
            if not self.ai.can_afford(unit.ASSIMILATOR) or self.ai.structures(unit.NEXUS).amount > 1 \
                    and self.ai.vespene > self.ai.minerals/2:
                return
            for nexus in self.ai.structures(unit.NEXUS).ready:
                vaspenes = self.ai.vespene_geyser.closer_than(10,nexus)
                for vaspene in vaspenes:
                    worker = self.ai.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if not self.ai.already_pending(unit.ASSIMILATOR) or not self.ai.structures(unit.ASSIMILATOR).exists or \
                            (self.ai.time > 100 and not self.ai.structures(unit.ASSIMILATOR).closer_than(5,vaspene).exists):
                        self.ai.do(worker.build(unit.ASSIMILATOR,vaspene))
                        break

    def standard(self):
        if self.ai.structures(unit.GATEWAY).exists or self.ai.structures(unit.WARPGATE).exists and not self.ai.already_pending(unit.ASSIMILATOR):

            if not self.ai.can_afford(unit.ASSIMILATOR) or self.ai.time < 250 and \
                    self.ai.structures(unit.ASSIMILATOR).amount > 1 or self.ai.structures(unit.NEXUS).amount > 1 \
                    and self.ai.vespene > self.ai.minerals:
                return
            for nexus in self.ai.structures(unit.NEXUS).ready:
                vaspenes = self.ai.vespene_geyser.closer_than(10,nexus)
                for vaspene in vaspenes:
                    worker = self.ai.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if (not self.ai.structures(
                            unit.ASSIMILATOR).exists) or \
                            (self.ai.time > 120 and not self.ai.structures(unit.ASSIMILATOR).closer_than(5,
                                                                                                         vaspene).exists):
                        self.ai.do(worker.build(unit.ASSIMILATOR,vaspene))
                        break