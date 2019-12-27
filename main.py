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
from coords import coords as cd
from strategy.carrier_madness import CarrierMadness


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
                unit.HIGHTEMPLAR, unit.DISRUPTOR, unit.WARPPRISM, unit.VOIDRAY, unit.CARRIER]
    units_to_ignore = [unit.LARVA, unit.EGG]
    workers_ids = [unit.SCV, unit.PROBE, unit.DRONE]
    proper_nexus_count = 1
    army = []
    known_enemies = []
    game_map = None
    leader = None
    defend_position = None
    destination = None
    prev_nexus_count = 0
    coords = None

    strategy = None


    async def on_start(self):
        print('start loc: ' + str(self.start_location.position))
        self.coords = cd['map1'][self.start_location.position]
        self.strategy = CarrierMadness(self)

    async def on_end(self, game_result: Result):
        print('start pos: ' + str(self.start_location.position))
        for gateway in self.structures().exclude_type({unit.NEXUS, unit.ASSIMILATOR}):
            print(str(gateway.type_id)+' coords: ' + str(gateway.position))

    async def on_step(self, iteration):
        for enemy in self.enemy_units():
            if enemy.tag not in self.known_enemies:
                # print('new enemy!')
                self.known_enemies.append(enemy.tag)

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

        await self.twilight_council_build()
        # await self.robotics_facility()
        await self.stargate_build()
        # await self.make_forge()
        # await self.ramp_wall_build()
        await self.nexus_buff()
        await self.pylon_first_build()
        await self.pylon_next_build()
        await self.distribute_workers()
        await self.expand()
        self.train_workers()
        # counter attack
        if self.enemy_units().exists and self.enemy_units().closer_than(20, self.defend_position).amount > 2:
            self.enemy_attack = True
        if self.enemy_attack and self.enemy_units().amount < 5: # and self.enemy_units().closer_than(18, self.defend_position).amount < 4:
            self.enemy_attack = False
            self.after_first_attack = True
            self.attack = True
        if self.structures(unit.NEXUS).amount >= self.proper_nexus_count or self.already_pending(unit.NEXUS) or self.minerals > 400:
            await self.cybernetics_core_build()
            await self.build_gate()
            self.train_army()
            await self.warp_new_units()
            self.cybernetics_core_upgrades()
            self.build_assimilators()
        await self.morph_gates()

        if self.build_type == 'rush' and self.army.amount > 12 and not self.first_attack:
            self.first_attack = True
            self.attack = True
        if self.build_type == 'rush' and self.army.amount > 5:
            await self.proxy()
        await self.warp_prism()


        if self.attack and self.army.amount < (6 if self.build_type == 'rush' else 7):
            self.attack = False
        if self.attack:
            await self.attack_formation()
        else:
            await self.defend()
        await self.micro_units()

    async def start_step(self):
        pass

    async def make_forge(self):
        await self.strategy.forge_build()

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
        if self.forge_upg_priority() or self.build_type != 'macro' or self.time < 220:
            return

        if self.structures(unit.ROBOTICSFACILITY).amount < 1 and self.can_afford(unit.ROBOTICSFACILITY)\
                and not self.already_pending(unit.ROBOTICSFACILITY):
            pylon = self.get_proper_pylon()
            if pylon:
                await self.build(unit.ROBOTICSFACILITY,near=pylon,random_alternative=True,placement_step=2)
        elif self.structures(unit.ROBOTICSFACILITY).ready.exists and \
                self.units(unit.OBSERVER).amount + self.units(unit.OBSERVERSIEGEMODE).amount < 1 and \
                self.can_afford(unit.OBSERVER) and self.supply_left > 0:
            for factory in self.structures(unit.ROBOTICSFACILITY).ready.idle:
                self.do(factory.train(unit.OBSERVER))
                break
        elif self.attack and self.units(unit.WARPPRISMPHASING).amount + self.units(unit.WARPPRISM).amount < 1 \
                and self.can_afford(unit.WARPPRISM) and not self.already_pending(
            unit.WARPPRISM) and self.supply_left > 2:
            for factory in self.structures(unit.ROBOTICSFACILITY).ready.idle:
                self.do(factory.train(unit.WARPPRISM))
                break
        elif self.can_afford(unit.IMMORTAL) and self.supply_left > 3 and self.structures(unit.ROBOTICSFACILITY).ready.exists \
                and self.units(unit.IMMORTAL).amount < 8:
            for factory in self.structures(unit.ROBOTICSFACILITY).ready.idle:
                self.do(factory.train(unit.IMMORTAL))

    async def warp_prism(self):
        if self.attack:
            dist = self.enemy_start_locations[0].distance_to(self.game_info.map_center) * 0.75
            for warp in self.units(unit.WARPPRISM):
                if warp.distance_to(self.enemy_start_locations[0]) <= dist:
                    abilities = await self.get_available_abilities(warp)
                    if ability.MORPH_WARPPRISMPHASINGMODE in abilities:
                        self.do(warp(ability.MORPH_WARPPRISMPHASINGMODE))
        else:
            for warp in self.units(unit.WARPPRISMPHASING):
                abilities = await self.get_available_abilities(warp)
                if ability.MORPH_WARPPRISMTRANSPORTMODE in abilities:
                    self.do(warp(ability.MORPH_WARPPRISMTRANSPORTMODE))

    async def stargate_build(self):
        await self.strategy.stargate_build()

    async def defend(self):
        enemy = self.enemy_units()
        if enemy.exists:
            dist = 25
        else:
            dist = 6
        for man in self.army:
            if man.distance_to(self.defend_position) > dist:
                self.do(man.move(Point2(self.defend_position).random_on_distance(random.randint(1,3))))

    def assign_defend_position(self):
        nex = self.structures(unit.NEXUS)
        enemy = self.enemy_units()
        # start = self.start_location.position
        # self.defend_position = self.coords['defend_pos']
        self.defend_position = self.main_base_ramp.top_center.towards(self.main_base_ramp.bottom_center,-6)

        if self.prev_nexus_count != nex.amount or enemy.exists:
            if nex.amount < 2:
                self.defend_position = self.main_base_ramp.top_center.towards(self.main_base_ramp.bottom_center, -6)
            elif nex.amount == 2:

                self.defend_position = self.coords['defend_pos']
            else:
                min = 999
                ramp = None
                if enemy.exists and enemy.closer_than(50,self.start_location).amount > 0:
                    nex = nex.closest_to(enemy.closest_to(self.enemy_start_locations[0]))
                else:
                    nex = nex.furthest_to(self.start_location)
                p = nex.position.towards(Point2(self.coords['defend_pos']),7)
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
        # if self.can_afford(unit.SENTRY) and self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(
        #     unit.SENTRY).amount < 1:
        #     u = unit.SENTRY
        # elif self.can_afford(unit.STALKER) and self.structures(unit.CYBERNETICSCORE).ready.exists:
        #     u = unit.STALKER
        # elif self.can_afford(unit.ADEPT) and self.structures(unit.CYBERNETICSCORE).ready.exists and \
        #         self.army(unit.ADEPT).amount < 2:
        #     u = unit.ADEPT
        elif self.supply_left > 1 and self.minerals > 100 and self.units(unit.ZEALOT).amount < 3:
            u = unit.ZEALOT
        else:
            return
        gateway = gateway.ready.idle.random
        self.do(gateway.train(u))

    async def twilight_council_build(self):
        await self.strategy.twilight_build()

    async def proxy(self):
        if self.build_type == 'rush':
            pylons = self.structures(unit.PYLON)
            if pylons.exists:
                if pylons.further_than(40, self.start_location.position).amount == 0 and not\
                        self.already_pending(unit.PYLON):
                    pos = self.game_info.map_center.position.towards(self.enemy_start_locations[0], 25)
                    c=0
                    placement = None
                    while placement is None and c < 5:
                        c+=1
                        placement = await self.find_placement(unit.PYLON, near=pos, max_distance=20, placement_step=2,
                                                         random_alternative=False)
                    if placement is not None:
                        await self.build(unit.PYLON, near=placement)

    async def build_gate(self):
        await self.strategy.gate_build()

    async def pylon_first_build(self):
        await self.strategy.pylon_first_build()

    async def pylon_next_build(self):
        await self.strategy.pylon_next_build()

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
        self.strategy.assimilator_build()

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
                self.army(unit.IMMORTAL).amount < 4 or self.forge_upg_priority() or not self.structures(unit.WARPGATE).exists:
            return
        if self.attack:
            prisms = self.units(unit.WARPPRISMPHASING)
            if prisms.exists:
                pos = prisms.furthest_to(self.start_location).position
            else:
                furthest_pylon = self.structures(unit.PYLON).ready.furthest_to(self.start_location.position)
                pos = furthest_pylon.position.to2.random_on_distance(6)
        else:
            pos = self.structures(unit.PYLON).ready.closer_than(20,self.start_location).furthest_to(
                self.start_location).position.to2.random_on_distance(7)
        placement = None
        i = 0
        while placement is None:
            i += 1
            placement = await self.find_placement(ability.TRAINWARP_ADEPT, near=pos.random_on_distance(i),
                                                  max_distance=4, placement_step=2, random_alternative=False)
            if i > 5:
                print("can't find position for warpin.")
                return
        for warpgate in self.structures(unit.WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            if ability.WARPGATETRAIN_ZEALOT in abilities:
                if self.can_afford(unit.SENTRY) and self.units(unit.STALKER).amount > 7 and \
                        self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(unit.SENTRY).amount < 0:
                    self.do(warpgate.warp_in(unit.SENTRY,placement))
                elif self.can_afford(unit.STALKER) and self.supply_left > 1 and self.army(unit.STALKER).amount < 0:
                    self.do(warpgate.warp_in(unit.STALKER, placement))
                elif self.minerals > 150 and self.supply_left > 1 and \
                        self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(unit.ADEPT).amount < 0:
                    self.do(warpgate.warp_in(unit.ADEPT, placement))
                elif self.minerals > 400 and self.can_afford(unit.ZEALOT) and \
                        self.supply_left > 5 and self.units(unit.ZEALOT).amount < 20:
                    self.do(warpgate.warp_in(unit.ZEALOT, placement))

    async def nexus_buff(self):
        if not self.structures(unit.NEXUS).exists:
            return
        for nexus in self.structures(unit.NEXUS).ready:
            abilities = await self.get_available_abilities(nexus)
            if ability.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                target = self.structures().filter(lambda x: x.type_id == unit.NEXUS
                               and x.is_ready and not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                if target.exists:
                    target = target.random
                else:
                    target = self.structures().filter(lambda x: x.type_id == unit.CYBERNETICSCORE
                        and x.is_ready and not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                    if target.exists:
                        target = target.random
                    else:
                        target = self.structures().filter(lambda x: x.type_id == unit.FORGE and x.is_ready
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
        await self.strategy.cybernetics_build()

    def cybernetics_core_upgrades(self):
        cyber = self.structures(unit.CYBERNETICSCORE).ready.idle
        if cyber.amount > 0:
            if upgrade.WARPGATERESEARCH not in self.state.upgrades and not self.already_pending_upgrade(
                    upgrade.WARPGATERESEARCH) and self.can_afford(upgrade.WARPGATERESEARCH):
                self.do(cyber.random.research(upgrade.WARPGATERESEARCH))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL1 not in self.state.upgrades and self.can_afford(upgrade.PROTOSSAIRWEAPONSLEVEL1) and\
                not self.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL1):
                self.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL1))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL2 not in self.state.upgrades and self.can_afford(upgrade.PROTOSSAIRWEAPONSLEVEL2) and\
                not self.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL2):
                self.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL2))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL3 not in self.state.upgrades and self.can_afford(upgrade.PROTOSSAIRWEAPONSLEVEL3) and\
                not self.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL3):
                self.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL3))

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

        def chunk(lst,n):
            for i in range(0,len(lst),n):
                yield lst[i:i + n]
        # stalkers // mixed
        whole_army = self.army.exclude_type(unit.CARRIER)
        dist = 7
        group_size = 5
        c = int(len(whole_army) / group_size)
        chunks = c if c > 0 else 1
        part_army = chunk(whole_army, chunks)
        for army_l in part_army:
            army = Units(army_l, self)
            if army.exists:
                # leader = self.leader
                # if leader is None:
                if self.destination is not None:
                    leader = army.closest_to(self.destination)
                else:
                    leader = army.random
                threats = enemy.filter(
                    lambda unit_: unit_.can_attack_ground and unit_.distance_to(leader) <= dist and
                                  unit_.type_id not in self.units_to_ignore)
                if self.attack:
                    threats.extend(self.enemy_structures().filter(lambda x: x.can_attack_ground or x.type_id in
                                                                        [unit.NEXUS, unit.HATCHERY, unit.COMMANDCENTER]))
                if threats.exists:
                    closest_enemy = threats.closest_to(leader)
                    priority = threats.filter(lambda x: x.type_id in [unit.COLOSSUS, unit.DISRUPTOR, unit.HIGHTEMPLAR,
                        unit.MEDIVAC, unit.SIEGETANKSIEGED, unit.SIEGETANK, unit.THOR])
                    if priority.exists:
                        targets = priority.sorted(lambda x: x.health + x.shield)
                        if targets[0].health_percentage * targets[0].shield_percentage == 1:
                            target = priority.closest_to(leader)
                        else:
                            target = targets[0]
                    else:
                        targets = threats.sorted(lambda x: x.health + x.shield)
                        if targets[0].health_percentage * targets[0].shield_percentage == 1:
                            target = closest_enemy
                        else:
                            target = targets[0]
                    if target.distance_to(leader) > leader.distance_to(closest_enemy) + 4:
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

        # Carrier
        for cr in self.army(unit.CARRIER):
            threats = self.enemy_units().filter(lambda z: z.distance_to(cr) < 12 and z.type_id not in self.units_to_ignore)
            threats.extend(self.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                # target2 = None
                priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                if priority.exists:
                    # closest = priority.closest_to(cr)
                    # if cr.distance_to(closest) < 7:
                    #     self.do(cr.move(cr.position.towards(closest,-3)))
                    # else:
                    if priority.amount > 2:
                        priority = sorted(priority[:int(len(priority)/2)], key=lambda z: z.health+z.shield)
                    target2 = priority[0]
                else:
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    self.do(cr.attack(target2))

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
                if ability.EFFECT_CHARGE in await self.get_available_abilities(zl):
                    self.do(zl(ability.EFFECT_CHARGE, target))
                self.do(zl.attack(target))

    async def attack_formation(self):
        enemy_units = self.enemy_units()
        enemy = enemy_units.filter(lambda x: x.type_id not in self.units_to_ignore and x.can_attack_ground)
        if enemy.amount > 2:
            if enemy.closer_than(40, self.start_location).amount > 7:
                await self.defend()
                return
            if self.destination is not None:
                destination = enemy.closest_to(self.destination).position
            else:
                destination = enemy.closest_to(self.start_location).position
        elif self.enemy_structures().exists:
            enemy = self.enemy_structures()
            destination = enemy.closest_to(self.start_location).position
        else:
            enemy = None
            destination = self.enemy_start_locations[0].position

        start = self.army.closest_to(destination)
        self.destination = destination

        # point halfway
        dist = start.distance_to(destination)
        if dist > 40:
            point = start.position.towards(destination, dist / 2)
        else:
            point = destination
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
        _range = 7 if self.army.amount < 24 else 12
        nearest = self.army.closer_than(_range, start.position)
        if nearest.amount > self.army.amount * 0.70:
            for man in self.army:
                if enemy is not None and not enemy.in_attack_range_of(man).exists:
                    if man.type_id == unit.STALKER:
                        if not await self.blink(man, enemy.closest_to(man).position.towards(man.position, 6)):
                            self.do(man.attack(enemy.closest_to(man)))
                    else:
                        closest_en = enemy.closest_to(man)
                        self.do(man.attack(closest_en))
                elif enemy is None:
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
        await self.strategy.expand()


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


def botVsComputer(real_time):
    maps_set = ['blink', "zealots", "AcropolisLE", "DiscoBloodbathLE", "ThunderbirdLE", "TritonLE", "Ephemeron",
                "WintersGateLE", "WorldofSleepersLE"]
    training_maps = ["DefeatZealotswithBlink", "ParaSiteTraining"]
    races = [Race.Protoss, Race.Zerg, Race.Terran]
    # computer_builds = [AIBuild.Rush]
    # computer_builds = [AIBuild.Air]
    computer_builds = [AIBuild.Macro, AIBuild.Power]
    build = random.choice(computer_builds)
    # map_index = random.randint(0, 6)
    race_index = random.randint(0, 2)
    res = run_game(map_settings=maps.get(maps_set[2]), players=[
        Bot(race=Race.Protoss, ai=Octopus(), name='Octopus'),
        Computer(race=races[2], difficulty=Difficulty.VeryHard, ai_build=build)
    ], realtime=bool(real_time))
    return res, build, races[race_index]


if __name__ == '__main__':
    test(real_time=0)


