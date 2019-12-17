import random
from sc2 import run_game, maps, Race, Difficulty, Result, AIBuild
import sc2
from sc2.constants import FakeEffectID
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.player import Bot, Computer
from sc2.units import Units
from sc2.ids.buff_id import BuffId as buff
from sc2.ids.upgrade_id import UpgradeId as upgrade
from sc2.ids.effect_id import EffectId as effect
from sc2.position import Point2
import numpy as np
import cv2


class Octopus(sc2.BotAI):
    enemy_attack = False
    second_ramp = None
    builds = ['rush', 'macro', 'defend_rush']
    build_type = 'macro'
    enemy_main_base_down = False
    first_attack = False
    attack = False
    after_first_attack = False
    army_ids = [unit.ADEPT, unit.STALKER, unit.ZEALOT, unit.SENTRY, unit.OBSERVER, unit.IMMORTAL, unit.ARCHON,
                unit.HIGHTEMPLAR, unit.DISRUPTOR, unit.WARPPRISM, unit.VOIDRAY]
    units_to_ignore = [unit.LARVA, unit.EGG]
    workers_ids = [unit.SCV, unit.PROBE, unit.DRONE]
    proper_nexus_count = 1
    army = []
    known_enemies = []
    game_map = None
    leader = None
    defend_position = None

    prev_nexus_count = 0

    # async def on_unit_destroyed(self, unit_tag):
    #     try:
    #         if unit_tag in self.known_enemies:
    #             # print('known unit died!')
    #             self.known_enemies.remove(unit_tag)
    #         else:
    #             for u in self.army:
    #                 if u.tag == unit_tag:
    #                     self.army.remove(u)
    #     except:
    #         pass

    # async def on_unit_created(self, unit):
        # if unit.type_id in self.army_ids:
        #     self.army.append(unit)

    async def on_start(self):
        self.second_ramp = self.find_2nd_ramp()
        # self.known_enemies = Units(self.known_enemies,self)
        # self.army = Units(self.army,self)

    async def on_step(self, iteration):
        # for enemy in self.enemy_units():
        #     if enemy.tag not in self.known_enemies:
        #         # print('new enemy!')
        #         self.known_enemies.append(enemy.tag)

        self.assign_defend_position()
        if (self.build_type == 'rush' or self.build_type == 'defend_rush') and self.after_first_attack and\
                self.time > 420:
            self.build_type = 'macro'

        self.army = self.units().filter(lambda x: x.type_id in self.army_ids)
        if self.time < 300 and self.enemy_units().exists and\
                self.enemy_units().closer_than(20,self.defend_position).amount > 3 and self.army(unit.PROBE).amount == 0:
            probes = self.units(unit.PROBE).sorted(lambda x: x.shield + x.health)
            self.army.extend(probes[int(len(probes)/2):])
        elif self.time < 360:
            self.army = self.army.filter(lambda x: x.type_id != unit.PROBE)
        # self.leader = self.select_leader()

        # await self.twilight_council_build()
        # await self.robotics_facility()
        await self.stargate_build()
        await self.make_forge()
        # await self.ramp_wall_build()
        await self.nexus_buff()
        await self.first_pylon()
        await self.build_pylons()
        await self.distribute_workers()
        await self.expand()
        # await self.adept_hunt()
        self.train_workers()
        # counter attack
        if self.enemy_units().exists and self.enemy_units().closer_than(20, self.defend_position).amount > 2:
            self.enemy_attack = True
        if self.enemy_attack and self.enemy_units().amount < 5: # and self.enemy_units().closer_than(18, self.defend_position).amount < 4:
            self.enemy_attack = False
            self.after_first_attack = True
            self.attack = True
        if self.structures(unit.NEXUS).amount >= self.proper_nexus_count or self.already_pending(unit.NEXUS) or self.minerals > 400:
            # print('nex amount = ' + str(self.structures(unit.NEXUS).amount))
            # print('proper amount = ' + str(self.proper_nexus_count))
            await self.cybernetics_core_build()
            await self.build_gate()
            self.train_army()
            await self.warp_new_units()
            self.cybernetics_core_upgrades()
            self.build_assimilators()
        await self.morph_gates()

        if self.build_type == 'rush' and self.army.amount > 6 and not self.first_attack:
            self.first_attack = True
            self.attack = True
        if self.build_type == 'rush' and self.army.amount > 2 or self.attack:
            await self.proxy()
        if self.attack and self.army.amount < (5 if self.build_type == 'rush' else 30):
            self.attack = False
        if self.attack:
            await self.attack_formation()
        else:
            await self.defend()
        await self.micro_units()

    async def start_step(self):
        pass

    async def make_forge(self):
        if self.time < 160 or self.build_type is not 'macro':
            return
        if self.structures(unit.FORGE).amount < 1 and not self.already_pending(unit.FORGE) and self.can_afford(unit.FORGE):
            if self.structures(unit.PYLON).ready.exists:
                placement = self.get_proper_pylon()
                if placement:
                    await self.build(unit.FORGE,near=placement,placement_step=2)
        elif self.structures(unit.FORGE).ready.exists:
            if self.time > 480 and self.structures(unit.FORGE).amount < 2 and not self.already_pending(
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
                        upgrade.PROTOSSSHIELDSLEVEL1 in self.state.upgrades and self.structures(
                    unit.TWILIGHTCOUNCIL).ready.exists:
                    self.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL2))
                elif upgrade.PROTOSSSHIELDSLEVEL3 not in self.state.upgrades and not self.already_pending_upgrade(
                        upgrade.PROTOSSSHIELDSLEVEL3) and self.can_afford(upgrade.PROTOSSSHIELDSLEVEL3) and \
                        upgrade.PROTOSSSHIELDSLEVEL2 in self.state.upgrades:
                    self.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL3))

    def forge_upg_priority(self):
        if self.structures(unit.TWILIGHTCOUNCIL).ready.exists:
            upgds = [upgrade.PROTOSSGROUNDWEAPONSLEVEL1,upgrade.PROTOSSGROUNDARMORSLEVEL2,upgrade.PROTOSSSHIELDSLEVEL1]
        else:
            upgds = [upgrade.PROTOSSGROUNDWEAPONSLEVEL1,upgrade.PROTOSSGROUNDARMORSLEVEL1,upgrade.PROTOSSSHIELDSLEVEL1]

        done = True
        for u in upgds:
            if u not in self.state.upgrades:
                done = False
                break
        if not done:
            if self.structures(unit.FORGE).ready.idle.exists:
                return True
        return False

    async def robotics_facility(self):
        if self.forge_upg_priority():
            return
        if self.build_type == 'macro':
            time = 220
        else:
            time = 180
        if self.structures(unit.ROBOTICSFACILITY).amount < 1 and self.can_afford(unit.ROBOTICSFACILITY)\
                and not self.already_pending(unit.ROBOTICSFACILITY) and self.time > time:
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
                and self.units(unit.IMMORTAL).amount < 6:
            for factory in self.structures(unit.ROBOTICSFACILITY).ready.idle:
                self.do(factory.train(unit.IMMORTAL))

    async def stargate_build(self):
        if self.structures(unit.STARGATE).exists:
            if self.can_afford(unit.ORACLE) and self.units(unit.ORACLE).amount < 3:
                self.train(unit_type=unit.ORACLE)
        elif self.structures(unit.CYBERNETICSCORE).ready.exists\
                and self.can_afford(unit.STARGATE) and not self.already_pending(unit.STARGATE):
            await self.build(unit.STARGATE, near=self.get_proper_pylon())

    async def oracle_micro(self):
        pass

    def build_batteries(self):
        if not self.structures(unit.PYLON).closer_than(5,self.defend_position).exists:
            self.build(unit.PYLON, near=self.defend_position.towards(self.structures(unit.NEXUS).closest_to(self.defend_position)))

    async def ramp_wall_build(self):
        nexs = self.structures(unit.NEXUS).amount
        if nexs > 1:
            pylon = self.structures(unit.PYLON).closer_than(5, self.defend_position)
            if not pylon.exists and self.can_afford(unit.PYLON) and not self.already_pending(unit.PYLON):
                await self.build(unit.PYLON, near=self.defend_position)
            elif pylon.ready.exists:
                if self.structures(unit.SHIELDBATTERY).amount < 2 * nexs and not self.already_pending(unit.SHIELDBATTERY):
                    await self.build(unit.SHIELDBATTERY, near=pylon.random,placement_step=1)
                if self.structures(unit.PHOTONCANNON).amount < 1 * nexs and not self.already_pending(unit.PHOTONCANNON):
                    await self.build(unit.PHOTONCANNON, near=pylon.random,placement_step=1)

    async def defend(self):
        enemy = self.enemy_units()
        if enemy.exists:
            dist = 25
        else:
            dist = 6
        for man in self.army:
            if man.distance_to(self.defend_position) > dist:
                self.do(man.move(self.defend_position.random_on_distance(random.randint(1,3))))
            if enemy.exists and not enemy.in_attack_range_of(man).exists:
                self.do(man.attack(enemy.closest_to(man)))

    def assign_defend_position(self):
        nex = self.structures(unit.NEXUS)
        enemy = self.enemy_units()

        if self.prev_nexus_count != nex.amount or enemy.exists:
            if nex.amount < 2:
                self.defend_position = self.main_base_ramp.top_center.towards(self.main_base_ramp.bottom_center, -6)
            elif nex.amount == 2:
                self.defend_position = self.second_ramp.top_center.towards(self.second_ramp.bottom_center,-6)
            else:
                min = 999
                ramp = None
                if enemy.exists and enemy.closer_than(50,self.start_location).amount > 0:
                    nex = nex.closest_to(enemy.closest_to(self.enemy_start_locations[0]))
                else:
                    nex = nex.furthest_to(self.start_location)
                p = nex.position.towards(self.second_ramp.bottom_center,7)
                for rmp in self.game_info.map_ramps:
                    d = p.distance_to(rmp.top_center)

                    if d < min:
                        min = d
                        ramp = rmp
                if min < 15:
                    self.defend_position = ramp.top_center.towards(ramp.bottom_center, -1)
                else:
                    self.defend_position = nex.position.towards(self.game_info.map_center,5)

    def train_army(self):
        gateway = self.structures(unit.GATEWAY).ready
        if self.minerals < 100 or not gateway.exists or not gateway.idle.exists:
            return
        if self.can_afford(unit.SENTRY) and self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(
            unit.SENTRY).amount < 3:
            u = unit.SENTRY
        elif self.can_afford(unit.STALKER) and self.structures(unit.CYBERNETICSCORE).ready.exists:
            u = unit.STALKER
        # elif self.can_afford(unit.ADEPT) and self.structures(unit.CYBERNETICSCORE).ready.exists and \
        #         self.army(unit.ADEPT).amount < 2:
        #     u = unit.ADEPT
        elif self.supply_left > 1 and self.minerals > 175 and self.units(unit.ZEALOT).amount < 4:
            u = unit.ZEALOT
        else:
            return
        gateway = gateway.ready.idle.random
        self.do(gateway.train(u))

    async def twilight_council_build(self):
        if self.structures(unit.CYBERNETICSCORE).ready.exists and self.time > 220 and self.build_type == 'macro':
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
        if self.build_type == 'rush' or self.build_type == 'macro' and self.attack:
            pylons = self.structures(unit.PYLON)
            if pylons.exists:
                if pylons.further_than(40, self.start_location.position).amount == 0 and not\
                        self.already_pending(unit.PYLON):
                    pos = self.game_info.map_center.position.towards(self.enemy_start_locations[0], 30)
                    # pos = Point2((pos.x, pos.y - 25))
                    c=0
                    placement = None
                    while placement is None and c < 5:
                        c+=1
                        placement = await self.find_placement(unit.PYLON, near=pos, max_distance=20, placement_step=2,
                                                         random_alternative=False)
                    if placement is not None:
                        await self.build(unit.PYLON, near=placement)

    async def build_gate(self):
        gates_count = self.structures(unit.GATEWAY).amount
        gates_count += self.structures(unit.WARPGATE).amount

        if self.build_type == 'macro' and self.structures(unit.NEXUS).amount < 2:
            gc = 1
        else:
            gc = 2
        if gates_count < gc \
                and self.can_afford(unit.GATEWAY) and self.structures(unit.PYLON).ready.exists and\
                self.already_pending(unit.GATEWAY) < 2:
            if gates_count < 1:
                pylon = self.main_base_ramp.protoss_wall_buildings[0]
            else:
                pylon = self.main_base_ramp.protoss_wall_buildings[1]
            if pylon is None:
                # print("Cannot find proper pylon for gateway")
                return
            await self.build(unit.GATEWAY, near=pylon, placement_step=2)
        elif 1 < gates_count < 4 and self.can_afford(unit.GATEWAY) and self.time > 180 and\
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
        if self.structures(unit.PYLON).amount < 1 and self.can_afford(unit.PYLON) and not self.already_pending(unit.PYLON):
            await self.build(unit.PYLON, near=self.main_base_ramp.protoss_wall_pylon)

    async def build_pylons(self):
        if self.structures(unit.PYLON).exists:
            if self.time < 120:
                pending = 1
                left = 5
            else:
                pending = 2
                left = 8
            if self.supply_left < left and self.supply_cap < 200:
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
                    self.structures(unit.ASSIMILATOR).amount > 1 or self.structures(unit.NEXUS).amount > 2 \
                    and self.vespene > self.minerals:
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
        if self.structures(unit.ROBOTICSFACILITY).ready.idle.exists and \
                self.army(unit.IMMORTAL).amount < 4 or self.forge_upg_priority():
            return
        for warpgate in self.structures(unit.WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            # all the units have the same cooldown anyway so let's just look at ZEALOT
            if ability.WARPGATETRAIN_ZEALOT in abilities:

                furthest_pylon = self.structures(unit.PYLON).ready.furthest_to(self.start_location.position)
                if self.attack:
                    pos = furthest_pylon.position.to2.random_on_distance(6)
                else:
                    pos = self.structures(unit.PYLON).ready.closer_than(20, self.start_location).furthest_to(
                        self.start_location).position.to2.random_on_distance(7)
                if self.can_afford(unit.SENTRY) and self.units(unit.STALKER).amount > 7 and \
                        self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(unit.SENTRY).amount < 5:
                    placement = await self.find_placement(ability.TRAINWARP_ADEPT,pos,placement_step=1)
                    if placement is None:
                        # print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.SENTRY,placement))
                elif self.can_afford(unit.STALKER) and self.supply_left > 1:
                    placement = await self.find_placement(ability.WARPGATETRAIN_STALKER, pos, placement_step=1)
                    if placement is None:
                        # print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.STALKER, placement))
                elif self.minerals > 150 and self.supply_left > 1 and \
                        self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(unit.ADEPT).amount < 5:
                    placement = await self.find_placement(ability.TRAINWARP_ADEPT, pos, placement_step=1)
                    if placement is None:
                        # print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.ADEPT, placement))

                elif self.vespene < 50 and self.minerals > 150 and self.can_afford(unit.ZEALOT) and \
                        self.supply_left > 5 and self.units(unit.ZEALOT).amount < 10:
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
            for _ in range(5):
                leader = army.random
                close = army.closer_than(9,leader)
                if close.exists:
                    if close.amount + 1 >= 0.33 * army.amount:
                        break
            if leader is None:
                print('couldnt select leader  <<--------')
                return None
            # if self.enemy_units().exists:
            #     leader = army.closest_to(self.enemy_units().closest_to(self.defend_position))
            # else:
            #     leader = army.closest_to(self.enemy_start_locations[0].position)
            return leader

    async def adept_hunt(self):
        adepts = self.army(unit.ADEPT).ready
        destination = self.enemy_start_locations[0]
        if adepts.amount > 3:
            for adept in adepts:
                targets = self.enemy_units().filter(lambda x: x.type_id in self.workers_ids and x.distance_to(adept) < 12)
                if targets.exists:

                    closest = targets.closest_to(adept)
                    target = targets.sorted(lambda x: x.health + x.shield)[0]
                    if target.health_percentage * target.shield_percentage == 1 or \
                            target.distance_to(adept) > closest.distance_to(adept) + 4:
                        target = closest
                    self.do(adept.attack(target))
                elif ability.ADEPTPHASESHIFT_ADEPTPHASESHIFT in await self.get_available_abilities(adept) and\
                        adept.distance_to(destination) > 12:
                    self.do(adept(ability.ADEPTPHASESHIFT_ADEPTPHASESHIFT, destination))
                else:
                    self.do(adept.move(destination))
            for shadow in self.units(unit.ADEPTPHASESHIFT):
                self.do(shadow.move(destination))


    async def micro_units(self):
        enemy = self.enemy_units()
        if not enemy.exists:
            return

        # def shuffle(arr):
        #     for n in range(len(arr) - 1):
        #         rnd = random.randint(0,(len(arr) - 1))
        #         val1 = arr[rnd]
        #         val2 = arr[rnd - 1]
        #         arr[rnd - 1] = val1
        #         arr[rnd] = val2
        #     return arr

        def chunk(lst,n):
            for i in range(0,len(lst),n):
                yield lst[i:i + n]
        # stalkers // mixed
        whole_army = self.army  #.filter(lambda x: x.type_id in [unit.STALKER, unit.ADEPT, unit.IMMORTAL])
        dist = 12# if self.attack else 12
        group_size = 7
        c = int(len(whole_army) / group_size)
        chunks = c if c > 0 else 1
        part_army = chunk(whole_army, chunks)
        for army_l in part_army:
            army = Units(army_l, self)
            if army.exists:
                # leader = self.leader
                # if leader is None:
                leader = army.random
                threats = self.enemy_units().filter(
                    lambda unit_: unit_.can_attack_ground and unit_.distance_to(leader) <= dist and
                                  unit_.type_id not in self.units_to_ignore)
                threats.extend(self.enemy_structures().filter(lambda x: x.can_attack_ground))
                if threats.exists:
                    closest_enemy = threats.closest_to(leader)
                    target = threats.filter(lambda x: x in [unit.COLOSSUS, unit.DISRUPTOR, unit.HIGHTEMPLAR,
                                                            unit.MEDIVAC, unit.SIEGETANKSIEGED, unit.SIEGETANK])
                    if target.exists:
                        target = target.sorted(lambda x: x.health + x.shield)[0]
                    else:
                        target = threats.sorted(lambda x: x.health + x.shield)[0]
                    if target.health_percentage * target.shield_percentage == 1 or target.distance_to(leader) > \
                            leader.distance_to(closest_enemy) + 3:
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
                        if abs(delta_x) > abs(delta_y):  # check x direction
                            if delta_x > 0:  # dont run left
                                left_legal = False
                            else:  # dont run right
                                right_legal = False
                        else:  # check y dir
                            if delta_y > 0:  # dont run up
                                up_legal = False
                            else:  # dont run down
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
                            paths_length.append((counter,(x_,y_)))
                            counter = 0
                            x_ = x
                        # right
                        if right_legal:
                            while self.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                x_ += 1
                            paths_length.append((counter,(x_,y_)))
                            counter = 0
                            x_ = x
                        # up
                        if up_legal:
                            while self.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                y_ -= 1
                            paths_length.append((counter,(x_,y_)))
                            counter = 0
                            y_ = y
                        # down
                        if down_legal:
                            while self.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                y_ += 1
                            paths_length.append((counter,(x_,y_)))

                        max_ = (-2,0)
                        for path in paths_length:
                            if path[0] > max_[0]:
                                max_ = path
                        if max_[0] < 4:  # there is nowhere to run - fight.
                            pos = None
                        else:
                            pos = Point2(max_[1])
                    # placement = None
                    # while placement is None:
                    #     placement = await self.find_placement(unit.PYLON,pos,placement_step=1)

                    for st in army:
                        if pos is not None and st.weapon_cooldown > 0 and \
                            closest_enemy.ground_range <= st.ground_range and threats.amount * 2 > army.amount:
                            if not await self.blink(st, pos):
                                self.do(st.move(st.position.towards(pos,2)))
                        else:
                            if st.distance_to(target) > 6:
                                if not await self.blink(st,target.position.towards(st,6)):
                                    self.do(st.attack(target))

        #  Sentry region  #
        sents = self.army(unit.SENTRY)
        if sents.exists:
            # sentry = sents.in_closest_distance_to_group(self.army)
            m = -1
            for se in sents:
                close = sents.closer_than(7, se).amount
                if close > m:
                    m = close
                    sentry = se
            force_fields = []
            guardian_shield_on = False
            for eff in self.state.effects:
                if eff.id == FakeEffectID.get(unit.FORCEFIELD.value):
                    force_fields.append(eff)
                elif not guardian_shield_on and eff.id == effect.GUARDIANSHIELDPERSISTENT:
                    guardian_shield_on = True
            threats = self.enemy_units().filter(
                lambda unit_: unit_.can_attack_ground and unit_.distance_to(sentry) <= 16 and
                              unit_.type_id not in self.units_to_ignore and unit_.type_id not in self.workers_ids)

            enemy_army_center = None
            has_energy_amount = sents.filter(lambda x: x.energy >= 50).amount
            points = []
            if self.build_type == 'macro':
                thr = 4
                ff = 7
            else:
                thr = 2
                ff = 1
            if has_energy_amount > 0 and len(force_fields) < ff and threats.amount > thr:  # and self.time - self.force_field_time > 1:
                # self.force_field_time = self.time
                enemy_army_center = threats.center
                gap = 2
                if self.build_type == 'defend_rush':
                    points.append(self.main_base_ramp.protoss_wall_warpin)
                else:
                    points.append(enemy_army_center)
                    points.append(Point2((enemy_army_center.x - gap, enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x + gap, enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x, enemy_army_center.y - gap)))
                    points.append(Point2((enemy_army_center.x, enemy_army_center.y + gap)))
            for se in self.units(unit.SENTRY):
                abilities = await self.get_available_abilities(se)
                if threats.amount > thr and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities:
                    self.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                    guardian_shield_on = True
                if ability.FORCEFIELD_FORCEFIELD in abilities and enemy_army_center is not None and len(points) > 0:
                    self.do(se(ability.FORCEFIELD_FORCEFIELD, points.pop(0)))
                else:
                    army_center = self.army.closer_than(9,se)
                    if army_center.exists:
                        army_center = army_center.center
                        if se.distance_to(army_center) > 3:
                            if not threats.exists:
                                self.do(se.move(army_center))
                            else:
                                self.do(se.move(army_center.towards(threats.closest_to(se),-1)))
        # zealot
        for zl in self.army(unit.ZEALOT):
            threats = self.enemy_units().filter(lambda x: x.distance_to(zl) < 9).sorted(lambda x: x.health + x.shield)
            if threats.exists:
                closest = threats.closest_to(zl)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(zl) > \
                    closest.distance_to(zl) + 4 or not self.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                self.do(zl.attack(target))

    async def attack_formation(self):
        enemy_units = self.enemy_units()
        enemy = enemy_units.filter(lambda x: x.type_id not in self.units_to_ignore and x.can_attack_ground)
        if enemy.amount > 2:
            if len(self.known_enemies) * 4 < len(self.army):
                for man in self.army:
                    self.do(man.attack(enemy.closest_to(man)))
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

        # point halfway
        dist = start.distance_to(destination)
        if dist > 30:
            point = start.position.towards(destination, dist / 2)
        # elif dist > 20:
        #     point = start.position.towards(destination, dist / 2)
        else:
            point = destination.position
        position = None
        i = 0
        while position is None:
            i += 1
            position = await self.find_placement(unit.PYLON, near=point.random_on_distance(i*3), max_distance=15, placement_step=5,
                                                 random_alternative=False)
            if i > 8:
                print("can't find position for army.")
                return
        # if everybody's here, we can go
        _range = 7 if self.army.amount < 24 else 9

        nearest = self.army.closer_than(_range, start.position)
        exclude = [unit.DISRUPTOR, unit.HIGHTEMPLAR]

        if nearest.amount > self.army.amount * 0.75:
            for man in self.army:
                # if man.is_idle:
                if enemy is not None and not enemy.in_attack_range_of(man).exists:
                    if man.type_id == unit.STALKER:
                        if not await self.blink(man, enemy.closest_to(man).position.towards(man.position, 6)):
                            self.do(man.attack(enemy.closest_to(man)))
                    else:
                        closest_en = enemy.closest_to(man)
                        self.do(man.attack(closest_en))
                elif enemy is None:
                    #if not man.is_attacking:
                    self.do(man.move(position))
        else:
            # center = nearest.center
            for man in self.army.filter(lambda man_: man_.distance_to(start) > _range/2):# and not man_.is_attacking):
                self.do(man.move(start))

    async def blink(self, stalker, target):
        abilities = await self.get_available_abilities(stalker)
        if ability.EFFECT_BLINK_STALKER in abilities:
            self.do(stalker(ability.EFFECT_BLINK_STALKER, target))
            return True
        else:
            return False

    async def expand(self):
        gates_count = self.structures(unit.GATEWAY).amount
        gates_count += self.structures(unit.WARPGATE).amount
        if gates_count < 1:
            return
        nexuses = self.structures(unit.NEXUS).ready
        if nexuses.amount < 2 and (self.build_type == 'macro' or self.proper_nexus_count == 2) or\
                (self.build_type == 'defend_rush' and self.after_first_attack or self.time > 360):
            self.proper_nexus_count = 2
            if self.can_afford(unit.NEXUS) and not self.already_pending(unit.NEXUS):
                await self.expand_now2()
        elif 3 > nexuses.amount > 1 and self.units(
                unit.PROBE).amount >= 34 and len(self.army) > 12:
            if self.proper_nexus_count == 2:
                self.proper_nexus_count = 3
            if self.can_afford(unit.NEXUS) and not self.already_pending(unit.NEXUS):
                await self.expand_now2()
        elif nexuses.amount > 2:
            totalExcess = 0
            for location, townhall in self.owned_expansions.items():
                actual = townhall.assigned_harvesters
                ideal = townhall.ideal_harvesters
                excess = actual - ideal
                totalExcess += excess
            for g in self.vespene_geyser:
                actual = g.assigned_harvesters
                ideal = g.ideal_harvesters
                excess = actual - ideal
                totalExcess += excess
            totalExcess += self.units(unit.PROBE).ready.idle.amount
            if totalExcess > 2 and not self.already_pending(unit.NEXUS):
                self.proper_nexus_count = 4
                if self.can_afford(unit.NEXUS):
                    await self.expand_now2()

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
        # building = None
        # if building is None:
        #     # self.race is never Race.Random
        #     start_townhall_type = {Race.Protoss: unit.NEXUS, Race.Terran: unit.COMMANDCENTER,
        #                            Race.Zerg: unit.HATCHERY}
        building = unit.NEXUS#start_townhall_type[self.race]
        # assert isinstance(building, unit)

        location = await self.get_next_expansion2()
        if location is not None:
            await self.build(building, near=location, max_distance=5, random_alternative=False, placement_step=1)

    async def get_next_expansion2(self):
        """Find next expansion location."""
        closest = None
        distance = 99999

        def is_near_to_expansion(t):
            return t.position.distance_to(el) < 5

        for el in self.expansion_locations:
            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            # if self.mineral_field.closer_than(15, el).amount < 3:
            #     # almost out of minerals
            #     continue

            startp = self.structures(unit.NEXUS).closest_to(self.start_location)
            # d = await self._client.query_pathing(startp, el)
            # if d is None:
            #     continue
            d = startp.distance_to(el)
            if d < distance:
                distance = d
                closest = el
        return closest


def botVsComputer(real_time):
    maps_set = ['blink', "zealots", "Bandwidth", "Reminiscence", "TheTimelessVoid", "PrimusQ9", "Ephemeron",
                "Sanglune", "Urzagol"]
    training_maps = ["DefeatZealotswithBlink", "ParaSiteTraining"]
    races = [Race.Protoss, Race.Zerg, Race.Terran]
    # computer_builds = [AIBuild.Rush]
    computer_builds = [AIBuild.Macro, AIBuild.Power]
    build = random.choice(computer_builds)
    map_index = random.randint(0, 6)
    race_index = random.randint(0, 2)
    res = run_game(save_replay_as='replay999', map_settings=maps.get(maps_set[2]), players=[
        Bot(race=Race.Protoss, ai=Octopus(), name='Octopus'),
        Computer(race=races[1], difficulty=Difficulty.VeryHard, ai_build=build)
    ], realtime=bool(real_time))
    return res, build, races[race_index]


def test(real_time=0):
    results = []
    score_board = {Race.Protoss: {'win': {}, 'loose':{}}, Race.Zerg: {'win': {}, 'loose':{}},Race.Terran:
        {'win': {}, 'loose':{}}}
    win = 0
    loose = 0
    r = 1
    for i in range(r):
        try:
            result = botVsComputer(real_time)
            result_str = str(result[0]) + ' ' + str(result[2]) + ' ' + str(result[1])
            print(result_str)
            if result[0] == Result.Victory:
                if result[1] not in score_board[result[2]]['win'].keys():
                    score_board[result[2]]['win'][result[1]] = 1
                else:
                    score_board[result[2]]['win'][result[1]] += 1
                win += 1
            else:
                if result[1] not in score_board[result[2]]['loose'].keys():
                    score_board[result[2]]['loose'][result[1]] = 1
                else:
                    score_board[result[2]]['loose'][result[1]] += 1
                loose += 1
        except Exception as ex:
            print('Error.')
            print(ex)

    print('================= Results ===================')
    for res in results:
        print(res)
    print('=============================================')
    print('win: ' + str(win) + '/' + str(r))
    print('vs Protoss:')
    for key in score_board[Race.Protoss]['win']:
        print(str(key) + ': ' + str(score_board[Race.Protoss]['win'][key]) + ' / ' + str(score_board[Race.Protoss]['loose'][key]))
    print('vs Zerg:')
    for key in score_board[Race.Zerg]['win']:
        print(str(key) + ': ' + str(score_board[Race.Zerg]['win'][key]) + ' / ' + str(score_board[Race.Zerg]['loose'][key]))
    print('vs Terran: ')
    for key in score_board[Race.Terran]['win']:
        print(str(key) + ': ' + str(score_board[Race.Terran]['win'][key]) + ' / ' + str(score_board[Race.Terran]['loose'][key]))
    print('=============================================')


test(real_time=1)