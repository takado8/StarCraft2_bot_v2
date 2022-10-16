import random, math, time

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units
from typing import List, Dict, Set, Tuple, Any, Optional, Union # mypy type checking
from sc2.ids.ability_id import AbilityId





class ANI_base_bot(sc2.BotAI):

    repair_group = []
    squad_group =[]
    kodinturvajoukot = []
    puuhapete = None
    remembered_puuhapete_by_tag = {}
    remembered_repair_group_by_tag = {}
    remembered_friendly_units_by_tag = {}
    remembered_squad_units_by_tag = {}
    remembered_kodinturvajoukot_by_tag = {}
    remembered_homeboys_by_tag = {}
    we_win = None

    def we_are_winning(self):
        enemy_health = 0
        our_health = 0
        units_to_ignore = [DRONE, SCV, PROBE]
        for unit in self.allEnemyUnits.exclude_type(units_to_ignore).filter(lambda x: x.can_attack_ground):
            enemy_health += (unit.health + unit.shield)
        for unit in self.units.exclude_type(units_to_ignore).filter(lambda x: x.can_attack_ground):
            our_health += unit.health
        if our_health > (1.8 * enemy_health):
            #print ("our health", our_health, "enemy_health", enemy_health)
            return True
        else:
            return False
            
    def remember_friendly_units(self):
    #goes throug every bot unit
    #saves .is_taking_damage True or False
        self.squad_group = sc2.units.Units([], self)
        self.kodinturvajoukot = sc2.units.Units([], self)
        self.homeboys = sc2.units.Units([], self)
        for unit in (self.units | self.structures(UnitTypeId.PLANETARYFORTRESS)):
            unit.is_taking_damage = False
            unit.did_take_first_hit = False
            unit.is_in_squad = False
            unit.is_in_kodinturvajoukot = False
            unit.is_in_homeboys = False

            # If we already remember this friendly unit
            if unit.tag in self.remembered_friendly_units_by_tag:
                health_old = self.remembered_friendly_units_by_tag[unit.tag].health
                health_percentage_old = self.remembered_friendly_units_by_tag[unit.tag].health_percentage

                # Compare its health/shield since last step, to find out if it has taken any damage
                if unit.health < health_old:
                    unit.is_taking_damage = True
                    if not health_percentage_old < 1:
                        unit.did_take_first_hit = True

            if unit.tag in self.remembered_homeboys_by_tag:
                unit.is_in_homeboys = True
                self.homeboys.append(unit)
            if unit.tag in self.remembered_squad_units_by_tag:
                unit.is_in_squad = True
                self.squad_group.append(unit)
            if unit.tag in self.remembered_kodinturvajoukot_by_tag:
                unit.is_in_kodinturvajoukot = True
                self.kodinturvajoukot.append(unit)

            #saves units tag
            self.remembered_friendly_units_by_tag[unit.tag] = unit



    def select_contractor(self, pos: Union[Unit, Point2, Point3], force: bool=False) -> Optional[Unit]:
        """Select a worker to build a bulding with."""

        workers = self.workers
        for worker in workers.sorted_by_distance_to(pos):
            if worker.is_puuhapete:
                continue 
            if worker.is_in_repair_group:
                continue 
            if ((len(worker.orders) == 1
                and worker.is_carrying_minerals
                and worker.orders[0].ability.id in {AbilityId.MOVE, AbilityId.HARVEST_RETURN})
            ):
                return worker

        return workers.random if force else None

    def threat_to_ground(self) -> "Units":
        visible = self.filter(lambda unit: unit.is_visible)
        return visible.filter(lambda unit: unit.can_attack_ground)

    async def marine_total(self):
        marineTotal = 0
        for barracks in self.units(BARRACKS).ready:
            for order in barracks.orders:
                if order.ability.id in [BARRACKSTRAIN_MARINE]:
                    marineTotal = marineTotal + 1
        marineTotal = marineTotal + self.units(MARINE).amount
        return marineTotal

    async def expand_now_ANI(self, building: UnitTypeId=None, max_distance: Union[int, float]=10, location: Optional[Point2]=None):
        """Takes new expansion."""

        if not building:
            # self.race is never Race.Random
            start_townhall_type = {Race.Protoss: UnitTypeId.NEXUS, Race.Terran: UnitTypeId.COMMANDCENTER, Race.Zerg: UnitTypeId.HATCHERY}
            building = start_townhall_type[self.race]

        assert isinstance(building, UnitTypeId)

        if not location:
            location = await self.get_next_expansion()
        if location == None:
            print("No expansions left")
            return False

        unit = self.select_contractor(location)
        if not unit:
            return False

        await self.build(building, near=location, max_distance=max_distance, build_worker=unit, random_alternative=False, placement_step=1)
        if self.chat_first_base == True and self.ccANDoc.amount == 1:
            print ("SCV: Building first expansion!")
            self.chat_first_base = False
        elif self.chat_second_base == True and self.ccANDoc.amount == 2:
            print("SCV: Building second expansion!")
            self.chat_second_base = False
        return True

    async def get_next_expansion(self) -> Optional[Point2]:
        """Find next expansion location."""

        startp = self._game_info.player_start_location


        if self.structures.exists:
            enemy_home = self.structures.furthest_to(self.start_location)
        closest = None
        distance = math.inf
        for el in self.expansion_locations:
            def is_near_to_expansion(t):
                return t.position.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            if not await self.can_place(COMMANDCENTER, el):
                continue

            if (self.enemy_units|self.enemy_structures).closer_than(10, el):
                continue

            if not self.mineral_field.closer_than(10, el):
                continue

            d = await self._client.query_pathing(startp, el)
            if d is None:
                continue

            if d < distance:
                distance = d
                closest = el

        return closest

    async def get_next_expansion_to_defend(self) -> Optional[Point2]:
        """Find next expansion location tp defend."""

        startp = self._game_info.player_start_location

        closest = None
        distance = math.inf
        for el in self.expansion_locations:
            def is_near_to_expansion(t):
                return t.position.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            if not await self.can_place(COMMANDCENTER, el) and self.structures.closer_than(8, el) and not self.enemy_structures.closer_than(8, el):
                continue

            if not self.mineral_field.closer_than(8, el):
                continue
            mineraldield_center = self.mineral_field.closer_than(8, el).center

            d = await self._client.query_pathing(startp, mineraldield_center)
            if d is None:
                continue

            if d < distance:
                distance = d
                closest = el

        return closest



    async def gather_gas_and_minerals(self):
        if not self.mineral_field:
            return
        """
        Stop long distance minig
        Send random worker to gather gas.
        Send idle scvs to gather minerals
        Send idle workers to mine closest base if no jobs available
        Relocate miners to base where is jobs available
        """
        townhalls = (self.townhalls(COMMANDCENTER).ready | self.townhalls(ORBITALCOMMAND) | self.townhalls(PLANETARYFORTRESS))
        scvs = self.workers()
        idle_workers = scvs.idle
        for refinery in self.gas_buildings:
            if self.enemy_units.closer_than(10, refinery):
                continue
            # stop long distance mining
            if refinery.assigned_harvesters != 0 and not townhalls.closer_than(10, refinery):
                for scv in self.scvs.filter(lambda x: x.is_carrying_vespene).closer_than(5, refinery):
                    target = scv.position.towards(self.game_info.map_center, 1)
                    self.do(scv.move(target))
                    return
            elif (self.vespene < self.minerals
                  and townhalls.closer_than(10, refinery)
                  and refinery.assigned_harvesters < refinery.ideal_harvesters and not self.home_in_danger):
                scvs = self.scvs.filter(lambda x: x.is_returning and x.is_carrying_minerals
                                                  and not x.is_in_repair_group
                                                  and not x.is_puuhapete)
                if scvs:
                    scv = random.choice(scvs)
                    self.do(scv.gather(refinery))
                    return

        # give job for idle scv
        for idle_worker in idle_workers:
            # gather minerals where jobs available
            townhalls_sorted = townhalls.sorted(lambda x: x.distance_to(idle_worker), reverse=False)
            for townhall in townhalls_sorted:
                if townhall.assigned_harvesters < townhall.ideal_harvesters and not self.allEnemyUnits.closer_than(10, townhall):
                    mf = self.mineral_field.closest_to(townhall)
                    self.do(idle_worker.gather(mf))
                    return

            # gather minerals from closest base
            for x in range (0, len(townhalls_sorted)):
                closest_mineral_field = self.mineral_field.closest_to(townhalls_sorted[x])
                if townhalls_sorted[x].distance_to(closest_mineral_field) < 10 and not self.allEnemyUnits.closer_than(10, townhall):
                    self.do(idle_worker.gather(closest_mineral_field))
                    return

        for townhall_out_of_jobs in townhalls:
            if townhall_out_of_jobs.assigned_harvesters > (townhall_out_of_jobs.ideal_harvesters):
                for townhall_jobs_available in townhalls:
                    if townhall_jobs_available.assigned_harvesters < townhall_jobs_available.ideal_harvesters:
                        scvs_carrying_minerals = scvs.filter(lambda x: x.is_carrying_minerals).closer_than(20,townhall_out_of_jobs)
                        if scvs_carrying_minerals:
                            scv_to_transfer = random.choice(scvs_carrying_minerals)
                            closest_mineral_field = self.mineral_field.closest_to(townhall_jobs_available)
                            self.do(scv_to_transfer.gather(closest_mineral_field))
                            return

    async def max_marine (self):
        maxmarine = 40 #max amount of marines
        return maxmarine

    def remember_repair_group (self):
    #manages units remembered_repair_group_by_tag
        self.repair_group = sc2.units.Units([], self)
        self.puuhapete = None
        for fixer in self.workers():
            if fixer.tag in self.remembered_repair_group_by_tag:
                fixer.is_in_repair_group = True
                self.repair_group.append(fixer)
            else:
                fixer.is_in_repair_group = False
            if fixer.tag in self.remembered_puuhapete_by_tag:
                fixer.is_puuhapete = True
                self.puuhapete = fixer
            else:
                fixer.is_puuhapete = False

    def add_unit_to_homeboys_group(self, unit):
    #adds units remembered_homeboys_by_tag
        self.remembered_homeboys_by_tag[unit.tag] = unit

    def add_unit_to_repair_group (self, fixer):
    #adds units remembered_repair_group_by_tag
        self.remembered_repair_group_by_tag[fixer.tag] = fixer

    def add_unit_to_squad_group (self, unit):
    #adds units remembered_squad_group_by_tag
        self.remembered_squad_units_by_tag[unit.tag] = unit

    def add_unit_to_kodinturvajoukot (self, unit):
    #adds units remembered_kodinturvajoukot_by_tag
        self.remembered_kodinturvajoukot_by_tag[unit.tag] = unit

    def assing_puuhapete (self, fixer):
    #adds units remembered_repair_group_by_tag
        self.remembered_puuhapete_by_tag[fixer.tag] = fixer
        
    async def can_take_expansion(self):
        # Must have a valid exp location
        location = await self.get_next_expansion()
        if location == None:
            return False

        # Must be able to find a valid building position
        if self.can_afford(COMMANDCENTER):
            position = await self.find_placement(COMMANDCENTER, location.rounded, max_distance=10, random_alternative=False, placement_step=1)
            if not position:
                return False
        return True

