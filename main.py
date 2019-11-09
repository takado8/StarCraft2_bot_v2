import itertools
import random
from sc2 import run_game,maps,Race,Difficulty,Result
import sc2
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.player import Bot,Computer,Human
from sc2.ids.buff_id import BuffId as buff
from sc2.ids.upgrade_id import UpgradeId as upgrade

class Octopus(sc2.BotAI):

    def __init__(self):
        pass

    async def on_step(self, iteration):
        await self.nexus_buff()
        await self.first_pylon()
        await self.build_pylons()
        await self.distribute_workers()
        await self.build_gate()
        self.train_army()
        self.train_workers()
        self.build_assimilators()
        await self.morph_gates()
        await self.warp_new_units()
        await self.cybernetics_core_build()
        self.cybernetics_core_upgrades()

    async def start_step(self):
        pass

    def train_army(self):
        if self.minerals < 100:
            return
        if self.can_afford(unit.STALKER) and self.structures(unit.CYBERNETICSCORE).ready.exists:
            u = unit.STALKER
        elif self.minerals > 150 and self.supply_left > 1:
            u = unit.ZEALOT
        else:
            return
        for gateway in self.structures(unit.GATEWAY).ready.idle:
            self.do(gateway.train(u))

    async def build_gate(self):
        gates_count = self.structures(unit.GATEWAY).amount
        gates_count += self.structures(unit.WARPGATE).amount

        if gates_count < 4 and self.can_afford(unit.GATEWAY) and \
                self.already_pending(unit.GATEWAY) < 1:
            pylon = self.get_proper_pylon()
            if pylon is None:
                print("Cannot find proper pylon for gateway")
                return
            await self.build(unit.GATEWAY, near=pylon, placement_step=2)

    async def first_pylon(self):
        if self.structures(unit.PYLON).amount < 1 and self.can_afford(unit.PYLON):
            await self.build(unit.PYLON, self.start_location.position.towards(self.game_info.map_center, 5))

    async def build_pylons(self):
        if self.structures(unit.PYLON).exists:
            if self.time < 240:
                pending = 1
                left = 5
            else:
                pending = 2
                left = 8
            if self.supply_left < left and self.supply_cap < 200 or self.structures(unit.PYLON).amount < 2:
                if self.can_afford(unit.PYLON) and self.already_pending(unit.PYLON) < pending:
                    max_dist = 18
                    pl_step = 6
                    if self.time < 180:
                        placement = await self.find_placement(unit.PYLON, near=self.start_location.position,
                                                              max_distance=18,
                                                              placement_step=6)
                        if self.structures(unit.PYLON).closest_to(self.main_base_ramp.top_center).distance_to(placement) < 6:
                            return
                    elif self.supply_cap < 100:
                        placement = self.start_location.position
                    else:
                        placement = self.start_location.position
                        max_dist = 40
                        pl_step = 3
                    await self.build(unit.PYLON, near=placement, max_distance=max_dist, placement_step=pl_step)

    def train_workers(self):
        workers = self.workers.amount
        nex = self.structures(unit.NEXUS).ready.amount
        if workers < 20 * nex and workers < 55:
            for nexus in self.structures(unit.NEXUS).ready:
                if nexus.is_idle and self.can_afford(unit.PROBE):
                    self.do(nexus.train(unit.PROBE))
        elif 54 < workers < 63:
            if self.can_afford(unit.PROBE) and not self.already_pending(unit.PROBE):
                if self.structures(unit.NEXUS).noqueue.amount < nex:
                    return
                nexus = self.structures(unit.NEXUS).ready.noqueue.random
                self.do(nexus.train(unit.PROBE))

    def build_assimilators(self):
        if self.structures(unit.GATEWAY).ready.exists or self.structures(unit.WARPGATE).exists:
            if not self.can_afford(unit.ASSIMILATOR):
                return
            for nexus in self.structures(unit.NEXUS).ready:
                vaspenes = self.vespene_geyser.closer_than(10.0,nexus)
                for vaspene in vaspenes:

                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break

                    if not self.structures(unit.ASSIMILATOR).exists or (not
                            self.structures(unit.ASSIMILATOR).closer_than(1.0,vaspene).exists and self.time > 180):
                        self.do(worker.build(unit.ASSIMILATOR,vaspene))
                        return

    def get_proper_pylon(self):
        properPylons = self.structures().filter(lambda unit_: unit_.type_id == unit.PYLON and unit_.is_ready)
        if properPylons.exists:
            min_neighbours = 99
            pylon = properPylons.random
            for pyl in properPylons:
                neighbours = self.structures().filter(lambda unit_: unit_.distance_to(pyl) < 6).amount
                if neighbours < min_neighbours:
                    min_neighbours = neighbours
                    pylon = pyl
            return pylon
        else:
            return None

    async def morph_gates(self):
        for gateway in self.structures(unit.GATEWAY).ready:
            abilities = await self.get_available_abilities(gateway)
            if ability.MORPH_WARPGATE in abilities and self.can_afford(ability.MORPH_WARPGATE):
                self.do(gateway(ability.MORPH_WARPGATE))

    async def warp_new_units(self):
        for warpgate in self.structures(unit.WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            # all the units have the same cooldown anyway so let's just look at ZEALOT
            if ability.WARPGATETRAIN_ZEALOT in abilities:

                furthest_pylon = self.structures(unit.PYLON).furthest_to(self.start_location.position)
                pos = furthest_pylon.position.to2.random_on_distance(4)

                if self.can_afford(unit.STALKER) and self.supply_left > 1 and self.units(unit.STALKER).amount < 40:
                    placement = await self.find_placement(ability.WARPGATETRAIN_STALKER,pos,placement_step=1)
                    if placement is None:
                        print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.STALKER,placement))
                elif self.can_afford(unit.ADEPT) and self.supply_left > 1 and \
                        self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(unit.ADEPT).amount < 10:
                    placement = await self.find_placement(ability.TRAINWARP_ADEPT,pos,placement_step=1)
                    if placement is None:
                        print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.ADEPT,placement))

                elif self.vespene < 100 and self.minerals > 400 and self.can_afford(unit.ZEALOT) and \
                        self.supply_left > 10 and self.units(unit.ZEALOT).amount < 6:
                    placement = await self.find_placement(ability.WARPGATETRAIN_ZEALOT,pos,placement_step=1)
                    if placement is None:
                        print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.ZEALOT,placement))

    async def nexus_buff(self):
        if not self.structures(unit.NEXUS).exists:
            return
        # sec_nexus = self.structures(unit.NEXUS).closest_to(
        #     self.main_base_ramp.top_center.towards(self.main_base_ramp.bottom_center,7))
        for nexus in self.structures(unit.NEXUS).ready:
            # if nexus.tag == sec_nexus.tag and self.time > 480 and nexus.energy < 100:
            #     return  # spare 50 energy for strategic recall
            abilities = await self.get_available_abilities(nexus)
            if ability.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                target = self.structures().filter(lambda x: x.type_id == unit.CYBERNETICSCORE
                                                       and x.is_ready and not x.noqueue and not x.has_buff(
                    buff.CHRONOBOOSTENERGYCOST))
                if target.exists:
                    target = target.random
                else:
                    target = self.structures().filter(lambda x: x.type_id == unit.NEXUS and x.is_ready
                                    and not x.noqueue and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                    if target.exists:
                        target = target.random
                    else:
                        target = self.structures().filter(lambda x: (x.type_id == unit.GATEWAY or x.type_id == unit.WARPGATE)
                                                               and x.is_ready and not x.noqueue and not x.has_buff(
                            buff.CHRONOBOOSTENERGYCOST))
                        if target.exists:
                            target = target.random
                if target:
                    self.do(nexus(ability.EFFECT_CHRONOBOOSTENERGYCOST,target))

    async def cybernetics_core_build(self):
        if self.structures(unit.CYBERNETICSCORE).amount < 1 and not self.already_pending(unit.CYBERNETICSCORE) and \
                self.structures(unit.GATEWAY).ready.exists and self.can_afford(unit.CYBERNETICSCORE):

            cybernetics_position = self.get_proper_pylon()
            if cybernetics_position:
                await self.build(unit.CYBERNETICSCORE, near=cybernetics_position, placement_step=3)

    def cybernetics_core_upgrades(self):
        if self.structures(unit.CYBERNETICSCORE).ready.idle.amount > 0:
            if upgrade.WARPGATERESEARCH not in self.state.upgrades and not self.already_pending_upgrade(
                    upgrade.WARPGATERESEARCH) and self.can_afford(upgrade.WARPGATERESEARCH):
                self.do(self.structures(unit.CYBERNETICSCORE).ready.idle.random.research(upgrade.WARPGATERESEARCH))


def botVsComputer():
    maps_set = ["CrystalCavern","Bandwidth","Reminiscence","TheTimelessVoid","PrimusQ9","Ephemeron",
                "Sanglune","Urzagol"]
    training_maps = ["DefeatZealotswithBlink","ParaSiteTraining"]
    races = [sc2.Race.Protoss, sc2.Race.Zerg, sc2.Race.Terran]
    map_index = random.randint(0,6)
    race_index = random.randint(0,2)
    run_game(map_settings=maps.get(maps_set[4]),players=[
        Bot(race=Race.Protoss,ai=Octopus(),name='Octopus'),
        Computer(race=races[0],difficulty=Difficulty.Easy)
    ],realtime=True)



botVsComputer()