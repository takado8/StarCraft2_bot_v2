import math
import random
from sc2 import run_game,maps,Race,Difficulty,Result, AIBuild
import sc2
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.player import Bot,Computer,Human

from sc2.ids.buff_id import BuffId as buff
from sc2.ids.upgrade_id import UpgradeId as upgrade


class Octopus(sc2.BotAI):
    enemy_main_base_down = False
    first_attack = False
    attack = False
    army_ids = [unit.ADEPT, unit.STALKER, unit.ZEALOT]
    units_to_ignore = [unit.LARVA, unit.EGG]
    workers_ids = [unit.SCV, unit.PROBE, unit.DRONE]
    proper_nexus_count = 1
    army = []

    def __init__(self):
        pass

    async def on_step(self, iteration):
        await self.nexus_buff()
        await self.first_pylon()
        await self.build_pylons()
        await self.distribute_workers()
        await self.expand()
        self.train_workers()

        if self.structures(unit.NEXUS).amount >= self.proper_nexus_count or self.already_pending(unit.NEXUS):
            await self.build_gate()
            self.train_army()
            await self.warp_new_units()
            await self.cybernetics_core_build()
            self.cybernetics_core_upgrades()
        self.build_assimilators()
        await self.morph_gates()
        self.army = self.units().filter(lambda x: x.type_id in self.army_ids)
        if (self.army.amount > 7 and not self.first_attack) or (self.first_attack and self.army.amount > 24):
            self.first_attack = True
            self.attack = True

        if self.attack and self.army.amount < 7:
            self.attack = False

        if self.attack:
            await self.attack_formation()
        else:
            self.defend()
        await self.micro_units()


    async def start_step(self):
        pass

    def defend(self):
        for man in self.army:
            if man.distance_to(self.start_location.position) > 30:
                self.do(man.move(self.start_location.position.random_on_distance(5)))

    def train_army(self):
        if self.minerals < 100:
            return
        if self.can_afford(unit.STALKER) and self.structures(unit.CYBERNETICSCORE).ready.exists:
            u = unit.STALKER
        # elif self.can_afford(unit.ADEPT) and self.structures(unit.CYBERNETICSCORE).ready.exists:
        #     u = unit.ADEPT
        elif self.supply_left > 1 and self.minerals > 300:
            u = unit.ZEALOT
        else:
            return
        for gateway in self.structures(unit.GATEWAY).ready.idle:
            self.do(gateway.train(u))

    async def build_gate(self):
        gates_count = self.structures(unit.GATEWAY).amount
        gates_count += self.structures(unit.WARPGATE).amount

        if gates_count < 2 and self.can_afford(unit.GATEWAY) and self.structures(unit.PYLON).ready.exists and\
                self.already_pending(unit.GATEWAY) < 1:
            pylon = self.get_proper_pylon()
            if pylon is None:
                print("Cannot find proper pylon for gateway")
                return
            await self.build(unit.GATEWAY, near=pylon, placement_step=2)
        elif 1 < gates_count < 3 and self.can_afford(unit.GATEWAY) and self.structures(unit.PYLON).ready.exists and\
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
                if self.structures(unit.NEXUS).idle.amount < nex:
                    return
                nexus = self.structures(unit.NEXUS).ready.idle.random
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
                            self.structures(unit.ASSIMILATOR).closer_than(1.0,vaspene).exists and self.time > 150):
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

                if self.can_afford(unit.STALKER) and self.supply_left > 1 and self.units(unit.STALKER).amount < 20:
                    placement = await self.find_placement(ability.WARPGATETRAIN_STALKER,pos,placement_step=1)
                    if placement is None:
                        print("can't place")
                        continue
                    self.do(warpgate.warp_in(unit.STALKER,placement))
                elif self.can_afford(unit.ADEPT) and self.supply_left > 1 and \
                        self.structures(unit.CYBERNETICSCORE).ready.exists and self.units(unit.ADEPT).amount < 7:
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

    async def micro_units(self):
        # stalkers
        stalkers = self.units().filter(lambda x: x.type_id == unit.STALKER)
        if stalkers.exists:
            for st in stalkers:
                threats = self.enemy_units().filter(
                        lambda unit_: unit_.can_attack_ground and unit_.distance_to(st) <= st.ground_range + st.radius and
                                      unit_.type_id not in self.units_to_ignore and unit_.type_id not in self.workers_ids)
                if threats.amount < 3:
                    enemy_workers = self.enemy_units().filter(lambda x: x.type_id in self.workers_ids and
                                                                        x.distance_to(st) < 7)
                    if enemy_workers.exists:
                        threats = enemy_workers
                if threats.exists:
                    closest_enemy = threats.closest_to(st)
                    target = closest_enemy
                    # prefer wounded enemy
                    threats = threats.sorted(lambda x: x.health)
                    if threats[0].distance_to(st) - target.distance_to(st) < 5:
                        target = threats[0]

                    enemy_range = closest_enemy.ground_range + closest_enemy.radius
                    if enemy_range < 4:
                        enemy_range = 4

                    if st.ground_range + st.radius >= enemy_range and (
                            st.weapon_cooldown > 0 and st.distance_to(closest_enemy) <= enemy_range):
                        place = None
                        dist = 0
                        pos = st.position.towards(self.game_info.map_center.position, 20)#target.position,-5)
                        # if await self._client.query_pathing(pos,target.position) is None:
                        #     pos = st.position.towards(target.position,st.distance_to(target) + target.ground_range + 5)
                        placement = None
                        while placement is None:
                            placement = await self.find_placement(unit.PYLON,pos,placement_step=1)
                        d = await self._client.query_pathing(placement,target.position)
                        if d is not None and d > dist:
                            place = placement

                        if not await self.blink(st,place):
                            self.do(st.move(place))
                    else:
                        self.do(st.attack(target))
        # zealot micro
        for zl in self.units(unit.ZEALOT):
            enemy = self.enemy_units().filter(lambda x: x.distance_to(zl) < 7 and not x.is_flying and
                                x.type_id not in self.workers_ids and x.type_id not in self.units_to_ignore)
            if enemy.amount < 3:
                enemy_workers = self.enemy_units().filter(lambda x: x.type_id in self.workers_ids and
                                                                    x.distance_to(zl) < 12)
                if enemy_workers.exists:
                    enemy = enemy_workers
            if enemy.exists:
                closest_enemy = enemy.closest_to(zl)
                target = closest_enemy
                # prefer wounded enemy
                threats = enemy.sorted(lambda x: x.health)
                if threats[0].distance_to(zl) - target.distance_to(zl) < 2:
                    target = threats[0]

                abilities = await self.get_available_abilities(zl)
                if ability.EFFECT_CHARGE in abilities:
                    self.do(zl(ability.EFFECT_CHARGE,target=target))
                else:
                    self.do(zl.attack(target))
        # adepts

        for ad in self.units(unit.ADEPT):
            enemy_workers = self.enemy_units().filter(lambda x: x.type_id in self.workers_ids and
                                                                x.distance_to(ad) < 12)
            if enemy_workers.exists:
                threats = enemy_workers
            else:
                threats = self.enemy_units().filter(lambda x: x.type_id in self.workers_ids and x.distance_to(ad) <= 5)
            if not threats.exists:
                threats = self.enemy_units().filter(
                    lambda unit_: unit_.can_attack_ground and unit_.distance_to(ad) <= ad.ground_range + ad.radius and
                                  unit_.type_id not in self.units_to_ignore)
            if threats.exists:
                closest_enemy = threats.closest_to(ad)
                target = closest_enemy
                # prefer wounded enemy
                threats = threats.sorted(lambda x: x.health)
                if threats[0].distance_to(ad) - target.distance_to(ad) < 2:
                    target = threats[0]

                enemy_range = closest_enemy.ground_range + closest_enemy.radius
                if enemy_range < 4:
                    enemy_range = 4

                if ad.ground_range + ad.radius >= enemy_range and (
                        ad.weapon_cooldown > 0 and ad.distance_to(closest_enemy) <= enemy_range):
                    place = None
                    dist = 0
                    pos = ad.position.towards(target.position, -5)
                    if await self._client.query_pathing(pos, target.position) is None:
                        pos = ad.position.towards(target.position, ad.distance_to(target) + target.ground_range + 5)
                    placement = None
                    while placement is None:
                        placement = await self.find_placement(unit.PYLON, pos, placement_step=1)
                    d = await self._client.query_pathing(placement, target.position)
                    if d is not None and d > dist:
                        place = placement

                    if not await self.blink(ad, place):
                        self.do(ad.move(place))
                else:
                    self.do(ad.attack(target))

    async def attack_formation(self):
        army_ids = [unit.ZEALOT, unit.STALKER, unit.ADEPT]
        army = self.units().filter(lambda unit_: unit_.type_id in army_ids)
        if not self.enemy_main_base_down:
            if self.time > 1800 and army.closer_than(10,self.enemy_start_locations[0]).amount > 12:
                self.enemy_main_base_down = True  # ugly fix of army getting stuck on enemy location when almost win.

            if army.closer_than(15,self.enemy_start_locations[0].position).amount > 5 and \
                    self.enemy_structures().closer_than(20,self.enemy_start_locations[0].position).amount < 4:
                # await self.observe()
                self.enemy_main_base_down = True

            enemy_units = self.enemy_units()

            if enemy_units.exists:
                enemy_in_my_base = enemy_units.closer_than(30, self.start_location.position)
                enemy_on_his_side = self.enemy_units().further_than(80, self.main_base_ramp.top_center)
            else:
                enemy_in_my_base = None
                enemy_on_his_side = None
            if enemy_in_my_base is not None and enemy_in_my_base.amount > 7:
                destination = enemy_in_my_base.closest_to(self.start_location.position)
                enemy = enemy_in_my_base
            elif enemy_on_his_side is not None and enemy_on_his_side.exists:
                enemy = enemy_on_his_side.filter(lambda x: x.type_id not in self.units_to_ignore and (
                                                                   x.can_attack_ground or x.can_attack_air))
                # workers = enemy.filter(lambda x: x.type_id in self.workers_ids)
                # if workers.exists:
                #     enemy = workers
                if not enemy.exists:
                    enemy = enemy_on_his_side
                destination = enemy.closest_to(self.start_location.position)
            elif self.enemy_structures().exists:
                enemy = self.enemy_structures()
                destination = enemy.closest_to(self.start_location.position)

            else:
                enemy = None
                destination = self.enemy_start_locations[0].position
            start = army.exclude_type({unit.OBSERVER}).closest_to(destination)
            # point halfway
            dist = start.distance_to(destination)
            if dist > 20:
                point = start.position.towards(destination,dist / 4)
            elif dist > 10:
                point = start.position.towards(destination,dist / 2)
            else:
                point = destination.position
            position = None
            i = 0
            while position is None:
                position = await self.find_placement(unit.PYLON,near=point,max_distance=30,placement_step=1,
                                                     random_alternative=False)
                i += 1
                if i > 10:
                    print("can't find position for army.")
                    return
            # if everybody's here, we can go
            _range = 7
            nova = self.enemy_units(unit.DISRUPTORPHASED)
            nova.extend(self.units(unit.DISRUPTORPHASED))
            nearest = army.closer_than(_range,start.position)
            exclude = [unit.DISRUPTOR,unit.DARKTEMPLAR]

            if nearest.amount > army.amount * 0.75:
                for man in army:
                    # if man.is_idle:
                    if nova.exists:
                        nova = nova.closer_than(2,man)
                        if nova.exists:
                            self.do(man.move(man.position.towards(nova.closest_to(man),-1)))
                            continue
                    if enemy is not None and not enemy.in_attack_range_of(
                            man).exists:  # man.is_idle and ## man.distance_to(start) < 9 and
                        if man.type_id == unit.STALKER:
                            if await self.blink(man,enemy.closest_to(man).position.towards(man.position,6)):
                                continue
                        if man.type_id in exclude:
                            continue
                        else:
                            closest_en = enemy.closest_to(man)
                            self.do(man.attack(closest_en))
                    else:
                        # if not man.is_attacking:
                        self.do(man.move(position))
            else:
                # center = nearest.center
                for man in army.filter(lambda man_: man_.distance_to(start) > 7 and not man_.is_attacking):
                    self.do(man.move(start))
        else:
            enemies = self.enemy_units()
            if enemies.exists:
                for man in army.idle:
                    if not enemies.in_attack_range_of(man).exists:
                        self.do(man.attack(enemies.closest_to(man)))

    async def blink(self, stalker, target):
        abilities = await self.get_available_abilities(stalker)
        if ability.EFFECT_BLINK_STALKER in abilities:
            self.do(stalker(ability.EFFECT_BLINK_STALKER,target))
            return True
        else:
            return False

    async def expand(self):
        gates_count = self.structures(unit.GATEWAY).amount
        gates_count += self.structures(unit.WARPGATE).amount
        if gates_count < 1:
            return
        nexuses = self.structures(unit.NEXUS).ready
        if nexuses.amount < 2 and self.attack or self.proper_nexus_count == 2:
            self.proper_nexus_count = 2
            if self.can_afford(unit.NEXUS) and not self.already_pending(unit.NEXUS):
                await self.expand_now2()
        elif 3 > nexuses.amount > 1 and self.units(
                unit.PROBE).amount >= 34:  # and len(self.army) > 9:
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
            if totalExcess > 1 and not self.already_pending(unit.NEXUS):
                self.proper_nexus_count = 4
                if self.can_afford(unit.NEXUS):
                    await self.expand_now2()
            elif self.proper_nexus_count == 4:
                self.proper_nexus_count = 3

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
    maps_set = ["CrystalCavern","Bandwidth","Reminiscence","TheTimelessVoid","PrimusQ9","Ephemeron",
                "Sanglune","Urzagol"]
    training_maps = ["DefeatZealotswithBlink","ParaSiteTraining"]
    races = [sc2.Race.Protoss, sc2.Race.Zerg, sc2.Race.Terran]
    map_index = random.randint(0, 6)
    race_index = random.randint(0, 2)
    run_game(map_settings=maps.get(maps_set[3]),players=[
        Bot(race=Race.Protoss, ai=Octopus(), name='Octopus'),
        Computer(race=races[1], difficulty=Difficulty.Harder)
    ], realtime=True)



botVsComputer()