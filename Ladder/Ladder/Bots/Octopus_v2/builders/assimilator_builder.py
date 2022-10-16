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
        if self.ai.structures().filter(lambda x: x.type_id in [unit.GATEWAY, unit.WARPGATE]).amount == 0 or\
                (self.ai.structures(unit.NEXUS).ready.amount > 1 and self.ai.vespene > self.ai.minerals):
            return
        nexuses = self.ai.structures(unit.NEXUS)
        if nexuses.amount < 4:
            nexuses = nexuses.ready
        probes = self.ai.units(unit.PROBE)
        if probes.exists:
            for nexus in nexuses:
                vespenes = self.ai.vespene_geyser.closer_than(9,nexus)
                workers = probes.closer_than(12, nexus)
                if workers.amount > 14 or nexuses.amount > 3:
                    for vespene in vespenes:
                        if (not self.ai.already_pending(unit.ASSIMILATOR)) and (not
                        self.ai.structures(unit.ASSIMILATOR).exists or not
                        self.ai.structures(unit.ASSIMILATOR).closer_than(3, vespene).exists):
                            if not self.ai.can_afford(unit.ASSIMILATOR):
                                return
                            worker = self.ai.select_build_worker(vespene.position)
                            if worker is None:
                                break
                            self.ai.do(worker.build(unit.ASSIMILATOR,vespene))
                            self.ai.do(worker.move(worker.position.random_on_distance(1), queue=True))

    def standard(self):
        if not self.ai.already_pending(unit.ASSIMILATOR) and (self.ai.structures(unit.GATEWAY).exists or self.ai.structures(unit.WARPGATE).exists):

            if self.ai.time < 250 and \
                    self.ai.structures(unit.ASSIMILATOR).amount > 1 or self.ai.structures(unit.NEXUS).amount > 1 \
                    and self.ai.vespene > self.ai.minerals:
                return
            for nexus in self.ai.structures(unit.NEXUS):
                vaspenes = self.ai.vespene_geyser.closer_than(10,nexus)
                for vaspene in vaspenes:
                    worker = self.ai.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if (not self.ai.structures(unit.ASSIMILATOR).exists) or \
                            (self.ai.time > 120 and not self.ai.structures(unit.ASSIMILATOR).closer_than(5,
                                                                                                         vaspene).exists):
                        if not self.ai.can_afford(unit.ASSIMILATOR):
                            return
                        self.ai.do(worker.build(unit.ASSIMILATOR,vaspene))
                        self.ai.do(worker.move(worker.position.towards(self.ai.n, 1),queue=True))
                        return