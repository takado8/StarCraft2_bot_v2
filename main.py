import math
import random
from sc2 import run_game, maps, Race, Difficulty, Result, AIBuild
import sc2
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.player import Bot, Computer
from sc2.units import Units
from sc2.ids.buff_id import BuffId as buff
from sc2.ids.upgrade_id import UpgradeId as upgrade
from visual import Visual
from sc2.position import Point2
import numpy as np
import cv2


class Octopus(sc2.BotAI):
    build_order = {
        'rush': {unit.GATEWAY: [0,0,90,120], unit.CYBERNETICSCORE: [0]},
        'macro': {'gate': [30], 'cybernetics': [0], 'robotics': [0]}
        }

    enemy_attack = False
    second_ramp = None
    builds = ['rush', 'macro']
    build_type = 'macro'
    enemy_main_base_down = False
    first_attack = False
    attack = False
    army_ids = [unit.ADEPT, unit.STALKER, unit.ZEALOT, unit.SENTRY, unit.OBSERVER, unit.IMMORTAL, unit.ARCHON,
                unit.HIGHTEMPLAR, unit.DISRUPTOR, unit.WARPPRISM]
    units_to_ignore = [unit.LARVA, unit.EGG]
    workers_ids = [unit.SCV, unit.PROBE, unit.DRONE]
    proper_nexus_count = 1
    army = []
    known_enemies = []
    game_map = None
    leader = None
    defend_position = None


    async def on_unit_destroyed(self, unit_tag):
        try:
            if unit_tag in self.known_enemies:
                # print('known unit died!')
                self.known_enemies.remove(unit_tag)
        except:
            pass

    async def on_start(self):
        self.second_ramp = self.find_2nd_ramp()

    async def on_step(self, iteration):
        for enemy in self.enemy_units():
            if enemy.tag not in self.known_enemies:
                # print('new enemy!')
                self.known_enemies.append(enemy.tag)

        self.army = self.units().filter(lambda x: x.type_id in self.army_ids)
        self.leader = self.select_leader()
        await self.ramp_wall_build()
        await self.nexus_buff()
        await self.first_pylon()
        await self.build_pylons()
        # await self.robotics_facility()
        await self.distribute_workers()
        await self.expand()
        await self.make_forge()
        self.train_workers()
        await self.twilight_council_build()
        # counter attack
        if self.enemy_units().exists and self.enemy_units().closer_than(20, self.defend_position).amount > 5:
            self.enemy_attack = True
        if self.enemy_attack and self.enemy_units().exists and self.enemy_units().closer_than(20, self.defend_position).amount < 4:
            self.enemy_attack = False
            self.attack = True
        if self.structures(unit.NEXUS).amount >= self.proper_nexus_count or self.already_pending(unit.NEXUS) or self.minerals > 400:
            # print('nex amount = ' + str(self.structures(unit.NEXUS).amount))
            # print('proper amount = ' + str(self.proper_nexus_count))
            await self.build_gate()
            self.train_army()
            await self.warp_new_units()
            await self.cybernetics_core_build()
            self.cybernetics_core_upgrades()
            self.build_assimilators()
        await self.morph_gates()

        if self.build_type == 'rush' and self.army.amount > 6 and not self.first_attack:
            self.first_attack = True
            self.attack = True
        if self.build_type == 'rush' and self.army.amount > 2 or self.attack:
            await self.proxy()
        if self.attack and self.army.amount < (5 if self.build_type == 'rush' else 16):
            self.attack = False

        if self.attack:
            await self.attack_formation()
        else:
            await self.defend()
        await self.micro_units()

    async def start_step(self):
        pass

    def make_build_order(self):
        order = self.build_order[self.build_type]
        for building in order:
            if self.can_afford(building) and self.tech_requirement_progress(building) == 1 and\
                self.structures(building).amount < len(order[building]):
                pass

    async def make_forge(self):
        if self.time < 180:
            return
        if self.structures(unit.FORGE).amount < 1 and not self.already_pending(unit.FORGE) and self.can_afford(unit.FORGE):
            if self.structures(unit.PYLON).ready.exists:
                placement = self.get_proper_pylon()
                if placement:
                    await self.build(unit.FORGE,near=placement,placement_step=2)
        elif self.structures(unit.FORGE).ready.exists:
            if self.time > 240 and self.structures(unit.FORGE).amount < 2 and not self.already_pending(
                    unit.FORGE) and self.can_afford(unit.FORGE):
                placement = self.get_proper_pylon()
                if placement:
                    await self.build(unit.FORGE,near=placement,placement_step=2)
            for forge in self.structures(unit.FORGE).ready.idle:
                if upgrade.PROTOSSGROUNDARMORSLEVEL1 not in self.state.upgrades and not self.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDARMORSLEVEL1) and self.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL1):
                    self.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL1))
                elif upgrade.PROTOSSGROUNDWEAPONSLEVEL1 not in self.state.upgrades and not self.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDWEAPONSLEVEL1) and self.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL1):
                    self.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL1))
                elif upgrade.PROTOSSSHIELDSLEVEL1 not in self.state.upgrades and not self.already_pending_upgrade(
                        upgrade.PROTOSSSHIELDSLEVEL1) and self.can_afford(upgrade.PROTOSSSHIELDSLEVEL1):
                    self.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL1))
                elif upgrade.PROTOSSGROUNDARMORSLEVEL2 not in self.state.upgrades and not self.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDARMORSLEVEL2) and self.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL2):
                    self.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL2))
                elif upgrade.PROTOSSGROUNDWEAPONSLEVEL2 not in self.state.upgrades and not self.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDWEAPONSLEVEL2) and self.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL2):
                    self.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL2))
                elif upgrade.PROTOSSGROUNDWEAPONSLEVEL2 in \
                        self.state.upgrades and not self.already_pending_upgrade(
                    upgrade.PROTOSSGROUNDWEAPONSLEVEL3) and self.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL3):
                    self.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL3))
                elif upgrade.PROTOSSGROUNDARMORSLEVEL2 in \
                        self.state.upgrades and not self.already_pending_upgrade(
                    upgrade.PROTOSSGROUNDARMORSLEVEL3) and self.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL3):
                    self.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL3))
                elif upgrade.PROTOSSSHIELDSLEVEL2 not in self.state.upgrades and not self.already_pending_upgrade(
                        upgrade.PROTOSSSHIELDSLEVEL2) and self.can_afford(upgrade.PROTOSSSHIELDSLEVEL2) and \
                        upgrade.PROTOSSSHIELDSLEVEL1 in self.state.upgrades and self.units(
                    unit.TWILIGHTCOUNCIL).ready.exists:
                    self.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL2))
                elif upgrade.PROTOSSSHIELDSLEVEL3 not in self.state.upgrades and not self.already_pending_upgrade(
                        upgrade.PROTOSSSHIELDSLEVEL3) and self.can_afford(upgrade.PROTOSSSHIELDSLEVEL3) and \
                        upgrade.PROTOSSSHIELDSLEVEL2 in self.state.upgrades:
                    self.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL3))

    async def robotics_facility(self):
        if self.structures(unit.ROBOTICSFACILITY).amount < 1 and self.can_afford(unit.ROBOTICSFACILITY)\
                and not self.already_pending(unit.ROBOTICSFACILITY) and self.time > 230:
            pylon = self.get_proper_pylon()
            if pylon:
                await self.build(unit.ROBOTICSFACILITY,near=pylon,random_alternative=True,placement_step=2)
        elif self.structures(unit.ROBOTICSFACILITY).ready.exists and \
                self.units(unit.OBSERVER).amount + self.units(unit.OBSERVERSIEGEMODE).amount < 1 and \
                self.can_afford(unit.OBSERVER) and self.supply_left > 0:
            for factory in self.structures(unit.ROBOTICSFACILITY).ready.idle:
                self.do(factory.train(unit.OBSERVER))
                break
        # elif (self.time > 600 and self.units(unit.ROBOTICSFACILITY).amount < 2 and self.can_afford(
        #         unit.ROBOTICSFACILITY)
        #       and not self.already_pending(unit.ROBOTICSFACILITY)):
        #     pylon = self.get_proper_pylon()
        #     if pylon:
        #         await self.build(unit.ROBOTICSFACILITY,near=pylon,random_alternative=True,placement_step=2)
        # elif self.time > 500 and self.units(unit.WARPPRISMPHASING).amount + self.units(unit.WARPPRISM).amount < 1 \
        #         and self.can_afford(unit.WARPPRISM) and not self.already_pending(
        #     unit.WARPPRISM) and self.supply_left > 2:
        #     for factory in self.structures(unit.ROBOTICSFACILITY).ready.idle:
        #         self.do(factory.train(unit.WARPPRISM))
        #         break
        # if (self.units(unit.ROBOTICSBAY).ready.exists and self.units(unit.DISRUPTOR).amount < 2 and
        #     self.units(unit.IMMORTAL).amount > 2) or (self.units(unit.IMMORTAL).amount > 7
        #                                               and self.units(unit.ROBOTICSBAY).ready.exists and self.units(
        #             unit.DISRUPTOR).amount < 3):
        #     for rf in self.units(unit.ROBOTICSFACILITY).ready.noqueue:
        #         if self.can_afford(unit.DISRUPTOR) and self.supply_left > 2:
        #             await self.do(rf.train(unit.DISRUPTOR))
        elif self.can_afford(unit.IMMORTAL) and self.supply_left > 3 and self.structures(unit.ROBOTICSFACILITY).ready.exists \
                and self.units(unit.IMMORTAL).amount < 4:
            for factory in self.structures(unit.ROBOTICSFACILITY).ready.idle:
                self.do(factory.train(unit.IMMORTAL))

    async def ramp_wall_build(self):
        if self.structures(unit.NEXUS).ready.amount > 1 and self.army.amount > 3:
            pylon = self.structures(unit.PYLON).closer_than(5, self.second_ramp.top_center)
            if not pylon.exists and self.can_afford(unit.PYLON) and not self.already_pending(unit.PYLON):
                await self.build(unit.PYLON, near=self.second_ramp.top_center.towards(self.second_ramp.bottom_center, -5))
            elif pylon.ready.exists:
                if self.structures(unit.SHIELDBATTERY).amount < 2:
                    await self.build(unit.SHIELDBATTERY, near=pylon.random,placement_step=1)

    once = False

    async def defend(self):
        if self.structures(unit.NEXUS).amount < 2:
            self.defend_position = self.main_base_ramp.top_center
        else:
            self.defend_position = self.second_ramp.top_center.towards(self.second_ramp.bottom_center, -4)
        if self.enemy_units().exists and self.enemy_units().closer_than(20, self.defend_position):
            enemy = True
        else:
            enemy = False
        # en = self.enemy_units()
        # if en.exists and not self.once:
        #     closest_en = en.closest_to(self.defend_position)
        #     if closest_en.distance_to(self.defend_position) < 7:
        #         stalkers = self.army(unit.STALKER).sorted_by_distance_to(closest_en)
        #         stalkers = stalkers[:int(len(stalkers)/2)]
        #         placement = await self.find_placement(ability.TRAINWARP_ADEPT,closest_en.position,placement_step=1)
        #         for st in stalkers:
        #             await self.blink(st,placement)
        #         self.once = True
        for man in self.army:
            if man.distance_to(self.defend_position) > (25 if enemy else 12):
                self.do(man.move(self.defend_position.random_on_distance(4)))

    def train_army(self):
        gateway = self.structures(unit.GATEWAY).ready
        if self.minerals < 100 or not gateway.exists or not gateway.idle.exists:
            return
        if self.can_afford(unit.SENTRY) and self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(
            unit.SENTRY).amount < 1 and self.units(unit.STALKER).amount > 5:
            u = unit.SENTRY
        elif self.can_afford(unit.STALKER) and self.structures(unit.CYBERNETICSCORE).ready.exists:
            u = unit.STALKER
        elif self.can_afford(unit.ADEPT) and self.structures(unit.CYBERNETICSCORE).ready.exists:
            u = unit.ADEPT
        elif self.supply_left > 1 and self.minerals > 200 and self.units(unit.ZEALOT).amount < 5:
            u = unit.ZEALOT
        else:
            return
        gateway = gateway.ready.idle.random
        self.do(gateway.train(u))

    async def twilight_council_build(self):
        if self.structures(unit.CYBERNETICSCORE).ready.exists and self.time > 300:
            if not self.structures(unit.TWILIGHTCOUNCIL).exists \
                    and not self.already_pending(unit.TWILIGHTCOUNCIL) and self.can_afford(unit.TWILIGHTCOUNCIL):
                pylon = self.get_proper_pylon()
                await self.build(unit.TWILIGHTCOUNCIL,near=pylon.position,
                                 random_alternative=True,placement_step=2)
            # elif self.units(unit.TWILIGHTCOUNCIL).ready.exists and not self.units(unit.TEMPLARARCHIVE).exists and \
            #         self.can_afford(unit.TEMPLARARCHIVE) and not self.already_pending(unit.TEMPLARARCHIVE):
            #     await self.build(unit.TEMPLARARCHIVE,near=self.get_proper_pylon())
            # elif self.units(unit.TEMPLARARCHIVE).ready.exists:
            #     temparch = self.units(unit.TEMPLARARCHIVE).ready.random
            #     abilities = await self.get_available_abilities(temparch)
            #     if ability.RESEARCH_PSISTORM in abilities:
            #         await self.do(temparch(ability.RESEARCH_PSISTORM))
            if self.structures(unit.TWILIGHTCOUNCIL).ready.exists:
                tc = self.structures(unit.TWILIGHTCOUNCIL).ready.idle
                if tc.exists:
                    tc = tc.random
                else:
                    return
                abilities = await self.get_available_abilities(tc)
                # if ability.RESEARCH_ADEPTRESONATINGGLAIVES in abilities:
                #     await self.do(tc(ability.RESEARCH_ADEPTRESONATINGGLAIVES))
                # if ability.RESEARCH_CHARGE in abilities:
                #     await self.do(tc(ability.RESEARCH_CHARGE))
                if ability.RESEARCH_BLINK in abilities:
                    self.do(tc(ability.RESEARCH_BLINK))

    async def proxy(self):
        if self.build_type == 'rush':
            pylons = self.structures(unit.PYLON)
            if pylons.exists:
                if pylons.further_than(40, self.start_location.position).amount == 0 and not\
                        self.already_pending(unit.PYLON):
                    pos = self.game_info.map_center.position.towards(self.enemy_start_locations[0], 30)
                    # pos = Point2((pos.x, pos.y - 25))
                    placement = await self.find_placement(unit.PYLON, near=pos, max_distance=20, placement_step=1,
                                                         random_alternative=False)
                    await self.build(unit.PYLON, near=placement)

    async def build_gate(self):
        gates_count = self.structures(unit.GATEWAY).amount
        gates_count += self.structures(unit.WARPGATE).amount

        if gates_count < (2 if self.build_type == 'rush' else 2 if self.structures(unit.NEXUS).ready.amount > 1 else 1) \
                and self.can_afford(unit.GATEWAY) and self.structures(unit.PYLON).ready.exists and\
                self.already_pending(unit.GATEWAY) < (1 if self.build_type == 'macro' else 2):
            pylon = self.get_proper_pylon()
            if pylon is None:
                # print("Cannot find proper pylon for gateway")
                return
            await self.build(unit.GATEWAY, near=pylon, placement_step=2)
        elif 1 < gates_count < 4 and self.can_afford(unit.GATEWAY) and self.structures(unit.PYLON).ready.exists and\
                self.already_pending(unit.GATEWAY) < 1:
            pylon = self.get_proper_pylon()
            if pylon is None:
                # print("Cannot find proper pylon for gateway")
                return
            await self.build(unit.GATEWAY, near=pylon, placement_step=2)
        elif 3 < gates_count < (9 if self.minerals > 300 else 6) and self.can_afford(unit.GATEWAY) and self.structures(unit.NEXUS).ready.amount > 1 and\
                self.already_pending(unit.GATEWAY) < 1:
            pylon = self.get_proper_pylon()
            if pylon is None:
                # print("Cannot find proper pylon for gateway")
                return
            await self.build(unit.GATEWAY, near=pylon, placement_step=2)

    async def first_pylon(self):
        if self.structures(unit.PYLON).amount < 1 and self.can_afford(unit.PYLON):
            await self.build(unit.PYLON, self.start_location.position.towards(self.game_info.map_center, 7))

    async def build_pylons(self):
        if self.structures(unit.PYLON).exists:
            if self.time < 240:
                pending = 2
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
                        if self.structures(unit.PYLON).closest_to(self.main_base_ramp.top_center).distance_to(
                                placement) < 6:
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
        elif 54 < workers < 60:
            if self.can_afford(unit.PROBE) and not self.already_pending(unit.PROBE):
                if self.structures(unit.NEXUS).idle.amount < nex:
                    return
                nexus = self.structures(unit.NEXUS).ready.idle.random
                self.do(nexus.train(unit.PROBE))

    def build_assimilators(self):
        if self.structures(unit.GATEWAY).exists or self.structures(unit.WARPGATE).exists:
            if not self.can_afford(unit.ASSIMILATOR) or self.time < 260 and\
                    self.structures(unit.ASSIMILATOR).amount > 1 or self.structures(unit.NEXUS).amount > 2:
                return
            for nexus in self.structures(unit.NEXUS).ready:
                vaspenes = self.vespene_geyser.closer_than(10.0, nexus)
                for vaspene in vaspenes:

                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break

                    if not self.structures(unit.ASSIMILATOR).exists or (not
                            self.structures(unit.ASSIMILATOR).closer_than(1.0, vaspene).exists and self.time > 100):
                        self.do(worker.build(unit.ASSIMILATOR, vaspene))
                        return

    def get_proper_pylon(self):
        properPylons = self.structures().filter(lambda unit_: unit_.type_id == unit.PYLON and unit_.is_ready and
            unit_.distance_to(self.start_location.position) < 30 and unit_.distance_to(self.defend_position) > 9)
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
        # if self.structures(unit.ROBOTICSFACILITY).ready.idle.exists and \
        #         self.army(unit.IMMORTAL).amount < 3:
        #     return
        for warpgate in self.structures(unit.WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            # all the units have the same cooldown anyway so let's just look at ZEALOT
            if ability.WARPGATETRAIN_ZEALOT in abilities:

                furthest_pylon = self.structures(unit.PYLON).furthest_to(self.start_location.position)
                if self.attack:
                    pos = furthest_pylon.position.to2.random_on_distance(6)
                else:
                    pos = self.structures(unit.PYLON).ready.closer_than(20, self.start_location).furthest_to(
                        self.start_location).position.to2.random_on_distance(7)
                if self.can_afford(unit.SENTRY) and self.units(unit.STALKER).amount > 6 and \
                        self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(unit.SENTRY).amount < 1:
                    placement = await self.find_placement(ability.TRAINWARP_ADEPT,pos,placement_step=1)
                    if placement is None:
                        # print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.SENTRY,placement))
                elif self.can_afford(unit.STALKER) and self.supply_left > 1 and self.units(unit.STALKER).amount < 999:
                    placement = await self.find_placement(ability.WARPGATETRAIN_STALKER, pos, placement_step=1)
                    if placement is None:
                        # print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.STALKER, placement))
                elif self.minerals > 130 and self.supply_left > 1 and \
                        self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(unit.ADEPT).amount < 12:
                    placement = await self.find_placement(ability.TRAINWARP_ADEPT, pos, placement_step=1)
                    if placement is None:
                        # print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.ADEPT, placement))

                elif self.vespene < 100 and self.minerals > 400 and self.can_afford(unit.ZEALOT) and \
                        self.supply_left > 10 and self.units(unit.ZEALOT).amount < 7:
                    placement = await self.find_placement(ability.WARPGATETRAIN_ZEALOT, pos, placement_step=1)
                    if placement is None:
                        # print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.ZEALOT, placement))

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
                target = self.structures().filter(lambda x: x.type_id == unit.FORGE
                               and x.is_ready and not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                if target.exists:
                    target = target.random
                else:
                    target = self.structures().filter(lambda x: x.type_id == unit.CYBERNETICSCORE
                        and x.is_ready and not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                    if target.exists:
                        target = target.random
                    else:
                        target = self.structures().filter(lambda x: x.type_id == unit.NEXUS and x.is_ready
                                        and not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                        if target.exists:
                            target = target.random
                        else:
                            target = self.structures().filter(lambda x: (x.type_id == unit.GATEWAY or x.type_id == unit.WARPGATE)
                                                                   and x.is_ready and not x.is_idle and not x.has_buff(
                                buff.CHRONOBOOSTENERGYCOST))
                            if target.exists:
                                target = target.random
                if target:
                    self.do(nexus(ability.EFFECT_CHRONOBOOSTENERGYCOST, target))

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

    def select_leader(self):
        army = self.army.filter(lambda x: x.type_id in [unit.STALKER,unit.ADEPT,unit.IMMORTAL, unit.ARCHON])
        if army.exists:
            leader = None
            for _ in range(10):
                leader = army.random
                close = army.closer_than(9,leader)
                if close.exists:
                    if close.amount + 1 >= 0.33 * army.amount:
                        break
            if leader is None:
                print('couldnt select leader  <<--------')
                return None
            return leader

    async def micro_units(self):
        def chunks(lst,n):
            """Yield successive n-sized chunks from list."""
            for i in range(0,len(lst),n):
                yield lst[i:i + n]
        # stalkers // mixed
        hole_army = self.army.filter(lambda x: x.type_id in [unit.STALKER, unit.ADEPT, unit.IMMORTAL])

        part_army = chunks(hole_army, 4)
        for army_l in part_army:
            army = Units(army_l, self)
            if army.exists:
                # leader = self.leader
                # if leader is None:
                leader = army.random
                # for _ in range(100):
                #     stalker = stalkers.random
                #     close = stalkers.closer_than(9, stalker)
                #     if close.exists:
                #         if close.amount + 1 >= 0.33 * stalkers.amount:
                #             break
                # if stalker is None:
                #     print('couldnt select leader  <<--------')
                #     return
                threats = self.enemy_units().filter(
                    lambda unit_: unit_.can_attack_ground and unit_.distance_to(leader) <= (20 if self.attack else 12) and
                                  unit_.type_id not in self.units_to_ignore)
                threats.extend(self.enemy_structures().filter(lambda x: x.can_attack_ground))
                if threats.exists:
                    #  Stalker region  #
                    closest_enemy = threats.closest_to(leader)
                    target = threats.sorted(lambda x: x.health + x.shield)[0]
                    if target.health_percentage * target.shield_percentage == 1 or target.distance_to(leader) > \
                            leader.distance_to(closest_enemy) + 4:
                        target = closest_enemy
                    pos = leader.position.towards(closest_enemy.position,-8)
                    if not self.in_pathing_grid(pos):
                        # retreat point, check 4 directions
                        enemy_x = closest_enemy.position.x
                        enemy_y = closest_enemy.position.y
                        x = leader.position.x
                        y = leader.position.y
                        delta_x = x - enemy_x
                        delta_y = y - enemy_y
                        left_legal = True
                        right_legal = True
                        up_legal = True
                        down_legal = True
                        if abs(delta_x) > abs(delta_y):   # check x direction
                            if delta_x > 0:  # dont run left
                                left_legal = False
                            else:      # dont run right
                                right_legal = False
                        else:     # check y dir
                            if delta_y > 0:    # dont run up
                                up_legal = False
                            else:      # dont run down
                                down_legal = False
                        x_ = x
                        y_ = y
                        counter = 0
                        paths_length = []
                        # left
                        if left_legal:
                            while self.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                x_ -= 1
                            paths_length.append((counter, (x_,y_)))
                            counter = 0
                            x_ = x
                        # right
                        if right_legal:
                            while self.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                x_ += 1
                            paths_length.append((counter, (x_,y_)))
                            counter = 0
                            x_ = x
                        # up
                        if up_legal:
                            while self.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                y_ -= 1
                            paths_length.append((counter, (x_,y_)))
                            counter = 0
                            y_ = y
                        # down
                        if down_legal:
                            while self.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                y_ += 1
                            paths_length.append((counter, (x_,y_)))

                        max_ = (-2,0)
                        for path in paths_length:
                            if path[0] > max_[0]:
                                max_ = path
                        if max_[0] < 4:    # there is nowhere to run - fight.
                            pos = None
                        else:
                            pos = Point2(max_[1])
                    # placement = None
                    # while placement is None:
                    #     placement = await self.find_placement(unit.PYLON,pos,placement_step=1)

                    for st in army:
                        if pos is not None and st.weapon_cooldown > 0 and st.shield_percentage < 0.33 and \
                            closest_enemy.ground_range <= st.ground_range and threats.amount * 2 > army.amount:
                            if not await self.blink(st, pos):
                                self.do(st.move(pos))
                        else:
                            if st.distance_to(target) > 6:
                                if not await self.blink(st,target.position):
                                    self.do(st.attack(target))

        #  Sentry region  #
        for se in self.units(unit.SENTRY):
            threats = self.enemy_units().filter(
                lambda unit_: unit_.can_attack_ground and unit_.distance_to(se) <= 9 and
                              unit_.type_id not in self.units_to_ignore and unit_.type_id not in self.workers_ids)
            if threats.amount > 3 and not se.has_buff(buff.GUARDIANSHIELD):
                if await self.can_cast(se,ability.GUARDIANSHIELD_GUARDIANSHIELD):
                    self.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))

            army_center = self.army.closer_than(9,se)
            if army_center.exists:
                army_center = army_center.center
                if se.distance_to(army_center) > 2:
                    if not threats.exists:
                        self.do(se.move(army_center))
                    else:
                        self.do(se.move(army_center.towards(threats.closest_to(se),-1)))

    async def attack_formation(self):
        enemy_units = self.enemy_units()
        enemy = enemy_units.filter(lambda x: x.type_id not in self.units_to_ignore and x.can_attack_ground)
        if enemy.exists:
            if self.leader is not None:
                destination = enemy.closest_to(self.leader)
            else:
                destination = enemy.closest_to(self.start_location.position)
        elif self.enemy_structures().exists:
            enemy = self.enemy_structures()
            if self.leader is not None:
                destination = enemy.closest_to(self.leader)
            else:
                destination = enemy.closest_to(self.start_location.position)
        else:
            enemy = None
            destination = self.enemy_start_locations[0].position
        if self.leader is not None:
            start = self.leader
        else:
            start = self.army.closest_to(destination)
        if self.build_type == 'macro' and len(self.known_enemies) < 10:
            for man in self.army.idle:
                self.do(man.attack(destination))
            return

        # point halfway
        dist = start.distance_to(destination)
        if dist > 40:
            point = start.position.towards(destination, dist / 3)
        elif dist > 20:
            point = start.position.towards(destination, dist / 2)
        else:
            point = destination.position
        position = None
        i = 0
        while position is None:
            position = await self.find_placement(unit.PYLON, near=point, max_distance=30, placement_step=1,
                                                 random_alternative=False)
            i += 1
            if i > 5:
                # print("can't find position for army.")
                return
        # if everybody's here, we can go
        _range = 9 if self.army.amount < 30 else 12

        nearest = self.army.closer_than(_range, start.position)
        exclude = [unit.DISRUPTOR, unit.HIGHTEMPLAR]

        if nearest.amount > self.army.amount * 0.7:
            for man in self.army:
                # if man.is_idle:
                if enemy is not None and not enemy.in_attack_range_of(man).exists:
                    if man.type_id == unit.STALKER:
                        if await self.blink(man, enemy.closest_to(man).position.towards(man.position, 6)):
                            continue
                    else:
                        closest_en = enemy.closest_to(man)
                        self.do(man.attack(closest_en))
                else:
                    #if not man.is_attacking:
                    self.do(man.move(position))
        else:
            # center = nearest.center
            for man in self.army.filter(lambda man_: man_.distance_to(start) > 11):# and not man_.is_attacking):
                self.do(man.move(start))

    async def blink(self, stalker, target):
        abilities = await self.get_available_abilities(stalker)
        if ability.EFFECT_BLINK_STALKER in abilities:
            placement = await self.find_placement(ability.TRAINWARP_ADEPT,target,placement_step=1)
            self.do(stalker(ability.EFFECT_BLINK_STALKER, placement))
            return True
        else:
            return False

    async def expand(self):
        gates_count = self.structures(unit.GATEWAY).amount
        gates_count += self.structures(unit.WARPGATE).amount
        if gates_count < 1:
            return
        nexuses = self.structures(unit.NEXUS).ready
        if nexuses.amount < 2 and (self.build_type == 'macro' or self.proper_nexus_count == 2):
            self.proper_nexus_count = 2
            if self.can_afford(unit.NEXUS) and not self.already_pending(unit.NEXUS):
                await self.expand_now2()
        elif 3 > nexuses.amount > 1 and self.units(
                unit.PROBE).amount >= 34 and len(self.army) > 16:
            if self.proper_nexus_count == 2:
                self.proper_nexus_count = 3
            if self.can_afford(unit.NEXUS) and not self.already_pending(unit.NEXUS):
                await self.expand_now2()
        # elif nexuses.amount > 2:
        #     totalExcess = 0
        #     for location, townhall in self.owned_expansions.items():
        #         actual = townhall.assigned_harvesters
        #         ideal = townhall.ideal_harvesters
        #         excess = actual - ideal
        #         totalExcess += excess
        #     for g in self.vespene_geyser:
        #         actual = g.assigned_harvesters
        #         ideal = g.ideal_harvesters
        #         excess = actual - ideal
        #         totalExcess += excess
        #     totalExcess += self.units(unit.PROBE).ready.idle.amount
        #     if totalExcess > 1 and not self.already_pending(unit.NEXUS):
        #         self.proper_nexus_count = 4
        #         if self.can_afford(unit.NEXUS):
        #             await self.expand_now2()
        #     elif self.proper_nexus_count == 4:
        #         self.proper_nexus_count = 3

    def find_2nd_ramp(self):
        second_ramp = None
        min_dist = 40
        first_ramp_dist = self.start_location.distance_to(self.main_base_ramp.top_center)
        for ramp in self.game_info.map_ramps:
            dist = self.start_location.distance_to(ramp.top_center)
            if first_ramp_dist + 5 < dist < min_dist:
                min_dist = dist
                second_ramp = ramp
        return second_ramp

    async def expand_now2(self):
        """Takes new expansion."""
        building = None
        if building is None:
            # self.race is never Race.Random
            start_townhall_type = {Race.Protoss: unit.NEXUS, Race.Terran: unit.COMMANDCENTER,
                                   Race.Zerg: unit.HATCHERY}
            building = start_townhall_type[self.race]
        assert isinstance(building, unit)
        location = None
        if location is None:
            location = await self.get_next_expansion2()
        if location is not None:
            await self.build(building, near=location, max_distance=5, random_alternative=False, placement_step=1)

    async def get_next_expansion2(self):
        """Find next expansion location."""
        closest = None
        distance = math.inf
        minerals = None

        for el in self.expansion_locations:
            def is_near_to_expansion(t):
                return t.position.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            if minerals and minerals.distance_to(el) < 9:
                return el

            if self.mineral_field.closer_than(15, el).amount < 3:
                # almost out of minerals
                continue

            startp = self._game_info.player_start_location
            d = await self._client.query_pathing(startp, el)
            if d is None:
                continue

            if d < distance:
                distance = d
                closest = el
        return closest


def botVsComputer():
    maps_set = ['blink', "zealots", "Bandwidth", "Reminiscence", "TheTimelessVoid", "PrimusQ9", "Ephemeron",
                "Sanglune", "Urzagol"]
    training_maps = ["DefeatZealotswithBlink", "ParaSiteTraining"]
    races = [Race.Protoss, Race.Zerg, Race.Terran]
    computer_builds = [AIBuild.Macro, AIBuild.Rush, AIBuild.Timing, AIBuild.Power, AIBuild.Air]
    build = random.choice(computer_builds)
    map_index = random.randint(0, 6)
    race_index = random.randint(0, 2)
    res = run_game(map_settings=maps.get(maps_set[2]), players=[
        Bot(race=Race.Protoss, ai=Octopus(), name='Octopus'),
        Computer(race=races[0], difficulty=Difficulty.VeryHard, ai_build=AIBuild.Macro)
    ], realtime=False)
    return res, build, races[race_index]


def test():
    results = []
    score_board = {Race.Protoss: [0,0],Race.Zerg: [0,0],Race.Terran: [0,0]}
    win = 0
    for i in range(1):
        try:
            result = botVsComputer()
            result_str = str(result[0]) + ' ' + str(result[2]) + ' ' + str(result[1])
            print(result_str)
            if result[0] == Result.Victory:
                score_board[result[2]][0] += 1
                win += 1
            score_board[result[2]][1] += 1
        except Exception as ex:
            print('Error.')
            print(ex)

    print('================= Results ===================')
    for res in results:
        print(res)
    print('=============================================')
    print('win: ' + str(win) + '/' + '100')
    print('win vs Protoss: ' + str(score_board[Race.Protoss][0]) + '/' + str(score_board[Race.Protoss][1]))
    print('win vs Zerg: ' + str(score_board[Race.Zerg][0]) + '/' + str(score_board[Race.Zerg][1]))
    print('win vs Terran: ' + str(score_board[Race.Terran][0]) + '/' + str(score_board[Race.Terran][1]))
    print('=============================================')


test()