from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.buff_id import BuffId as buff


class Chronobooster:
    def __init__(self,ai):
        self.ai = ai
        self.first_chrono_casted = False
        self.standard_chrono_queue = [unit.NEXUS, unit.STARGATE, unit.ROBOTICSFACILITY]


    async def air(self):
        pass


    async def standard(self):
        if self.ai.structures(unit.NEXUS).exists and self.ai.structures(unit.PYLON).ready.exists:
            nexuses = self.ai.structures().filter(lambda x: x.type_id == unit.NEXUS and x.is_ready and x.energy >= 50)
            i = 0
            for nexus in nexuses:
                targets = None
                while not targets and i < len(self.standard_chrono_queue):
                    targets = self.ai.structures().filter(lambda x: x.type_id == self.standard_chrono_queue[i] and x.is_ready and
                                                not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                    if not targets:
                        i += 1
                if targets:
                    target = targets.random
                    if not self.first_chrono_casted:
                        self.first_chrono_casted = True
                        self.standard_chrono_queue.remove(unit.NEXUS)
                    self.ai.do(nexus(ability.EFFECT_CHRONOBOOSTENERGYCOST,target))