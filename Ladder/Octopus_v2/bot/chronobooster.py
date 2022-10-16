from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.buff_id import BuffId as buff
from sc2.units import Units
import random


class Chronobooster:
    def __init__(self,ai):
        self.ai = ai
        self.standard_chrono_queue = [unit.NEXUS, unit.GATEWAY, unit.STARGATE, unit.ROBOTICSFACILITY, unit.CYBERNETICSCORE]
        self.stalker_proxy_chrono_queue = [unit.NEXUS, unit.CYBERNETICSCORE]


    async def air(self):
        pass


    async def standard(self):
        if self.ai.structures(unit.NEXUS).exists and self.ai.structures(unit.PYLON).ready.exists:
            nexuses = self.ai.structures().filter(lambda x: x.type_id == unit.NEXUS and x.is_ready and x.energy >= 50)
            i = 0
            for nexus in nexuses:
                # targets = None
                targets_filtered = Units([],self)
                while targets_filtered.amount < 1 and i < len(self.standard_chrono_queue):
                    targets = self.ai.structures().filter(lambda x: x.type_id == self.standard_chrono_queue[i] and x.is_ready and
                                                not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                    for tg in targets:
                        if tg.orders:
                            progress = tg.orders[0].progress
                            abil_id = tg.orders[0].ability.id
                            if abil_id == ability.STARGATETRAIN_CARRIER:
                                time = 64
                            elif abil_id == ability.STARGATETRAIN_TEMPEST:
                                time = 43
                            elif abil_id == ability.RESEARCH_WARPGATE:
                                time = 150
                            else:
                                time = 31

                            time_left = time * (1 - progress)
                            # print('time left: ' + str(round(time_left,1)) + '  for unit ' + str(abil_id)[10:])
                            if time_left < 30:
                                # print('skipping')
                                targets.remove(tg)
                            else:
                                # print('allowing cast on ' + str(tg.type_id) + ' for unit ' + str(abil_id)[10:] +
                                #       ' with time left: ' + str(time_left))
                                targets_filtered.append(tg)
                        else:
                            targets.remove(tg)
                    if targets_filtered.amount < 1:
                        i += 1
                if targets_filtered:
                    target = targets_filtered.random
                    if target.type_id in [unit.NEXUS, unit.GATEWAY]:
                        self.standard_chrono_queue.remove(target.type_id)
                    self.ai.do(nexus(ability.EFFECT_CHRONOBOOSTENERGYCOST,target))
                    return
                else:
                    warpgates = self.ai.structures(unit.WARPGATE).ready
                    targets = []
                    for warpgate in warpgates:
                        abilities = await self.ai.get_available_abilities(warpgate)
                        if ability.WARPGATETRAIN_STALKER in abilities:
                            targets.append(warpgate)
                    if targets:
                        target = random.choice(targets)
                        self.ai.do(nexus(ability.EFFECT_CHRONOBOOSTENERGYCOST,target))
                        return

    async def stalker_proxy(self):
        if self.ai.structures(unit.NEXUS).exists and self.ai.structures(unit.PYLON).ready.exists:
            nexuses = self.ai.structures().filter(lambda x: x.type_id == unit.NEXUS and x.is_ready and x.energy >= 50)
            i = 0
            for nexus in nexuses:
                # targets = None
                targets_filtered = Units([],self)
                while targets_filtered.amount < 1 and i < len(self.stalker_proxy_chrono_queue):
                    targets = self.ai.structures().filter(lambda x: x.type_id == self.stalker_proxy_chrono_queue[i] and x.is_ready and
                                                not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                    for tg in targets:
                        if tg.orders:
                            progress = tg.orders[0].progress
                            abil_id = tg.orders[0].ability.id
                            if abil_id == ability.STARGATETRAIN_CARRIER:
                                time = 64
                            elif abil_id == ability.STARGATETRAIN_TEMPEST:
                                time = 43
                            elif abil_id == ability.RESEARCH_WARPGATE:
                                time = 110
                            else:
                                time = 31

                            time_left = time * (1 - progress)
                            # print('time left: ' + str(round(time_left,1)) + '  for unit ' + str(abil_id)[10:])
                            if time_left < 30:
                                # print('skipping')
                                targets.remove(tg)
                            else:
                                # print('allowing cast on ' + str(tg.type_id) + ' for unit ' + str(abil_id)[10:] +
                                #       ' with time left: ' + str(time_left))
                                targets_filtered.append(tg)
                        else:
                            targets.remove(tg)
                    if targets_filtered.amount < 1:
                        i += 1
                if targets_filtered:
                    target = targets_filtered.random
                    if target.type_id in [unit.NEXUS, unit.GATEWAY]:
                        self.stalker_proxy_chrono_queue.remove(target.type_id)
                    self.ai.do(nexus(ability.EFFECT_CHRONOBOOSTENERGYCOST,target))
                    return
                else:
                    warpgates = self.ai.structures(unit.WARPGATE).ready
                    targets = []
                    for warpgate in warpgates:
                        abilities = await self.ai.get_available_abilities(warpgate)
                        if ability.WARPGATETRAIN_STALKER in abilities:
                            targets.append(warpgate)
                    if targets:
                        target = random.choice(targets)
                        self.ai.do(nexus(ability.EFFECT_CHRONOBOOSTENERGYCOST,target))
                        return
