import asyncio
import random, math
import sc2
import time
import argparse
from sc2 import run_game, Race, maps, Difficulty
from sc2.player import Bot, Computer, Human
from sc2.constants import *
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units
from ANI_base_bot import ANI_base_bot
from sc2.client import Client
from sc2 import Race
from trainingdata import TrainingData as trainingData
from sc2.game_state import GameState


# maps for prpbots DiscoBloodbathLE, EphemeronLE, Triton LE,
# Winter’s Gate LE, World of Sleepers LE, Acropolis LE, Thunderbird LE

# noinspection PyUnresolvedReferences
class ANIbot(ANI_base_bot):
    chat = True
    build_one_liberator = False
    upgrade_liberator = False
    first_base_saturation = -2
    refineries_in_first_base = 1  # note: refineries slow down first expansion!
    scv_limit = 70  # 60
    scv_build_speed = 2
    greedy_scv_consrtuction = False
    BuildReapers = True
    reapers_left = 3
    FastReaper = False
    MaxGhost = 2
    NukesLeft = 5  # max 10. If used 11 or more changes many variables
    raven_left = 3
    mines_left = 4
    agressive_mines = False
    leapfrog_mines = False
    cyclone_left = 0
    liberator_left = 0
    hellion_left = 0
    researsh_blueflame = False  # upgrades infernaligniter.
    banshee_left = 4
    upgrade_banshee = False
    min_marine = 8  # try keep this amount of marines
    max_marine = 36
    marine_drop = False
    marines_last_resort = False
    max_thor = 4
    max_BC = 4
    max_viking = 5
    adaptive_viking_count = False
    delay_vikings = False
    viking_landing_delay = 0
    maxsiege = 5
    faster_tanks = False
    max_barracks = 2  # maxamount of barracks
    delay_barracs = False  # makes only one barracks until starport pending
    barracks_reactor_first = False
    maxfactory = 2
    max_starports = 3
    build_starportreactor = False
    max_engineeringbays = 1
    fast_engineeringbay = True
    build_armory = True
    maxmarauder = 6
    can_assault = True
    scan_enemy_base = False
    careful_marines = False
    build_missile_turrets = True
    mineral_field_turret = False
    build_bunker = True  # if chosen, then build bunker in first expansion after barracks
    mech_build = False
    min_thors_to_attack = 1
    expand_for_vespene = True
    fast_vespene = False
    fast_orbital = True  # slow orbital makes first OC after first expansion is pending
    upgrade_marine = True
    upgrade_mech = True
    upgrade_vehicle_weapons = True
    maxmedivacs = 3
    barracks_switch = False
    wall_in = False
    wall_tank = False
    wall_tank_pos = None
    build_priority_cyclone = False
    limit_vespene = False
    fast_hellions = False
    minimum_repairgroup = 1
    nuke_enemy_home = False
    activate_all_mines = False
    build_planetaries = False
    scan_cloaked_enemies = False
    more_depots = False

    # game state variables
    target_of_assault = None
    ReapersDone = False
    rush_possible = True
    can_surrender = False
    last_phase = False
    last_iteration = 0
    iteraatio = 0
    last_turn = 0
    start = 0
    enemy_natural = None
    scout_sent = False
    send_scout = False
    chat_once_1 = True
    chat_once_mine = True
    chat_first_base = True
    chat_second_base = True
    canSiege = True
    load_dropship = False
    dropship_sent = False
    banshee_target_location = None
    viking_target_location = None
    enemy_has_air2air_units = False
    anti_air_unit_location = None
    enemy_air_unit_location = None
    midle_depo_position = None
    home_in_danger = False
    liberator_timer = 0
    new_strategy = False
    remembered_fired_mines_by_tag = {}
    gatekeeper = None




    def __init__(self):
        self.strategy = 0
        self._training_data = trainingData()
        self.opp_id = self.findOppId()
        self.enemy_start_location = None
        self.clear_result = True
        self.nuke_timer = 0
        self.fallout_zone = []
        self.slow_cycle_timer = 0
        self.last_iter = 0
        self.delay_first_expansion = False
        self.super_greed = False
        self.bonus_scv_in_start = 0
        self.real_time = False
        self.last_game_loop = -10
        self.doner_location = None
        self.research_stimpack = True
        self.defence_radius = 0
        self.lowest_health_viking_tag = None
        self.natural = None
        self.ramps = None
        self.all_ramp_top_centers = []
        self.all_ramp_bottom_centers = []
        self.natural_ramp_top_center = None


    async def on_step(self, iteration):

        if not self.real_time and self.state.game_loop - self.last_game_loop < 4:
            self.real_time = True
            self.chat = False
            # await self._client.chat_send("Meatbag detected.", team_only=False)
            print("Playing against meatbag")
            self._client.game_step = 1  # Real time mode activated!
            return
        elif self.real_time and self.state.game_loop - self.last_game_loop < 4:
            return
        #print(self.state.game_loop - self.last_game_loop)

        self.last_game_loop = self.state.game_loop
        self.defence_radius = self.start_location.distance_to(self.game_info.map_center)

        await self.cashe_units_fast_cycle()
        self.homeBase = None
        await self.get_homeBase()
        if not self.homeBase:
            return
        await self.move_reapers()
        await self.move_marines()
        self.slow_cycle_timer += 1
        if self.slow_cycle_timer < 2:
            return
        else:
            self.slow_cycle_timer = 0
        await self.cashe_units()

        #        print((time.time()-self.start)*1000)
        self.start = time.time()
        self.nuke_timer -= 1

        await self.cashe_effects()
        await self.remember_enemy()
        if self.structures.amount < 3 and self.scvs.amount <= 3:
            if self.clear_result:
                self.clear_result = False
                self._training_data.removeResult(self.opp_id)
            if self.can_surrender:
                await self._client.chat_send("pineapple", team_only=False)
                self.can_surrender = False
        if not self.last_phase and self.supply_used > 130:
            if self.vikings_total.amount >= self.max_viking:
                self.last_phase = True

        if self.enemy_start_location == None:
            distance = math.inf
            if self.enemy_structures.exists:
                enemy_home = self.enemy_structures.furthest_to(self.start_location)
                enemy_start_point = self.enemy_start_locations[0]
                distance = enemy_start_point.distance_to(enemy_home)
                for x in range(0, len(self.enemy_start_locations)):
                    location = self.enemy_start_locations[x]
                    if location.distance_to(enemy_home) < distance:
                        distance = location.distance_to(enemy_home)
                        enemy_start_point = location.position
                self.enemy_start_location = enemy_start_point

        thorTotal = 0
        siegeTotal = 0
        for factory in self.factories.ready:
            for order in factory.orders:
                order_id = order.ability.id
                if order_id in [AbilityId.FACTORYTRAIN_THOR]:
                    thorTotal += 1
                elif order_id in [AbilityId.FACTORYTRAIN_SIEGETANK]:
                    siegeTotal += 1
        thorTotal += self.thors.amount
        siegeTotal += (self.siegetanks.amount + self.siegetanks_sieged.amount)

        self.remember_repair_group()
        if self.puuhapete == None and self.scvs.amount > 0:
            print("Assigning new handyman")
            new_puuhapete = random.choice(self.scvs)
            if new_puuhapete:
                self.assing_puuhapete(new_puuhapete)

        units_to_ignore = [ADEPTPHASESHIFT, MULE, DRONE, SCV, PROBE, EGG, LARVA, OVERLORD, OVERSEER, OBSERVER,
                           BROODLING, INTERCEPTOR, MEDIVAC, CREEPTUMOR, CREEPTUMORBURROWED, CREEPTUMORQUEEN,
                           CREEPTUMORMISSILE]
        units_to_ignore_ghost = [ADEPTPHASESHIFT, ZERGLING, INFESTEDTERRANSEGG, MULE, DRONE, SCV, PROBE, EGG, LARVA,
                                 OVERLORD, OBSERVER, BROODLING, INTERCEPTOR, MEDIVAC, CREEPTUMOR, CREEPTUMORBURROWED,
                                 CREEPTUMORQUEEN, CREEPTUMORMISSILE]
        units_to_ignore_marine = [ADEPTPHASESHIFT, EGG, LARVA]
        ##        if self.supply_used > 170:
        ##            maxscv = self.scv_limit - 20
        ##        else:
        if self.ccANDoc.amount == 1:
            maxscv = 30
        else:
            maxscv = self.scv_limit + self.bonus_scv_in_start + 1
        maxbarracks = self.max_barracks
        if self.delay_barracs and self.starports.amount == 0:
            maxbarracks = 1
        if self.minerals > 450 and not self.expand_for_vespene and self.ccANDoc.amount > 2:
            if self.limit_vespene:
                maxbarracks += 5
            else:
                maxbarracks += 4
        #elif self.already_pending(BARRACKS) and not self.FastReaper:
        #    maxbarracks = maxbarracks - 1
        if not self.BuildReapers:
            maxreaper = 0
        elif self.FastReaper:
            maxreaper = 3  # max amount reapers reaper opening
        else:
            maxreaper = 1  # max amount of reapers when enemy location is known (scout)
        self.canSiege = True

        ## scout control
        if self.puuhapete:
            if self.scout_sent:
                if self.rush_possible and self.ccANDoc.amount == 1:
                    # if enemy has expanded there is no money for rush.
                    if self.puuhapete.distance_to(self.enemy_natural) < 10:
                        if self.enemy_structures.closer_than(5, self.enemy_natural):
                            await self._client.chat_send("No one base all in -> greedy mode activated.", team_only=False)
                            if self.strategy == 3:
                                self.max_engineeringbays = 2
                            self.super_greed = True
                            self.more_depots = True
                            self.rush_possible = False
                            self.build_bunker = False
                            self.last_phase = True
                            self.wall_tank = False
                            self.wall_in = False
                            self.fast_engineeringbay = False
                            self.scv_build_speed = 3
                            mf = self.mineral_field.closest_to(self.start_location)
                            self.do(self.puuhapete.gather(mf))
                        else:
                            self.scan_enemy_base = True
                            if self.chat_once_1:
                                self.chat_once_1 = False
                                if self.chat:
                                    await self._client.chat_send("Possible one base all in.", team_only=False)
                                self.refineries_in_first_base = 2
                                self.first_base_saturation = 3
                                self.wall_tank = True
                                self.wall_in = True
                                self.upgrade_mech = True
                if (self.first_base_saturation != 4
                        and self.enemy_structures.closer_than(self.defence_radius, self.start_location)):
                    self.first_base_saturation = 4
                    self.refineries_in_first_base = 2
                    self.wall_in = True
                    if self.enemy_race != Race.Protoss:
                        self.wall_tank = True
                    if self.chat:
                        await self._client.chat_send("Proxy build detected -> Turtle mode activated.", team_only=False)

        ## continue construction and scout
        if self.iteraatio % 3 == 0 and self.puuhapete and not self.home_in_danger:
            allOwnBuildings = self.structures.exclude_type(
                [REACTOR, TECHLAB, BARRACKSTECHLAB, BARRACKSREACTOR, FACTORYTECHLAB, FACTORYREACTOR, STARPORTTECHLAB,
                 STARPORTREACTOR])
            for building in allOwnBuildings:
                if (building.health_percentage < 1
                        and await self.has_ability(CANCEL_BUILDINPROGRESS, building)
                        and not await self.has_ability(HALT_BUILDING, building)):
                    if building.health_percentage < 1 / 6:
                        self.do(building(AbilityId.CANCEL_BUILDINPROGRESS))
                        print("Building cancelled")
                    elif await self.has_ability(SMART, self.puuhapete):
                        self.do(self.puuhapete(AbilityId.SMART, building))
            if self.barracks.ready and not self.scout_sent and self.send_scout and not self.puuhapete.is_carrying_minerals:
                enemy_mineral_fields = self.mineral_field.closer_than(10, (self.enemy_natural))
                enemy_mineral_field_1 = enemy_mineral_fields.furthest_to(self.enemy_start_location).position.towards(self.enemy_natural, -6)
                enemy_mineral_field_2 = enemy_mineral_fields.closest_to(self.enemy_start_location).position.towards(self.enemy_natural, -6)
                self.do(self.puuhapete.move(enemy_mineral_field_1, queue = True))
                self.do(self.puuhapete.move(enemy_mineral_field_2, queue = True))
                if self.chat:
                    await self._client.chat_send("Scout sent.", team_only=False)
                self.scout_sent = True
            if self.techlabs_and_reactors.amount > 1 and not self.barracks_switch:
                self.do(self.puuhapete.attack(self.techlabs_and_reactors.closest_to(self.puuhapete)))

        # ravens
        for raven in self.units(RAVEN):
            if await self.avoid_own_nuke(raven):
                continue
            if self.allEnemyUnits.filter(lambda x: x.can_attack_air).closer_than(11, raven):
                target = raven.position.towards(self.allEnemyUnits.closest_to(raven), 2).random_on_distance(1)
                if raven.energy >= 50:
                    self.do(raven(AbilityId.BUILDAUTOTURRET_AUTOTURRET, target.position))
                    continue
                else:
                    self.do(raven.move(self.homeBase.position))
                    continue
            if self.banshees:
                self.do(raven.move(self.banshees.center))
                continue
            if self.general:
                if self.enemy_start_location:
                    target_position = self.general.position.towards(self.enemy_start_location, 2)
                else:
                    target_position = self.general.position
                if raven.distance_to(target_position) > 2:
                    self.do(raven.attack(target_position))
                    continue

        ## fix broken things
        units_in_repair_group = 0
        outpost = await self.get_outpost()
        new_fixer = None
        for fixer in self.scvs:
            if fixer.is_in_repair_group:
                units_in_repair_group += 1
        if (units_in_repair_group < self.minimum_repairgroup
                or ((self.wall_in or self.ccANDoc.amount >= 4) and units_in_repair_group < 4)):
            possible_fixers = self.scvs.filter(lambda x: x.is_carrying_minerals and not x.is_puuhapete)
            if possible_fixers:
                new_fixer = random.choice(possible_fixers)
            if new_fixer:
                self.add_unit_to_repair_group(new_fixer)
                print("New fixer assigned")
        repailable_units = (self.vikingassault |
                            self.hellions.closer_than(15, outpost) |
                            self.hellions.closer_than(15, self.homeBase) |
                            self.hell_bats |
                            self.cyclones.closer_than(15, self.homeBase) |
                            self.siegetanks |
                            self.mines_burrowed |
                            self.siegetanks_sieged |
                            self.medivacs.closer_than(15, self.homeBase) |
                            self.battlecruisers.closer_than(15, self.homeBase) |
                            self.structures.exclude_type([TECHLAB, REACTOR]) |
                            self.thors)
        if self.repair_group.exists and self.iteraatio % 5 == 0:
            potilaat = repailable_units.ready.filter(lambda x: x.health_percentage < 1)
            if potilaat.exists:
                for fixer in self.repair_group:
                    potilas = potilaat.closest_to(fixer)
                    if self.wall_in:
                        wall = self.structures(UnitTypeId.SUPPLYDEPOT).filter(lambda x: x.health_percentage < 1)
                        if wall:
                            potilas = wall.sorted(lambda x: x.health_percentage, reverse=False)[0]
                    self.do(fixer(EFFECT_REPAIR_SCV, potilas))
            elif self.supply_used > 170 and self.general:
                for fixer in self.repair_group:
                    if fixer.distance_to(self.general) > 10:
                        self.do(fixer.move(self.general.position))

        ## ghost reporting
        max_energy = 0
        nuke_ordered = False
        for ghost in self.ghosts:
            ghost.can_nuke = False
            ghost.next_in_line = False
            if len(ghost.orders) >= 1:
                if ghost.orders[0].ability.id in [AbilityId.TACNUKESTRIKE_NUKECALLDOWN]:
                    nuke_ordered = True
            if ghost.energy > max_energy and ghost.health_percentage > 0.8:
                max_energy = ghost.energy
        for ghost in self.ghosts:
            if ghost.energy == max_energy and await self.has_ability(TACNUKESTRIKE_NUKECALLDOWN, ghost):
                ghost.next_in_line = True
                if not nuke_ordered:
                    ghost.can_nuke = True

        for ghost in self.ghosts:
            ghost_range = ghost.ground_range + ghost.radius
            ghost_EMP_range = self._game_data.abilities[AbilityId.EMP_EMP.value]._proto.cast_range
            ghost_SNIPE_range = self._game_data.abilities[AbilityId.EFFECT_GHOSTSNIPE.value]._proto.cast_range
            # print("emp range", ghost_EMP_range) # = 10
            # print("SNIPE range", ghost_SNIPE_range) # = 10
            potential_targets_EMP = None
            # if self.enemy_race == Race.Protoss:
            #     targets_for_EMP = self.allEnemyUnits.not_structure.filter(lambda x: x.shield > 50)
            #     potential_targets_EMP = targets_for_EMP.closer_than(ghost_EMP_range, ghost)
            # else:
            #     potential_targets_EMP = None
            targets_for_snipe = self.allEnemyUnits.not_structure.exclude_type(units_to_ignore_ghost).filter(
                lambda x: x.is_biological)
            potential_targets = targets_for_snipe.closer_than(11, ghost)
            known_enemies = self.allEnemyUnits.not_structure
            if await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKOFF_GHOST):
                detectors = (self.enemy_units|self.enemy_structures).filter(lambda x: x.is_detector)
                if detectors.closer_than(12, ghost) and ghost.distance_to(self.homeBase) > 20:
                    self.do(ghost.move(self.homeBase.position))
                    continue
            if len(ghost.orders) >= 1:
                if ghost.orders[0].ability.id in [AbilityId.TACNUKESTRIKE_NUKECALLDOWN]:
                    if ghost.health_percentage < 1 and self.medivacs:
                        self.do(ghost.move(self.homeBase.position))
                        continue
                    if (await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKON_GHOST)
                            and self.allEnemyUnits.filter(lambda x: x.can_attack_ground).closer_than(20, ghost)):
                        self.do(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))
                    continue
            if await self.avoid_own_nuke(ghost):
                continue
            if await self.avoid_enemy_siegetanks(ghost):
                continue
            if ghost.can_nuke and await self.has_ability(TACNUKESTRIKE_NUKECALLDOWN, ghost):
                if self.nuke_enemy_home:
                    if ghost.energy > 70 and await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKON_GHOST):
                        target = self.enemy_start_location
                        self.do(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target.position))
                        self.nuke_enemy_home = False
                        print("NUKE")
                        return
                # elif (self.enemy_units_on_ground.closer_than(20, ghost)
                #       and not self.enemy_units_on_ground.closer_than(ghost_range + ghost.radius, ghost)
                #       and self.NukesLeft >= 10):
                #     target = self.enemy_units_on_ground.closest_to(ghost)
                #     self.do(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target.position.towards(ghost, 3)))
                #     print("NUKE")
                #     return
                elif (self.enemy_structures.exists
                      and ghost.energy > 70
                      and await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKON_GHOST)):
                    target = random.choice(self.enemy_structures)
                    self.do(ghost(AbilityId.TACNUKESTRIKE_NUKECALLDOWN, target.position))
                    print("NUKE")
                    return
            if ghost.weapon_cooldown != 0:
                self.do(ghost.move(self.homeBase.position))
                continue
            if (ghost.health_percentage < 1 and await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKON_GHOST)
                    and self.allEnemyUnits.filter(lambda x: x.can_attack_ground).closer_than(20, ghost)
                    and self.medivacs):
                self.do(ghost(AbilityId.BEHAVIOR_CLOAKON_GHOST))
                continue
            elif not ghost.next_in_line:
                if known_enemies.closer_than(9, ghost):
                    if potential_targets_EMP and ghost.energy >= 75:
                        potential_targets_EMP = potential_targets_EMP.sorted(lambda x: (x.shield), reverse=True)
                        target = potential_targets_EMP[0]
                        self.do(ghost(AbilityId.EMP_EMP, target.position))
                        print("Ghost: EMP")
                        continue
                    if potential_targets and ghost.energy >= 50:
                        potential_targets = potential_targets.sorted(lambda x: (x.health + x.shield), reverse=True)
                        target = potential_targets[0]
                        self.do(ghost(AbilityId.EFFECT_GHOSTSNIPE, target))
                        print("Ghost: SNIPE", target.type_id)
                        continue
                if targets_for_snipe and ghost.energy >= 50:
                    target = targets_for_snipe.closest_to(ghost)
                    self.do(ghost.attack(target.position))
                    continue
            light_enemies_in_range = known_enemies.closer_than(ghost_range + ghost.radius, ghost).filter(lambda x: x.is_light)
            if light_enemies_in_range:
                enemies_in_range_sorted = light_enemies_in_range.sorted(lambda x: (x.health + x.shield), reverse=True)
                target = enemies_in_range_sorted[0]
                self.do(ghost.attack(target))
                continue
            if await self.can_cast(ghost, AbilityId.BEHAVIOR_CLOAKOFF_GHOST):
                if not self.enemy_units.closer_than(20, ghost):
                    self.do(ghost(AbilityId.BEHAVIOR_CLOAKOFF_GHOST))
                    continue
            if known_enemies and ghost.health_percentage >= 1:
                self.do(ghost.attack(known_enemies.closest_to(ghost)))
                continue
            # if self.general:
            #     if ghost.distance_to(self.general.position) > 10:
            #         self.do(ghost.move(self.general.position))
            #         continue
            if ghost.position.to2.distance_to(self.homeBase.position.to2) > 10:
                self.do(ghost.move(self.homeBase.position))
                continue  # continue for loop, dont execute any of the following

        ## bunkers
        if self.bunkers.ready and self.marines and self.bunkers.ready.amount < 6:
            for bunker in self.bunkers.ready:
                if await self.has_ability(LOAD_BUNKER, bunker):
                    marines = self.marines.closer_than(5, bunker)
                    if marines:
                        self.do(bunker(AbilityId.LOAD_BUNKER, marines.closest_to(bunker)))
                        continue  # continue for loop, dont execute any of the following

        if self.iteraatio % 3 == 0:
            await self.safkaa()
        await self.build_refinery()

        """
        Calculate available jobs
        scvs in refinery are not counted as scvs!
        add one scv for every full refinery
        """
        harvesters = 0
        if self.ccANDoc.ready.amount == 1:
            jobs = self.first_base_saturation
            if self.allEnemyUnits.closer_than(30, self.homeBase).amount > 2:
                self.delay_first_expansion = True
            if self.delay_first_expansion:
                jobs += 3
        else:
            jobs = 0
        for cc in (self.ccANDoc):
            jobs += cc.ideal_harvesters
            harvesters += cc.assigned_harvesters

        if self.marine_drop and not self.dropship_sent:
            we_need_to_expand = False
        elif (jobs <= harvesters and not self.already_pending(COMMANDCENTER) and self.barracks):
            we_need_to_expand = True
        else:
            we_need_to_expand = False

        can_build = True
        can_build_workes = not we_need_to_expand

        # super green forces to expand to 3 bases before building military
        if self.super_greed and self.ccANDoc.amount < 2:
            if self.minerals > 400:
                await self.expand_now_ANI()
            can_build = False
        elif self.super_greed and self.barracks:
            if self.ccANDoc.amount > 2:
                self.super_greed = False
            if self.minerals > 400:
                await self.expand_now_ANI()
            can_build = False
        elif not self.rush_possible and (self.ccANDoc.amount + self.townhalls_flying.amount) < 3:  # rush not iminent
            if self.mech_build and self.ccANDoc.amount == 1 and not self.already_pending(COMMANDCENTER):
                await self.build_cc_at_home()
            elif self.allEnemyUnits.amount < 3:
                if self.minerals > 400:
                    await self.expand_now_ANI()
                can_build = False
        elif self.marine_drop:
            can_build = await self.manage_drop()
        elif self.build_priority_cyclone:
            can_build = await self.build_priority_cyclones()
        elif self.wall_tank:
            can_build = await self.build_priority_tank()

        if can_build and self.scvs:
            # this makes bunker before expansion
            if self.build_bunker and not self.already_pending(BUNKER) and not self.bunkers and we_need_to_expand:
                can_build = await self.build_bunker_to_next_expansion(self.scvs.random)
                can_build_workes = False
            elif (self.fast_orbital
                  and self.barracks.ready
                  and self.ccANDoc.amount == 1
                  and not self.already_pending(UnitTypeId.ORBITALCOMMAND)
                  #and we_need_to_expand
                  and self.cc.ready):
                can_build_workes = True
                if self.minerals > 150:
                    for cc in self.cc.ready.idle:
                        if cc.health_percentage < 1:
                            continue
                        self.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))
                        print("up grade orbital")
                        can_build_workes = False
                can_build = False
            elif (we_need_to_expand
                  and (self.ccANDoc.amount + self.townhalls_flying.amount) == 1
                  and not self.already_pending(COMMANDCENTER)):
                can_build = False
                if self.greedy_scv_consrtuction:
                    can_build_workes = True
                else:
                    can_build_workes = False
                if self.wall_in and self.minerals > 400:
                    await self.build_cc_at_home()
                elif self.minerals > 400:
                    await self.expand_now_ANI()
            elif (self.barracks.ready and self.cc.ready.idle and self.ccANDoc.amount > 1 and not self.super_greed):
                if (((self.orbitalcommand.amount >= 2 and self.structures(PLANETARYFORTRESS).amount == 0)
                     or self.build_planetaries)
                        and self.engineeringbays.ready.exists
                        and not self.mech_build
                        and not self.already_pending(PLANETARYFORTRESS)):
                    for cc in self.cc.ready.idle:
                        if await self.has_ability(UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS, cc):
                            self.do(cc(AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS))
                            print("up grade planetary fortress")
                elif self.minerals > 150:
                    if (self.build_planetaries):
                        pass
                    else:
                        for cc in self.cc.ready.idle:
                            self.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))
                            print("up grade orbital")
                if (self.build_planetaries and not self.engineeringbays.ready):
                    can_build = True
                    can_build_workes = True
                else:
                    can_build = False
                    can_build_workes = False
            elif (we_need_to_expand
                  and not self.already_pending(COMMANDCENTER)
                  and not self.already_pending(ORBITALCOMMAND)
                  and not self.already_pending(PLANETARYFORTRESS)):
                can_build = False
                can_build_workes = False
                await self.expand_now_ANI()
            elif (not self.already_pending(COMMANDCENTER)
                    and self.expand_for_vespene
                    and (self.vespene + 700) < self.minerals
                    and self.ccANDoc.amount > 1
                    and not self.already_pending(REFINERY)):
                print("building commandcenter for vespene")
                await self.expand_now_ANI()
            elif self.minerals > 2000 and not self.already_pending(UnitTypeId.COMMANDCENTER) and self.expand_for_vespene:
                await self.expand_now_ANI()



        if can_build_workes:
            await self.build_workers(maxscv)
        if can_build and self.scvs:
            if await self.train_liberator():
                if (await self.do_research()
                        or self.enemy_units.closer_than(self.defence_radius, self.homeBase).amount > 1):
                    await self.buildings(maxbarracks, iteration)
                    await self.military_units(maxreaper, maxbarracks)
        elif self.enemy_units.closer_than(self.defence_radius,self.homeBase).amount > 1:
            await self.military_units(maxreaper, maxbarracks)
        await self.landbuildings()
        await self.evac_orbital()
        await self.call_for_mules()
        if self.build_planetaries:
            await self.repair_planetaries()
        await self.raise_lower_depots()
        await self.move_scvs(),
        await self.move_squad(),
        await self.move_vikings(),
        await self.move_thors(),
        await self.move_banshees(),
        await self.move_liberators(),
        await self.move_hellions_and_hellbats(),
        if not self.marine_drop:
            await self.move_medivacs(),
        await self.move_mines(),
        await self.move_battle_ruiser(),
        await self.move_tanks(),
        await self.move_cyclones(),
        await self.move_marauders(),

        # remove wall_in parameters
        if self.wall_in:
            if self.townhalls_flying or self.ccANDoc.amount > 3 or self.supply_used > 100:
                self.wall_in = False

        if self.iteraatio == 0:
            self.natural = await self.get_next_expansion()


            self.ramps = self.game_info.map_ramps
            for ramp in self.game_info.map_ramps:
                if self.main_base_ramp.top_center != ramp.top_center:
                    self.all_ramp_top_centers.append(ramp.top_center)
                    self.all_ramp_bottom_centers.append(ramp.bottom_center)
            #print(self.all_ramp_top_centers)
            # natural_ramp = self.closest_ramp_to(unit)
            # for pos in self.all_ramp_top_centers:
            #     print(self.natural.position.distance_to(pos))

            self._client.game_step = 4
            if len(self.enemy_start_locations) == 1:
                self.enemy_start_location = self.enemy_start_locations[0]
                self.enemy_natural = await self.get_enemy_natural()

            "Load previous tactics that worked agains this opponent"
            if not self.opp_id:
                if self.enemy_race == Race.Zerg:
                    self.opp_id = "liskot"
                elif self.enemy_race == Race.Protoss:
                    self.opp_id = "avaruusmiehet"
                elif self.enemy_race == Race.Terran:
                    self.opp_id = "ihmiset"
                else:
                    self.opp_id = "satunnainen"
            print('playing vs', self.opp_id)
            self._training_data.loadData()
            # find out which strat we want to use.
            self.strategy = self._training_data.findStrat(self.opp_id)
            "save strategy as victory, and remove if defeated"
            self._training_data.saveVictory(self.opp_id, self.strategy)

            """hardcoded strategies for opponents"""
            # if self.opp_id == "d4f4776b-f4dd-4cdc-bb29-18f28c016c66":  # MicroMachine
            #     print("Opponent: MicroMachine")
            #     self.strategy = 9 # Fast cyclone
            #     self._training_data.removeResult(self.opp_id)
            if self.opp_id == "54bca4a3-7539-4364-b84b-e918784b488a":  # Jensiiibot
                print("Opponent: Jensiiibot")
                self.strategy = 5 # Air superiority
                self._training_data.removeResult(self.opp_id)

            """
            chose tactics from 1 to 10
            1 = Greed
            2 = Reaper opening
            3 = Terran Bio
            4 = Mech build
            5 = Air superiority
            6 = Nuke rain
            7 = No starport
            8 = marine drop
            9 = Fast cyclone
            10 = Minefields
            """
            #self.strategy = 9 # 2020
            #self.strategy = random.randint(1,10)

            if self.strategy == 1:  # Greed
                self.super_greed = True
                self.more_depots = True
                self.greedy_scv_consrtuction = False
                self.scan_enemy_base = True
                self.scv_build_speed = 3
                self.raven_left = 0
                self.fast_orbital = False
                self.first_base_saturation = 0
                self.scv_limit = 70
                self.build_one_liberator = False
                self.bonus_scv_in_start = 20
                self.build_bunker = False
                self.max_BC = 50
                self.last_phase = True
                self.can_assault = True
                self.BuildReapers = False
                self.maxmarauder = 50
                self.MaxGhost = 0
                self.expand_for_vespene = False
                self.mines_left = 2
                self.cyclone_left = 0
                self.hellion_left = 0
                self.banshee_left = 0
                self.liberator_left = 0
                self.maxsiege = 2
                self.max_viking = 0
                self.max_barracks = 4
                self.barracks_reactor_first = True
                self.maxfactory = 1
                self.max_starports = 4
                self.build_starportreactor = False
                self.maxmedivacs = 4
                self.min_marine = 2  # try keep this amount of marines
                self.max_marine = 100
                self.research_stimpack = False
                self.marines_last_resort = False
                self.upgrade_vehicle_weapons = False
                self.max_engineeringbays = 1
                self.careful_marines = True
                self.build_missile_turrets = True
                self.max_thor = 0
                self.NukesLeft = 0
            elif self.strategy == 2:  # Reaper opening
                self.first_base_saturation = 0
                self.fast_orbital = False
                self.refineries_in_first_base = 2
                self.greedy_scv_consrtuction = True
                self.FastReaper = True
                self.cyclone_left = 1
                self.mines_left = 0
                self.hellion_left = 3
            elif self.strategy == 3:  # Terran Bio
                self.scv_build_speed = 2
                self.first_base_saturation = 0
                self.fast_orbital = True
                self.refineries_in_first_base = 2
                self.fast_vespene = True
                self.limit_vespene = True
                self.expand_for_vespene = False
                self.wall_in = False
                self.wall_tank = False
                self.mines_left = 0
                self.build_one_liberator = False
                self.upgrade_mech = False
                self.build_bunker = False
                self.scv_limit = 65
                self.send_scout = True
                self.greedy_scv_consrtuction = False
                self.cyclone_left = 0
                self.max_barracks = 4
                self.delay_barracs = True
                self.MaxGhost = 0
                self.maxfactory = 1
                self.max_starports = 1
                self.build_starportreactor = False
                self.barracks_reactor_first = False
                self.barracks_switch = False
                self.BuildReapers = False
                self.min_marine = 20
                self.max_marine = 100
                self.marines_last_resort = False
                self.maxmarauder = 20
                self.maxsiege = 6
                self.faster_tanks = True
                self.raven_left = 0
                self.maxmedivacs = 5
                self.banshee_left = 0
                self.hellion_left = 0
                self.max_viking = 2
                self.adaptive_viking_count = False
                self.liberator_left = 6
                self.upgrade_liberator = True
                self.max_thor = 0
                self.max_BC = 0
                self.fast_engineeringbay = True
                self.build_armory = True
                self.NukesLeft = 0
                self.careful_marines = True
                self.max_engineeringbays = 1
                self.fast_hellions = False
            elif self.strategy == 4:  # Mech build
                self.first_base_saturation = 3
                self.refineries_in_first_base = 1
                self.scv_limit = 70
                self.scv_build_speed = 1
                self.bonus_scv_in_start = 0
                self.more_depots = False
                self.send_scout = True
                self.fast_orbital = False
                self.BuildReapers = False
                self.mech_build = True
                self.wall_in = True
                self.wall_tank = True
                self.fast_engineeringbay = True
                self.min_marine = 1  # try keep this amount of marines
                self.max_marine = 4  # absolute maximum
                self.marines_last_resort = True
                self.MaxGhost = 0
                self.hellion_left = 100
                self.researsh_blueflame = True
                self.upgrade_marine = False
                self.max_barracks = 1
                self.barracks_reactor_first = False
                self.maxfactory = 5
                self.max_starports = 1
                self.careful_marines = False
                self.banshee_left = 0
                self.max_viking = 3
                self.liberator_left = 4
                self.maxmedivacs = 0
                self.mines_left = 0
                self.maxsiege = 12
                self.cyclone_left = 20
                self.max_thor = 8
                self.max_BC = 10
            elif self.strategy == 5:  # Air superiority, counter for Jensiii
                self.super_greed = False
                self.build_bunker = True
                self.wall_in = False
                self.wall_tank = False
                self.refineries_in_first_base = 1
                self.first_base_saturation = 0
                self.build_one_liberator = False
                self.fast_orbital = True
                self.scv_limit = 70
                self.bonus_scv_in_start = 10
                self.max_viking = 5
                self.adaptive_viking_count = False
                self.banshee_left = 16
                self.liberator_left = 0
                self.upgrade_liberator = False
                self.raven_left = 100
                self.hellion_left = 0
                self.upgrade_banshee = True  # researsh banshee cloak and hyper rotors. delays  banshee production
                self.upgrade_vehicle_weapons = False
                self.max_thor = 0
                self.maxsiege = 6
                self.faster_tanks = True # added this to defense against Jensiibot
                self.delay_vikings = False # Should this be added against Jensii?
                self.cyclone_left = 0
                self.upgrade_marine = False
                self.max_barracks = 2
                self.maxfactory = 1
                self.max_starports = 4
                self.build_starportreactor = True
                self.barracks_switch = False
                self.barracks_reactor_first = True
                self.min_marine = 2  # try keep this amount of marines
                self.max_marine = 50
                self.maxmarauder = 8
                self.last_phase = False
                self.max_engineeringbays = 1
                self.fast_engineeringbay = False
                self.MaxGhost = 0
                self.NukesLeft = 0
            elif self.strategy == 6:  # Nuke rain
                self.scv_limit = 80
                self.scv_build_speed = 1
                self.first_base_saturation = 0
                self.refineries_in_first_base = 1
                self.limit_vespene = False
                self.build_bunker = False
                self.wall_in = False
                self.wall_tank = False
                self.fast_engineeringbay = True
                self.build_planetaries = True
                self.scan_cloaked_enemies = True
                self.fast_orbital = True
                self.scan_enemy_base = False
                self.raven_left = 100
                self.expand_for_vespene = False
                self.max_barracks = 4
                self.delay_barracs = True
                self.maxfactory = 1
                self.upgrade_mech = False
                self.max_starports = 1
                self.build_starportreactor = True
                self.banshee_left = 0
                self.maxsiege = 5
                self.min_marine = 6  # try keep this amount of marines
                self.max_marine = 100
                self.maxmarauder = 4
                self.MaxGhost = 16
                self.mines_left = 0
                self.cyclone_left = 1
                self.hellion_left = 0
                self.NukesLeft = 100
                self.nuke_enemy_home = True
                self.barracks_reactor_first = True
                self.max_thor = 0
                self.max_BC = 0
                self.max_viking = 2
            elif self.strategy == 7:  # No Starport
                self.scv_limit = 90
                self.first_base_saturation = 4
                self.refineries_in_first_base = 2
                self.BuildReapers = False
                self.wall_in = True
                self.wall_tank = True
                self.build_bunker = False
                self.max_barracks = 3
                self.maxfactory = 5
                self.max_starports = 0
                self.mines_left = 0
                self.maxsiege = 8
                self.min_marine = 8  # try keep this amount of marines
                self.max_marine = 100
                self.maxmarauder = 12
                self.MaxGhost = 4
                self.max_thor = 2
                self.cyclone_left = 2
                self.hellion_left = 0
                self.researsh_blueflame = False
                self.research_stimpack = False
                self.expand_for_vespene = False
                self.scan_enemy_base = True
                self.nuke_enemy_home = True
            elif self.strategy == 8:  # marine drop
                self.first_base_saturation = 0
                self.max_barracks = 2
                self.barracks_reactor_first = True
                self.min_marine = 8
                self.max_marine = 50
                self.maxmarauder = 10
                self.MaxGhost = 1
                self.maxsiege = 8
                self.max_thor = 0
                self.liberator_left = 4
                self.upgrade_liberator = True
                self.max_BC = 5
                self.delay_barracs = False
                self.marine_drop = True
                self.fast_orbital = False
                self.expand_for_vespene = False
                self.maxfactory = 2
                self.faster_tanks = True
                self.max_starports = 2
                self.build_starportreactor = True
                self.mines_left = 0
                self.cyclone_left = 0
                self.banshee_left = 0
                self.upgrade_banshee = False
                self.max_viking = 14
            elif self.strategy == 9:  # Fast cyclone
                self.scv_limit = 90
                self.greedy_scv_consrtuction = True
                self.first_base_saturation = 2
                self.refineries_in_first_base = 2
                self.build_priority_cyclone = True
                self.raven_left = 4
                self.BuildReapers = True
                self.max_barracks = 1
                self.maxfactory = 3
                self.max_starports = 2
                self.build_starportreactor = False
                self.min_marine = 2  # try keep this amount of marines
                self.max_marine = 50
                self.MaxGhost = 0
                self.hellion_left = 0
                self.cyclone_left = 6
                self.maxsiege = 4
                self.max_thor = 9
                self.barracks_reactor_first = True
                self.expand_for_vespene = False
                self.marines_last_resort = True
                self.fast_orbital = False
                self.fast_engineeringbay = False
                self.build_bunker = False
                self.build_missile_turrets = True
                self.mineral_field_turret = True
                self.can_surrender = False
                self.mines_left = 0
                self.banshee_left = 4
                self.max_viking = 5
                self.delay_vikings = True
                self.maxmedivacs = 0
                self.upgrade_marine = False
                self.minimum_repairgroup = 2
            else:  # Minefields
                self.build_one_liberator = False
                self.upgrade_liberator = True
                self.first_base_saturation = 0
                self.refineries_in_first_base = 1  # note: refineries slow down first expansion!
                self.scv_limit = 70
                self.bonus_scv_in_start = 0
                self.BuildReapers = True
                self.FastReaper = False
                self.MaxGhost = 0
                self.raven_left = 100
                self.mines_left = 100
                self.agressive_mines = True
                self.leapfrog_mines = True
                self.cyclone_left = 100
                self.hellion_left = 0
                self.banshee_left = 0
                self.upgrade_banshee = False
                self.min_marine = 0  # try keep this amount of marines
                self.max_marine = 100
                self.marine_drop = False
                self.marines_last_resort = True
                self.max_thor = 0
                self.max_BC = 0
                self.max_viking = 1
                self.maxmedivacs = 2
                self.liberator_left = 10
                self.maxsiege = 3
                self.max_barracks = 1  # maxamount of barracks
                self.barracks_reactor_first = False
                self.delay_barracs = False  # makes only one barracks until starport pending
                self.maxfactory = 2
                self.max_starports = 1
                self.build_starportreactor = False
                self.max_engineeringbays = 1
                self.fast_engineeringbay = False
                self.maxmarauder = 8
                self.can_assault = True
                self.scan_enemy_base = True
                self.careful_marines = True
                self.build_missile_turrets = False
                self.mineral_field_turret = True
                self.build_bunker = False  # if chosen, then build bunker in first expansion after barracks
                self.NukesLeft = 0  # max 10. If used 11 or more changes many variables
                self.mech_build = False
                self.expand_for_vespene = False
                self.fast_orbital = False  # slow orbital makes first OC after first expansion is pending
                self.upgrade_marine = True
                self.upgrade_vehicle_weapons = False

        if self.chat:
            if self.iteraatio == 10:
                await self._client.chat_send("ANI 14.2.2020. GLHF!", team_only=False)
            if self.iteraatio == 50:
                if self.strategy == 1:
                    await self._client.chat_send("Greed", team_only=False)
                    print("Strat: Greed")
                elif self.strategy == 2:
                    await self._client.chat_send("Strategy: Reaper opening", team_only=False)
                    print("Strat: Reaper opening")
                elif self.strategy == 3:
                    await self._client.chat_send("Strategy: Terran Bio", team_only=False)
                    print("Strat: Terran Bio")
                elif self.strategy == 4:
                    await self._client.chat_send("Strategy: Mech build", team_only=False)
                    print("Strat: Mech build")
                elif self.strategy == 5:
                    await self._client.chat_send("Strategy: Air superiority", team_only=False)
                    print("Strat: Air superiority")
                elif self.strategy == 6:
                    await self._client.chat_send("Strategy: Nuke rain", team_only=False)
                    print("Strat: Nuke rain")
                elif self.strategy == 7:
                    await self._client.chat_send("Strategy: No Starport", team_only=False)
                    print("Strat: No Starport")
                elif self.strategy == 8:
                    await self._client.chat_send("Strategy: Marine drop", team_only=False)
                    print("Strat: Marine drop")
                elif self.strategy == 9:
                    await self._client.chat_send("Strategy: Fast cyclone", team_only=False)
                    print("Strat: Fast cyclone")
                else:
                    await self._client.chat_send("Strategy: Minefields", team_only=False)
                    print("Strat: Minefields")

        self.iteraatio += 1

    async def search_for_proxy(self, unit):
        ##        for x in self.expansion_locations:
        ##            print(x)
        ##        for x in self.expansion_locations:
        ##            print(self.expansion_locations[x])

        possible_proxy_locations = sorted(self.expansion_locations.keys(),
                                          key=lambda p: p.distance_to(self.start_location), reverse=False)
        self.do(unit.move(possible_proxy_locations[3], queue=True))
        self.do(unit.move(possible_proxy_locations[2], queue=True))
        self.do(unit.move(possible_proxy_locations[1], queue=True))

    async def cashe_effects(self):
        efektit = self.state.effects
        for effect in efektit:
            if effect.id in [EffectId.NUKEPERSISTENT]:
                self.nuke_timer = 10
                self.fallout_zone = []
        for effect in efektit:
            if effect.id in [EffectId.NUKEPERSISTENT]:
                for position in effect.positions:
                    self.fallout_zone.append(position)
        ##        if self.fallout_zone:
        ##            print(self.fallout_zone)
        if self.nuke_timer <= 0:
            self.fallout_zone = []

    async def avoid_enemy_siegetanks(self, unit):
        if not self.starports:
            return False
        if self.enemy_units.of_type(SIEGETANKSIEGED).closer_than(17, unit):
            self.do(unit.move(self.homeBase.position))
            return True
        else:
            return False

    async def build_bunker_to_next_expansion(self, unit):
        if self.barracks.ready:  # This makes bunker
            bunker_location = await self.get_next_expansion()
            if bunker_location != None :
                if self.can_afford(BUNKER):
                    bunker_location = bunker_location.towards(self.game_info.map_center, 7).random_on_distance(2)
                    await self.build(BUNKER, near=bunker_location.position,
                                     build_worker=self.select_contractor(bunker_location))
                    print("building bunker")
                return False
        return True


    async def avoid_own_nuke(self, unit):
            if not self.fallout_zone:
                return False

            for position in self.fallout_zone:
                if unit.distance_to(position) < 11:
                    ##                print("Avoid NUKE")
                    self.do(unit.move(self.homeBase.position))
                    return True
            return False

    async def get_waypoint_for_dropship(self):
        wayPoints = await self.neighbors4(self.enemy_start_location, distance=40)
        wayPoints = sorted(wayPoints, key=lambda x: x.distance_to(self.game_info.map_center))
        if wayPoints[0].distance_to(self.enemy_natural) < wayPoints[1].distance_to(self.enemy_natural):
            return wayPoints[1]
        else:
            return wayPoints[0]

    # stolen from mass_reaper.py
    async def neighbors4(self, position, distance=1):
        p = position
        d = distance
        return [
            Point2((p.x - d, p.y)),
            Point2((p.x + d, p.y)),
            Point2((p.x, p.y - d)),
            Point2((p.x, p.y + d)),
        ]

    "build barracks, barracks reactor and factory"
    async def build_priority_cyclones(self):

        # wait for barracks to be ready
        if not self.barracks.ready.exists:
            return True
        elif self.marines.amount < 1 and not self.already_pending(MARINE):
            for barracks in self.barracks.idle:
                self.do(barracks.train(MARINE))
            return False

        if self.minerals > 300 and not self.already_pending(SUPPLYDEPOT) and self.supplydepots.amount == 1:
            expand = random.choice(self.supplydepots)
            await self.build(SUPPLYDEPOT, near=expand.position.random_on_distance(10),
                             build_worker=self.select_contractor(expand))
            print("Building priority supplydepot")

        "build factory"
        if ((not self.factories and not self.factoriesflying)
                and not self.already_pending(FACTORY)
                and (self.barracks.ready.exists or self.barracksflyings)):
            if self.can_afford(FACTORY):
                if self.doner_location and await self.can_place(FACTORY, self.doner_location):
                    await self.build(FACTORY, self.doner_location)
                    return False
                await self.build_for_me(FACTORY)
            return False

        """Build techlab"""
        if (not self.structures(TECHLAB)
              and not self.structures(FACTORYTECHLAB)
              and not self.structures(BARRACKSTECHLAB)
              and not self.already_pending(BARRACKSTECHLAB)):
                if self.can_afford(BARRACKSTECHLAB):
                    for barracks in self.barracks:
                        addonlocation = barracks.position.offset((2.5, -0.5))
                        if await self.can_place(SUPPLYDEPOT, addonlocation):
                            self.do(barracks.build(BARRACKSTECHLAB))
                        else:
                            self.do(barracks(LIFT))
                return False

        if self.structures(BARRACKSTECHLAB).ready:
            for barracks in self.barracks.ready:
                for lab in self.structures(BARRACKSTECHLAB).ready:
                    if barracks.add_on_tag == lab.tag:
                        self.doner_location = barracks.position
                        self.do(barracks(LIFT))

        "move factory to techlab"
        if (self.factories.ready
                and self.doner_location
                and not self.structures(FACTORYTECHLAB)
                and not self.already_pending(FACTORYTECHLAB)
                and self.doner_location):
            for factory in self.factories:
                self.do(factory(LIFT))
            return False
        for factory in self.factoriesflying:
            self.do(factory(LAND, self.doner_location))

        if self.structures(FACTORYTECHLAB) and self.doner_location:
            self.doner_location = None


        "build one cyclone"
        if (self.factories.ready
                and not self.already_pending(CYCLONE)
                and not self.cyclones
                and self.structures(FACTORYTECHLAB).ready):
            for factory in self.factories.ready:
                if not self.can_feed(CYCLONE):
                    return True
                if (self.can_afford(CYCLONE)):
                    self.do(factory.train(CYCLONE))
                    self.build_priority_cyclone = False
                    print("Training priority cyclone")
                    break
                return False

        return True

    async def find_potential_construction_locations(self, location):
        p = location.position
        return [
            Point2((p.x - 7, p.y)),
            Point2((p.x + 7, p.y)),
            Point2((p.x, p.y + 5)),
            Point2((p.x, p.y - 5)),
            Point2((p.x - 7, p.y + 5)),
            Point2((p.x - 7, p.y - 5)),
            Point2((p.x + 7, p.y - 5)),
            Point2((p.x + 7, p.y + 5)),
        ]

    async def find_potential_construction_locations_in_home(self, location):
        p = location.position
        return [
            Point2((p.x - 7, p.y + 5)),
            Point2((p.x - 7, p.y - 5)),
            Point2((p.x + 5, p.y + 5)),
            Point2((p.x + 5, p.y - 5)),
        ]

    async def pathing_points(self, location):
        p = location.position
        list = []
        for a in range(-3, 4):
            for b in range(0, 2):
                list.append(Point2((p.x + a, p.y + b)))
        #print(len(list))
        return list

    async def building_leaves_pathing_for_units(self, location):
        pathing_available = True
        place = location.position.offset((0, -3))
        if not self.in_pathing_grid(place):
            pathing_available = False
        if not pathing_available:
            pathing_available = True
            needs_to_be_free = await self.pathing_points(location.position.offset((0, 2)))
            for place in needs_to_be_free:
                if not self.in_pathing_grid(place):
                    pathing_available = False
                    break
        return pathing_available

    async def can_have_addon_in_this_location(self, location):
        addonlocation = location.position.offset((3, 0))
        return await self.can_place(BARRACKS, addonlocation)

    async def find_placement_for_barracks(self):
        for structure in (self.barracks | self.factories | self.starports
                          | self.engineeringbays | self.armories
                          | self.ghost_academies | self.fusioncores):
            potential_construction_locations = await self.find_potential_construction_locations(structure)
            for location in potential_construction_locations:
                if (await self.can_place(BARRACKS, location)
                        and await self.can_have_addon_in_this_location(location)
                        #and await self.building_leaves_pathing_for_units(location)
                ):
                    print("Found place for structure around existing buildings.")
                    return location
        for structure in self.ccANDoc:
            potential_construction_locations = await self.find_potential_construction_locations_in_home(structure)
            for location in potential_construction_locations:
                if (await self.can_place(BARRACKS, location)
                        and await self.can_have_addon_in_this_location(location)
                        #and await self.building_leaves_pathing_for_units(location)
                ):
                    print("Found place for structure around CC.")
                    return location
        print("Did not find place for structure around existing buildings.")
        return None

    async def build_for_me(self, structure_type):
        structure_location = await self.find_placement_for_barracks()
        if not structure_location and self.supplydepots:
            expand = random.choice(self.supplydepots)
            structure_location = await self.find_placement(UnitTypeId.BARRACKS,
                                                         near=expand.position.random_on_distance(10))
            if structure_location and not await self.can_have_addon_in_this_location(structure_location):
                print("Warning: No room for add_on!")
                return
        if structure_location:
            await self.build(structure_type, structure_location,
                             build_worker=self.select_contractor(structure_location))
            print("Building", structure_type)


    async def build_priority_tank(self):
        # builds barracks -> factory -> tank
        # tank sieges behind wall
        # return true -> continue with normal production

        # wait for barracks to be ready
        if not self.barracks.ready.exists:
            return True
        if (not self.already_pending(BARRACKS)
                and self.barracks.amount < 1
                and self.minerals > 300):
            await self.build_for_me(BARRACKS)
        elif self.marines.amount < 2 and not self.already_pending(MARINE):
            for barracks in self.barracks.idle:
                self.do(barracks.train(MARINE))
            return False

        elif (not self.structures(TECHLAB)
              and not self.structures(FACTORYTECHLAB)
              and not self.structures(BARRACKSTECHLAB)
              and not self.already_pending(BARRACKSTECHLAB)):
            if self.can_afford(BARRACKSTECHLAB):
                for barracks in self.barracks.idle:
                    self.do(barracks.build(BARRACKSTECHLAB))
            return False

        elif (not self.structures(TECHLAB)
              and not self.structures(FACTORYTECHLAB)
              and self.structures(BARRACKSTECHLAB).ready):
            for barracks in self.barracks:
                for addon in self.structures(BARRACKSTECHLAB):
                    if barracks.add_on_tag == addon.tag:
                        self.doner_location = barracks.position
                        print("doner location", self.doner_location)
                        self.do(barracks(LIFT))

        "build factory immediately after BarracksTechlab"
        if ((not self.factories and not self.factoriesflying)
                and not self.already_pending(FACTORY)
                and (self.barracks.ready.exists or self.barracksflyings)):
            if self.can_afford(FACTORY):
                if self.doner_location:
                    if await self.can_place(FACTORY, self.doner_location):
                        await self.build(FACTORY, self.doner_location)
                        self.doner_location = None
                        print("building factory in doner location")
                        return False
                await self.build_for_me(FACTORY)
            return False

        "move factory to techlab"
        if (self.factories.ready
                and self.doner_location
                and not self.structures(FACTORYTECHLAB)
                and not self.already_pending(FACTORYTECHLAB)
                and await self.can_place(FACTORY, self.doner_location)):
            for factory in self.factories:
                self.do(factory(LIFT))
            return False
        for factory in self.factoriesflying.idle:
            if self.doner_location:
                if await self.can_place(FACTORY, self.doner_location):
                    self.do(factory(LAND, self.doner_location))
                    print("land factory to doner location")
                else:
                    self.doner_location = None

        if self.structures(FACTORYTECHLAB) and self.doner_location:
            self.doner_location = None

        "build one priority tank"
        if (self.factories.ready
                and not self.already_pending(SIEGETANK)
                and not self.siegetanks
                and not self.siegetanks_sieged
                and self.structures(FACTORYTECHLAB).ready):
            for factory in self.factories.ready:
                if not self.can_feed(SIEGETANK):
                    return True
                if (self.can_afford(SIEGETANK)):
                    self.do(factory.train(SIEGETANK))
                    print("Training priority siegetank")
                    break
                return False

        "siege priority tank behind wall"
        for tank in self.siegetanks.idle:
            if self.wall_tank_pos:
                self.do(tank.move(self.wall_tank_pos, queue=True))
                self.do(tank(AbilityId.SIEGEMODE_SIEGEMODE, queue=True))
                continue  # only one to siegemode at a time
        if self.siegetanks_sieged:
            self.wall_tank = False
        return True

    async def manage_drop(self):
        await self.build_workers(100)
        "for 4 player map skip marinedrop"
        if self.enemy_start_location == None:
            self.marine_drop = False
            return True
        self.build_bunker = False
        waypoint = await self.get_waypoint_for_dropship()
        drop_point = self.mineral_field.closer_than(10.0, self.enemy_start_location).center
        drop_point = drop_point.position.towards(self.enemy_start_location, -1)

        "gives load order to dropship (self.load_dropship = True)"
        if ((self.marines.ready.amount) >= 16
                and not self.dropship_sent
                and not self.load_dropship
                and self.medivacs.amount >= 2):
            self.load_dropship = True
        elif self.enemy_units.amount > 4 and not self.load_dropship and not self.dropship_sent:
            self.marine_drop = False
            self.first_base_saturation = -10
            self.wall_in = True
            self.wall_tank = True
            self.refineries_in_first_base = 2
            await self._client.chat_send("Abort marinedrop strategy. Go turtle.", team_only=False)

        "expand if first base saturation reached"
        if self.ccANDoc.amount == 1 and not self.already_pending(COMMANDCENTER):
            for cc in self.ccANDoc:
                if cc.assigned_harvesters >= (cc.ideal_harvesters + self.first_base_saturation):
                    if self.minerals > 400:
                        await self.expand_now_ANI()
                    else:
                        return False

        "upgrade to orbital"
        if (self.barracks.ready and self.cc.ready.idle and self.ccANDoc.amount > 1):
            if self.minerals > 150:
                for cc in self.cc.ready.idle:
                    self.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))
                    print("up grade orbital")
            return False

        "After dropship departure we expand"
        if (self.dropship_sent or self.load_dropship) and not self.already_pending(COMMANDCENTER):
            expand = True
            for cc in self.ccANDoc:
                if cc.assigned_harvesters < cc.ideal_harvesters:
                    expand = False
            if expand:
                if self.minerals > 400:
                    await self.expand_now_ANI()
                else:
                    return False

        "if dropship is full remove load command from dropship (self.load_dropship = False)"
        dropship_is_full = 0
        if self.medivacs.amount >= 2:
            for dropship in self.medivacs:
                abilities = (await self.get_available_abilities(dropship))
                if not (LOAD_MEDIVAC in abilities) and (UNLOADALLAT_MEDIVAC in abilities):
                    dropship_is_full = dropship_is_full + 1
            if dropship_is_full >= 2 and self.load_dropship:
                self.load_dropship = False
        if self.dropship_sent and (self.medivacs.idle.amount == self.medivacs.amount or not self.medivacs):
            self.build_bunker = True
            self.marine_drop = False

        "land flying starport to rector"
        if self.starportflying and self.doner_location:
            for starport in self.starportflying:
                self.do(starport(LAND, self.doner_location))
                return False

        "wait for first supplydepot"
        if not self.supplydepots or not self.enemy_natural:
            return True
        expand = random.choice(self.supplydepots)

        "make first refinery"
        if not self.refineries:
            await self.execute_build_refinery()
            return False

        "Build 1 barracks"
        if (self.barracks.amount + self.barracksflyings.amount) < 1:
            if self.minerals > 150:
                await self.build_for_me(BARRACKS)
            return False

        "Build 2nd barracks"
        if (self.barracks.amount + self.barracksflyings.amount) < 2 and self.factories:
            if self.minerals > 150:
                await self.build_for_me(BARRACKS)
            return False

        "build factory"
        if not self.factories and not self.already_pending(FACTORY) and self.barracks.ready:
            if self.can_afford(FACTORY):
                await self.build_for_me(FACTORY)
            return False

        "build starport"
        if ((self.starports.amount + self.starportflying.amount) == 0
                and not self.already_pending(STARPORT)
                and self.factories.ready):
            if self.can_afford(STARPORT):
                await self.build_for_me(STARPORT)
            return False

        if self.doner_location:
            if self.starports.closer_than(1, self.doner_location):
                self.doner_location = None
                return False

        if self.doner_location and self.starports.ready:
            sp = random.choice(self.starports.ready)
            self.do(sp(LIFT))
            return False

        "build two priority medivacs and marines"
        if ((self.medivacs.amount + self.already_pending(MEDIVAC)) < 2 and self.vespene > 100):
            for starport in self.starports.ready:
                if self.can_afford(MEDIVAC) and self.can_feed(MEDIVAC):
                    print("Training dropship")
                    self.do(starport.train(MEDIVAC))
                return False
        elif (self.minerals > 50
              and not self.dropship_sent
              and dropship_is_full < 2
              and not self.load_dropship):
            for barracks in self.barracks:
                if len(barracks.orders) >= 2:
                    continue
                if len(barracks.orders) >= 1 and barracks.add_on_tag == 0:
                    continue
                self.do(barracks.train(MARINE))
                return False
            if self.minerals > 300:
                return True
            else:
                return False

        # load and send dropship
        if not self.dropship_sent and (self.load_dropship or dropship_is_full >= 2):
            return_home = True
            for dropship in self.medivacs.idle:
                if await self.can_cast(dropship, AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS):
                    self.do(dropship(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS))
                if self.marines and self.load_dropship:
                    marine = random.choice(self.marines)
                    self.do(dropship(AbilityId.LOAD_MEDIVAC, marine, queue = True))
                    marine = random.choice(self.marines)
                    self.do(dropship(AbilityId.LOAD_MEDIVAC, marine, queue = True))
                    continue  # continue for loop, dont execute any of the following
                elif dropship_is_full >= 2 and not self.dropship_sent:
                    self.do(dropship.move(waypoint, queue=True))
                    self.do(dropship.move(drop_point, queue=True))
                    self.do(dropship(AbilityId.UNLOADALLAT_MEDIVAC, drop_point, queue=True))
                    if return_home:
                        if self.chat:
                            await self._client.chat_send("Medivac: This is one way trip for you boys.", team_only=False)
                        self.do(dropship.move(waypoint, queue=True))
                        self.do(dropship.move(self.homeBase.position, queue=True))
                        self.dropship_sent = True
                        return_home = False
                    else:
                        self.do(dropship.attack(waypoint, queue=True))
                        self.do(dropship.attack(self.homeBase.position, queue=True))
                        self.dropship_sent = True
                        self.min_marine = 0
        return True

    async def build_cc_at_home(self):
        build_site = self.homeBase.position.towards(self.game_info.map_center, 5)
        build_site = build_site.random_on_distance(7)
        if self.mineral_field.closer_than(11, build_site):
            return False
        await self.build(COMMANDCENTER, near=build_site, build_worker=self.select_contractor(build_site))
        return True

    async def remember_enemy(self):
        units_to_ignore = [ADEPTPHASESHIFT, EGG, LARVA, BROODLING]

        # banshee_target_location
        targets = self.enemy_units_on_ground.filter(lambda x: not x.can_attack_air).exclude_type(units_to_ignore)
        if targets and self.banshees:
            target = targets.closest_to(self.homeBase).position
            if not self.banshee_target_location:
                print("fist target available")
                self.banshee_target_location = target
            elif target.distance_to(self.homeBase) < self.banshee_target_location.distance_to(self.homeBase):
                self.banshee_target_location = target

        # viking_target_location
        self.viking_target_location = None  # vikings are less agressive with this line
        targets = (self.allEnemyUnits.filter(lambda x: x.is_flying) |
                   self.allEnemyUnits.of_type([COLOSSUS]))
        if targets:
            target = targets.closest_to(self.homeBase).position
            if not self.viking_target_location:
                self.viking_target_location = target
            elif target.distance_to(self.homeBase) < self.viking_target_location.distance_to(self.homeBase):
                self.viking_target_location = target

        # anti_air_unit_location (threats)
        targets = self.enemy_units_on_ground.filter(lambda x: x.can_attack_air)
        if targets:
            target = targets.closest_to(self.homeBase).position
            if not self.anti_air_unit_location:
                self.anti_air_unit_location = target
            elif target.distance_to(self.homeBase) < self.anti_air_unit_location.distance_to(self.homeBase):
                self.anti_air_unit_location = target

        # enemy_air_unit_location
        self.enemy_air_unit_location = None  # vikings are less agressive with this line
        targets = self.allEnemyUnits.filter(lambda x: x.is_flying and x.can_attack_air)
        if targets:
            target = targets.closest_to(self.homeBase).position
            if not self.enemy_air_unit_location:
                self.enemy_air_unit_location = target
            elif target.distance_to(self.homeBase) < self.enemy_air_unit_location.distance_to(self.homeBase):
                self.enemy_air_unit_location = target

    async def cashe_units_fast_cycle(self):
        self.cc = self.townhalls(COMMANDCENTER)
        self.orbitalcommand = self.townhalls(ORBITALCOMMAND)
        self.ccANDoc = (self.cc | self.orbitalcommand | self.townhalls(PLANETARYFORTRESS))
        self.reapers = self.units(REAPER)
        self.marines = self.units(MARINE)
        self.marauders = self.units(MARAUDER)
        self.hellions = self.units(HELLION)
        self.cyclones = self.units(CYCLONE)
        self.thors = (self.units(THOR) | self.units(THORAP))
        # self.allEnemyUnits = self.known_enemy_units.filter(lambda x: x.is_visible)
        self.allEnemyUnits = (self.enemy_units | self.enemy_structures).filter(lambda x: x.is_visible)
        # self.enemy_structures = self.known_enemy_structures burnys fork does this already
        self.remember_friendly_units()
        self.bunkers = self.structures(BUNKER)
        self.general = None
        if self.FastReaper and self.reapers.exists:
            self.general = self.reapers.furthest_to(self.start_location)
        elif self.dropship_sent and self.hellions:
            self.general = self.hellions.furthest_to(self.start_location)
        elif self.thors.exists:
            self.general = self.thors.furthest_to(self.start_location)
        elif self.marauders.exists:
            self.general = self.marauders.furthest_to(self.start_location)


    async def cashe_units(self):
        self.scvs = self.workers(SCV)
        self.townhalls_flying = (self.townhalls(COMMANDCENTERFLYING) | self.townhalls(ORBITALCOMMANDFLYING))
        self.supplydepots = (self.structures(SUPPLYDEPOT) | self.structures(SUPPLYDEPOTLOWERED))
        self.refineries = self.gas_buildings
        self.barracks = self.structures(BARRACKS)
        self.barracksflyings = self.structures(BARRACKSFLYING)
        self.starports = self.structures(STARPORT)
        self.starportflying = self.structures(STARPORTFLYING)
        self.engineeringbays = self.structures(ENGINEERINGBAY)
        self.ghost_academies = self.structures(GHOSTACADEMY)
        self.armories = self.structures(ARMORY)
        self.factories = self.structures(FACTORY)
        self.factory_reactors = self.structures(FACTORYREACTOR)
        self.factory_techlabs = self.structures(UnitTypeId.FACTORYTECHLAB)
        self.factoriesflying = self.structures(FACTORYFLYING)
        self.fusioncores = self.structures(FUSIONCORE)
        self.techlabs_and_reactors = (self.structures(TECHLAB) | self.structures(REACTOR))
        self.enemy_units_on_ground = self.allEnemyUnits.not_structure.not_flying.filter(lambda x: not x.is_hallucination)
        self.outpost = None
        self.outpost = await self.get_outpost()
        self.ghosts = self.units(GHOST)
        self.hell_bats = self.units(HELLIONTANK)
        self.mines = self.units(WIDOWMINE)
        self.mines_burrowed = self.units(WIDOWMINEBURROWED)
        self.siegetanks = self.units(SIEGETANK)
        self.siegetanks_sieged = self.units(SIEGETANKSIEGED)
        self.vikings = self.units(VIKINGFIGHTER)
        self.vikingassault = self.units(VIKINGASSAULT)
        self.vikings_total = (self.units(VIKINGFIGHTER) | self.units(VIKINGASSAULT))
        self.liberators = self.units(LIBERATOR)
        self.liberatorsdefending = self.units(LIBERATORAG)
        self.all_liberators = (self.liberators | self.liberatorsdefending)
        self.banshees = self.units(BANSHEE)
        self.medivacs = self.units(MEDIVAC)
        self.battlecruisers = self.units(BATTLECRUISER)

    async def get_enemy_natural(self):
        """Find enemy natural."""
        if self.enemy_start_location == None:
            return None
        closest = None
        distance = math.inf
        for el in self.expansion_locations:
            ##            def is_near_to_expansion(t):
            ##                return t.distance_to(el) < self.EXPANSION_GAP_THRESHOLD
            ##
            ##            if any(map(is_near_to_expansion, self.townhalls)):
            ##                # already taken
            ##                continue
            d = await self._client.query_pathing(self.enemy_start_location, el)
            if d is None:
                continue
            if d < 10:
                continue
            if d < distance:
                distance = d
                closest = el
        return closest

    async def move_scvs(self):
        scvs = self.scvs
        units_to_ignore = [REAPER]
        targets = self.allEnemyUnits.not_flying.not_structure.filter(lambda x: x.type_id not in units_to_ignore)
        if self.enemy_structures:
            mierals_left = False
            for cc in self.ccANDoc:
                if self.mineral_field.closer_than(10, cc):
                    mierals_left = True
                    break
            if not mierals_left:
                for scv in self.scvs.idle:
                    self.do(scv.attack(self.enemy_structures.random))
                return
        if targets and scvs:
            mf = self.mineral_field.closest_to(self.homeBase)
            targets_near_home = targets.closer_than(25, self.homeBase)
            needed_units_in_kodinturvajoukot = 0
            if targets_near_home.amount > 2 and self.supplydepots.amount < 3:
                iminent_threats = targets.closer_than(30, self.homeBase)
                if self.kodinturvajoukot.amount <= iminent_threats.amount:
                    needed_units_in_kodinturvajoukot = iminent_threats.amount - self.kodinturvajoukot.amount + 2
                    self.add_unit_to_kodinturvajoukot(self.scvs.random)
                self.home_in_danger = True
            elif not targets.closer_than(100, self.homeBase):
                self.home_in_danger = False
            for scv in scvs:
                if scv.is_in_repair_group:
                    continue
                if needed_units_in_kodinturvajoukot > 0 and not scv.is_in_kodinturvajoukot and not scv.is_puuhapete:
                    self.add_unit_to_kodinturvajoukot(scv)
                    needed_units_in_kodinturvajoukot = needed_units_in_kodinturvajoukot - 1
                if self.home_in_danger and scv.is_in_kodinturvajoukot:
                    target = targets.closest_to(scv)
                    self.do(scv.attack(target.position.towards(scv, -5)))
                    continue
                if (self.scvs.amount <= (self.scv_limit - 7)
                        and scv.distance_to(self.homeBase) > 10
                        and not self.build_planetaries):
                    scv_targets = targets.closer_than(10, scv)
                    if scv_targets.amount > 1:
                        self.do(scv.gather(mf))
                        continue
        else:
            self.home_in_danger = False
        if self.iteraatio % 10 == 0:
            if self.supply_used > 150 and not self.enemy_structures.exists:
                target = random.choice(self.vespene_geyser)
                scout = self.scvs.random
                self.do(scout.attack(target.position))
        await self.gather_gas_and_minerals()

    async def priority_train(self, unit):
        """
        called example: await self.priority_train(MARAUDER)
        return False if no training facility, resourses, or supply left.
        return True if managed to train unit or waiting for minerals.
        max queue for units = 2
        """

        if not self.can_afford(unit):
            return True

        # find facility that producecs this unit
        barracks_units = [MARINE, MARAUDER, REAPER, GHOST]
        factory_units = [HELLION, HELLIONTANK, SIEGETANK, CYCLONE, WIDOWMINE, THOR]
        starport_units = [VIKINGFIGHTER, MEDIVAC, LIBERATOR, RAVEN, BANSHEE, BATTLECRUISER]
        if unit in barracks_units:
            FACILITY = BARRACKS
        elif unit in factory_units:
            FACILITY = FACTORY
        elif unit in starport_units:
            FACILITY = STARPORT
        else:
            return False

        # find ability that is needed to build this unit
        unit_creation_ability = {
            MARINE: BARRACKSTRAIN_MARINE,
            MARAUDER: BARRACKSTRAIN_MARAUDER,
            REAPER: BARRACKSTRAIN_REAPER,
            GHOST: BARRACKSTRAIN_GHOST,
            HELLION: FACTORYTRAIN_HELLION,
            HELLIONTANK: TRAIN_HELLBAT,
            SIEGETANK: FACTORYTRAIN_SIEGETANK,
            CYCLONE: TRAIN_CYCLONE,
            WIDOWMINE: FACTORYTRAIN_WIDOWMINE,
            THOR: FACTORYTRAIN_THOR,
            VIKINGFIGHTER: STARPORTTRAIN_VIKINGFIGHTER,
            MEDIVAC: STARPORTTRAIN_MEDIVAC,
            LIBERATOR: STARPORTTRAIN_LIBERATOR,
            RAVEN: STARPORTTRAIN_RAVEN,
            BANSHEE: STARPORTTRAIN_BANSHEE,
            BATTLECRUISER: STARPORTTRAIN_BATTLECRUISER
        }
        ability = unit_creation_ability.get(unit)
        for building in self.structures(FACILITY):
            if len(building.orders) > 1:
                continue
            if self.can_feed(unit) and await self.has_ability(ability, unit=building):
                await self.do(building.train(unit))
                return True
        return False

    async def has_ability(self, ability, unit):
        abilities = await self.get_available_abilities(unit)
        if ability in abilities:
            return True
        else:
            return False

    async def move_reapers(self):
        units_to_ignore = [ADEPTPHASESHIFT, EGG, LARVA]
        units_to_hunt = [DRONE, SCV, PROBE]
        homeBase = None
        if self.ccANDoc:
            homeBase = self.ccANDoc.closest_to(self.homeBase)
        if not self.reapers:
            return
        if not homeBase:
            return
        if self.reapers.exists:
            outpost = await self.get_outpost()
            reaperGrenadeRange = self._game_data.abilities[AbilityId.KD8CHARGE_KD8CHARGE.value]._proto.cast_range
            not_visible_geysers = self.vespene_geyser.filter(lambda x: x.is_visible == False)
            not_visible_geysers = not_visible_geysers.filter(lambda x: not self.enemy_structures.closer_than(15, x))
            enemy_ground_units = self.allEnemyUnits.not_structure.not_flying.exclude_type(units_to_ignore)
            if enemy_ground_units.closer_than(30, homeBase):
                priority_targets = enemy_ground_units.closer_than(30, homeBase)
            else:
                priority_targets = None
            if not_visible_geysers:
                target = random.choice(not_visible_geysers)
            else:
                target = (outpost)
            for reaper in self.reapers:
                reaperRange = (reaper.ground_range + reaper.radius)
                if self.FastReaper:
                    if reaper.health_percentage < 2 / 3:
                        if self.allEnemyUnits.closer_than(15, reaper) and homeBase:
                            self.do(reaper.move(homeBase.position.towards(self.allEnemyUnits.closest_to(reaper), -6)))
                            continue
                        else:
                            self.do(reaper.move(reaper.position))
                            continue
                    if enemy_ground_units.exists:
                        if reaper.weapon_cooldown != 0:
                            closest_enemy = enemy_ground_units.closest_to(reaper)
                            target = reaper.position.towards(closest_enemy, reaperGrenadeRange)
                            abilities = (await self.get_available_abilities(reaper))
                            # taken damage -> do not hunt workers
                            if reaper.health_percentage < 1 and homeBase:
                                self.do(reaper.move(homeBase.position))
                                continue
                            # no other than workers visible -> charge
                            if not enemy_ground_units.exclude_type(units_to_hunt):
                                self.do(reaper.move(target))
                                continue
                        priority_targets = enemy_ground_units.closer_than(reaperRange, reaper.position)\
                            .sorted(lambda x: (x.health + x.shield), reverse=False)
                        if priority_targets:
                            target = priority_targets[0]
                            self.do(reaper.attack(target))
                            continue
                    if self.cyclones.exists and self.enemy_start_location:
                        self.do(reaper.attack(self.enemy_start_location))
                        continue
                    elif self.enemy_natural and self.enemy_start_location and len(reaper.orders) < 2:
                        enemy_homebase_mineral_line = self.mineral_field.closer_than(10.0, self.enemy_start_location).center
                        enemy_natural_mineral_line = self.mineral_field.closer_than(10.0, self.enemy_natural).center
                        self.do(reaper.move(enemy_natural_mineral_line))
                        self.do(reaper.move(enemy_homebase_mineral_line, queue=True))
                        self.do(reaper.move(enemy_natural_mineral_line, queue=True))
                    continue

                if await self.avoid_own_nuke(reaper):
                    continue
                if await self.avoid_enemy_siegetanks(reaper):
                    continue

                if reaper.weapon_cooldown != 0 and enemy_ground_units.exists and reaper.health_percentage < 1:
                    closest_enemy = enemy_ground_units.closest_to(reaper)
                    abilities = (await self.get_available_abilities(reaper))
                    target = closest_enemy
                    if await self.can_cast(reaper, AbilityId.KD8CHARGE_KD8CHARGE, target,
                                           cached_abilities_of_unit=abilities):
                        self.do(reaper(AbilityId.KD8CHARGE_KD8CHARGE, target.position.towards(reaper, -1)))
                        continue
                if reaper.health_percentage < 0.5 and homeBase:
                    if self.enemy_units.closer_than(20,self.homeBase):
                        if reaper.weapon_cooldown != 0:
                            self.do(reaper.move(homeBase.position.towards(self.enemy_units.closest_to(reaper), -6)))
                        else:
                            target = self.enemy_units.closest_to(reaper)
                            self.do(reaper.attack(target.position))
                    self.do(reaper.move(homeBase.position))
                    continue
                if priority_targets:
                    self.do(reaper.attack(priority_targets.closest_to(reaper.position).position))
                if len(reaper.orders) == 0:
                    self.do(reaper.attack(target.position))
                    continue

    async def move_vikings(self):
        if not self.vikings and not self.vikingassault:
            return
        enemy_airunits = [UnitTypeId.VIKING, UnitTypeId.VIKINGASSAULT]
        delay_air_battle = False
        self.viking_landing_delay += 1
        if (self.supply_used > 175 or self.enemy_race == Race.Protoss) and self.viking_landing_delay > 20:
            viking_can_land = True
        else:
            viking_can_land = False
        if self.adaptive_viking_count and self.enemy_units.of_type(enemy_airunits):
            if (self.vikings.amount <= self.enemy_units.of_type(enemy_airunits).amount
                    and not self.enemy_units.closer_than(15, self.homeBase)):
                delay_air_battle = True
        if not self.homeboys and self.vikings_total.amount > 5:
            self.add_unit_to_homeboys_group(self.vikings_total.random)
        if self.vikings_total.amount > 5:
            lowest_health_for_viking = 1000
        else:
            lowest_health_for_viking = 100
        outpost = await self.get_outpost()
        enemy_threats = self.allEnemyUnits.filter(lambda x: x.can_attack_air)
        if self.allEnemyUnits.of_type([UnitTypeId.MOTHERSHIP]):
            enemy_high_priority_targets = self.allEnemyUnits.of_type(
                [UnitTypeId.MOTHERSHIP]).sorted(lambda x: (x.health + x.shield),reverse=False)
            priority_target = enemy_high_priority_targets[0]
        elif self.allEnemyUnits.of_type([TEMPEST, UnitTypeId.COLOSSUS]):
            enemy_high_priority_targets = self.allEnemyUnits.of_type(
                [TEMPEST, UnitTypeId.COLOSSUS]).sorted(lambda x: (x.health + x.shield),reverse=False)
            priority_target = enemy_high_priority_targets[0]
        else:
            priority_target = None

        reset_lowest_health_viking_tag = True
        low_health_viking_tag = None
        for viking in self.vikings:
            if self.vikingassault.amount > 1:
                break
            if not self.lowest_health_viking_tag:
                if viking.health < lowest_health_for_viking and viking.health_percentage < 1:
                    reset_lowest_health_viking_tag = False
                    lowest_health_for_viking = viking.health
                    low_health_viking_tag = viking.tag
            elif viking.tag == self.lowest_health_viking_tag:
                reset_lowest_health_viking_tag = False
        if low_health_viking_tag:
            self.lowest_health_viking_tag = low_health_viking_tag
        if reset_lowest_health_viking_tag:
            self.lowest_health_viking_tag = None

        def attacks_air(x):
            return x.can_attack_air
        for viking in self.vikings:
            if priority_target:
                self.do(viking.attack(priority_target))
                continue
            elif viking.tag == self.lowest_health_viking_tag or viking.health_percentage < 0.25:
                if viking.distance_to(self.homeBase) < 7:
                    self.do(viking(AbilityId.MORPH_VIKINGASSAULTMODE))
                    continue
                else:
                    self.do(viking.move(self.homeBase.position))
                    continue  # continue for loop, dont execute any of the following

            unit_in_no_flight_zone = (self.enemy_structures.filter(attacks_air).closer_than(12,viking) |
                                      self.enemy_units_on_ground.filter(attacks_air).closer_than(7, viking))
            if await self.avoid_own_nuke(viking):
                continue
            if self.supply_used < 190 and unit_in_no_flight_zone:
                self.do(viking.move(viking.position.towards(self.homeBase.position, 5)))
                continue  # continue for loop, dont execute any of the following
            flying_enemies = self.enemy_units.flying.filter(attacks_air)
            if viking.weapon_cooldown != 0:
                self.do(viking.move(viking.position.towards(self.homeBase.position, 2)))
                continue

            if delay_air_battle:
                self.do(viking.move(self.homeBase.position))
                continue

            # attack air units (threaths)
            if self.enemy_air_unit_location and not viking.is_in_homeboys:
                if viking.distance_to(self.enemy_air_unit_location) < 2:
                    self.enemy_air_unit_location = None
                    continue
                else:
                    self.do(viking.attack(self.enemy_air_unit_location))
                    continue

            # attack all air targets (including colossus)
            if self.viking_target_location:
                if viking.distance_to(self.viking_target_location) < 2:
                    self.viking_target_location = None
                    continue
                else:
                    self.do(viking.attack(self.viking_target_location))
                    continue
            if (self.siegetanks_sieged
                    and not viking.is_in_homeboys
                    and self.supply_used < 180
                    and self.enemy_race != Race.Protoss):
                if len(viking.orders) == 0:
                    need_vision = self.siegetanks_sieged.random
                    self.do(viking.move(need_vision.position.random_on_distance(6)))
                continue
            if self.general and not viking.is_in_homeboys:
                if self.banshees:
                    target_position = self.general.position.towards(self.homeBase, 10)
                else:
                    target_position = self.general.position.towards(self.enemy_start_location, 4)
                if viking.distance_to(target_position) > 7:
                    self.do(viking.attack(target_position.random_on_distance(6)))
                    continue
            if (viking.distance_to(self.homeBase) > 15
                    and not viking.is_in_homeboys and viking_can_land):
                self.do(viking(AbilityId.MORPH_VIKINGASSAULTMODE))
                viking_can_land = False
                self.viking_landing_delay = 0
                continue
            if viking.position.to2.distance_to(outpost.position.to2) > 8 and (not self.general or viking.is_in_homeboys):
                self.do(viking.move(outpost.position))
                continue

        secondary_targets = self.enemy_structures.filter(lambda x: x.is_visible)
        for viking in self.vikingassault:
            if viking.tag == self.lowest_health_viking_tag:
                self.lowest_health_viking_tag = None
            if viking.distance_to(self.homeBase) < 12:
                if viking.health_percentage < 1:
                    continue
                else:
                    self.do(viking(AbilityId.MORPH_VIKINGFIGHTERMODE))
                    continue
            if ((viking.health_percentage < 0.5
                 and ((self.vikings.amount + self.vikingassault.amount) <= self.max_viking))
                    or self.enemy_air_unit_location
                    or self.viking_target_location
                    or await self.avoid_own_nuke(viking)
                    or await self.avoid_enemy_siegetanks(viking)):
                self.do(viking(AbilityId.MORPH_VIKINGFIGHTERMODE))
                continue

            if self.enemy_units_on_ground.amount > 1:
                if viking.weapon_cooldown != 0 and viking.health_percentage < 1:
                    self.do(viking.move(self.homeBase))
                    continue
                priority_targets = self.enemy_units_on_ground.filter(lambda x: x.is_mechanical)
                if priority_targets:
                    target = priority_targets.closest_to(viking)
                    if target.distance_to(viking) < 8:
                        self.do(viking.attack(target))
                        continue
                target = self.enemy_units_on_ground.closest_to(viking)
                self.do(viking.attack(target.position))
                continue
            if secondary_targets:
                target = secondary_targets.closest_to(viking)
                self.do(viking.attack(target.position))
                continue
            if self.general:
                if viking.distance_to(self.general.position.towards(self.homeBase, 8)) > 6:
                    self.do(viking.move(self.general.position.towards(self.homeBase, 8)))
                    continue
            if viking.position.to2.distance_to(outpost.position.to2) > 8 and (not self.general or viking.is_in_homeboys):
                self.do(viking.move(outpost.position))
                continue

    async def move_thors(self):
        outpost = await self.get_outpost()
        thorMinHealth = 2 / 10  # minimum healt for thor to continue fight
        idle_thors = self.thors.idle
        if self.minerals > 3000:
            self.min_thors_to_attack = 0
        for thor in self.thors:
            # if await self.avoid_own_nuke(thor):
            #     continue
            if thor.health_percentage < thorMinHealth:
                if thor.distance_to(outpost) > 10:
                    self.do(thor.move(outpost.position))
                    continue  # continue for loop, dont execute any of the following
        for thor in idle_thors:
            if await self.has_ability(MORPH_THORHIGHIMPACTMODE, thor):
                self.do(thor(AbilityId.MORPH_THORHIGHIMPACTMODE))
                continue
            if thor.distance_to(outpost.position.towards(self.game_info.map_center, 6)) > 10:
                self.do(thor.attack(outpost.position.towards(self.game_info.map_center, 6)))
                continue  # continue for loop, don't execute any of the following
        if len(idle_thors) >= self.min_thors_to_attack or len(idle_thors) >= 4 or len(idle_thors) >= self.max_thor:
            if self.min_thors_to_attack <= 4:
                if self.min_thors_to_attack == 1 and self.thors:
                    if self.chat:
                        say = "Thor time."
                        await self._client.chat_send(say, team_only=False)
                self.min_thors_to_attack += 1
            if self.enemy_structures.exists:
                target_of_assault = random.choice(self.enemy_structures)
            else:
                target_of_assault = random.choice(self.vespene_geyser.filter(lambda x: x.is_visible == False))
            for thor in idle_thors:
                self.do(thor.attack(target_of_assault.position))
                continue  # continue for loop, dont execute any of the following

    async def move_liberators(self):
        for liberator in self.liberators:
            unit_in_no_flight_zone = (
                self.enemy_structures.filter(lambda x: x.can_attack_air).closer_than(11, liberator))
            if await self.avoid_own_nuke(liberator):
                self.do(liberator.move(self.homeBase.position))
                continue
            if unit_in_no_flight_zone:
                self.do(liberator.move(self.homeBase.position))
                continue

            if self.enemy_units_on_ground:
                if self.enemy_units_on_ground.of_type([SIEGETANKSIEGED]):
                    target = self.enemy_units_on_ground.of_type([SIEGETANKSIEGED]).closest_to(
                        liberator).position.towards(liberator, 3)
                else:
                    target = self.enemy_units_on_ground.closest_to(liberator).position.towards(liberator, 2)
                if await self.has_ability(MORPH_LIBERATORAGMODE, liberator):
                    self.do(liberator(AbilityId.MORPH_LIBERATORAGMODE, target.position))
                    if not self.liberatorsdefending:
                        self.liberator_timer = -5
                continue
            if len(liberator.orders) == 0 and self.marine_drop and self.medivacs:
                self.do(liberator.move(random.choice(self.medivacs)))
                continue
            if len(liberator.orders) == 0 and self.ccANDoc:
                self.do(liberator.move(random.choice(self.ccANDoc).position))
                continue

        ##                if self.general:
        ##                    self.do(liberator.move(self.general.position))
        ##                    continue
        ##                else:
        ##                    self.do(liberator.move(self.homeBase.position))
        ##                    continue
        self.liberator_timer += 1
        if self.liberatorsdefending.amount == 1:
            for liberator in self.liberatorsdefending:
                if liberator.weapon_cooldown != 0:
                    self.liberator_timer = 0
        for liberator in self.liberatorsdefending:
            if self.liberator_timer >= 12 and liberator.weapon_cooldown == 0:
                self.liberator_timer = 0
                self.do(liberator(AbilityId.MORPH_LIBERATORAAMODE))
                break

    async def move_banshees(self):
        outpost = await self.get_outpost()
        units_to_ignore = [ADEPTPHASESHIFT, EGG, LARVA, BROODLING]
        targets = self.enemy_units_on_ground.exclude_type(units_to_ignore)
        secondary_targets = self.enemy_structures.filter(lambda x: x.is_visible)
        end_game_targets = self.enemy_structures
        for banshee in self.banshees:
            unit_in_no_flight_zone = (self.enemy_structures.filter(lambda x: x.can_attack_air).closer_than(11, banshee))
            enemy_threats = self.allEnemyUnits.filter(lambda x: x.can_attack_air).closer_than(11, banshee)

            if banshee.is_taking_damage and await self.can_cast(banshee, AbilityId.BEHAVIOR_CLOAKON_BANSHEE):
                self.do(banshee(AbilityId.BEHAVIOR_CLOAKON_BANSHEE))
                continue

            if unit_in_no_flight_zone:
                # if self.supply_used < 180:
                if self.banshee_left > 0:
                    self.do(banshee.move(self.homeBase.position))
                    continue
                else:
                    self.do(banshee.attack(unit_in_no_flight_zone.closest_to(banshee)))
                    continue

            if await self.avoid_own_nuke(banshee):
                self.do(banshee(AbilityId.BEHAVIOR_CLOAKON_BANSHEE))
                continue

            if targets:
                if (banshee.weapon_cooldown != 0
                      and (enemy_threats
                           or self.enemy_units.of_type(CYCLONE).closer_than(11, banshee))):
                    self.do(banshee.move(self.homeBase.position))
                    continue
                else:
                    self.do(banshee.attack(targets.closest_to(banshee)))
                    continue
            if secondary_targets:
                target = secondary_targets.closest_to(banshee)
                self.do(banshee.attack(target.position))
                continue
            if self.general:
                target_position = self.general.position.towards(self.enemy_start_location, 5)
                if banshee.distance_to(target_position) > 3:
                    self.do(banshee.attack(target_position))
                continue

            if self.vespene > 1000 and end_game_targets:
                target = end_game_targets.closest_to(banshee)
                self.do(banshee.attack(target.position))
                continue

            if banshee.position.to2.distance_to(outpost.position.to2) > 8:
                self.do(banshee.move(outpost))
                continue

    async def move_medivacs(self):
        priority_units = (self.ghosts)
        healable_units = (self.marines |
                          self.ghosts |
                          self.hell_bats |
                          self.marauders)
        priority_healing = priority_units.filter(lambda x: x.health_percentage < 0.9)
        needs_healing = healable_units.filter(lambda x: x.health_percentage < 1)
        target_for_standby = None
        if self.marauders.exists:
            target_for_standby = self.marauders.furthest_to(self.homeBase)
        elif self.marines.exists:
            target_for_standby = self.marines.furthest_to(self.homeBase)
        if target_for_standby:
            target_position = target_for_standby.position.towards(self.homeBase, 5)
        for healer in self.medivacs:
            unit_in_no_flight_zone = (self.enemy_structures.filter(
                lambda x: x.can_attack_air).closer_than(10,healer) | self.allEnemyUnits.filter(
                lambda x: x.can_attack_air).closer_than(6, healer))
            if healer.position.to2.distance_to(self.homeBase.position.to2) < 10:
                if healer.health_percentage < 1:
                    if self.iteraatio % 30 == 0:
                        self.do(healer.move(self.homeBase.position.random_on_distance(6)))
                    continue
            if await self.avoid_own_nuke(healer):
                continue
            if unit_in_no_flight_zone:
                self.do(healer.move(self.homeBase.position))
                continue
            if healer.health_percentage > 0.5:
                if priority_healing and self.NukesLeft > 10:
                    target = priority_healing.closest_to(healer)
                    if await self.can_cast(healer, AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS):
                        self.do(healer(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS))
                        continue
                    self.do(healer.attack(target.position))
                    continue
                if needs_healing:
                    # if healer.energy > 25 and await self.can_cast(healer, AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS):
                    #     self.do(healer(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS))
                    #     continue
                    target = needs_healing.closest_to(healer).position.towards(healer, -2)
                    self.do(healer.attack(target))
                    continue
                if target_for_standby:
                    if healer.position.distance_to(target_position) > 5:
                        self.do(healer.move(target_position))
                    continue
            if healer.distance_to(self.homeBase) > 15:
                if await self.can_cast(healer, AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS):
                    self.do(healer(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS))
                    continue
                self.do(healer.move(self.homeBase.position))

    async def move_hellions_and_hellbats(self):
        outpost = await self.get_outpost()
        hellions = self.hellions
        hell_bats = self.hell_bats
        enemy_threats = self.allEnemyUnits.not_flying.not_structure
        primary_targets = enemy_threats.filter(lambda x: x.is_light)
        cyclones = self.cyclones
        for hellion in hellions:
            if await self.has_ability(MORPH_HELLBAT, hellion):
                self.do(hellion(AbilityId.MORPH_HELLBAT))
                continue
            if hellion.health_percentage < 0.5 and hellion.distance_to(self.homeBase) > 10 and not self.marine_drop:
                self.do(hellion.move(self.homeBase.position))
                continue
            if hellion.distance_to(self.homeBase) < 10 and hellion.health_percentage < 1:
                continue
            if await self.avoid_own_nuke(hellion):
                continue
            if await self.avoid_enemy_siegetanks(hellion):
                continue
            if enemy_threats:
                if hellion.weapon_cooldown == 0:
                    target = enemy_threats.closest_to(hellion)
                    self.do(hellion.attack(target))
                    continue
                else:
                    self.do(hellion.move(self.homeBase.position))
                    continue
            if self.marine_drop and self.enemy_start_location and self.medivacs:
                dropship = self.medivacs.furthest_to(self.start_location)
                if self.dropship_sent and dropship.distance_to(self.enemy_start_location) < hellion.distance_to(
                        self.enemy_start_location):
                    self.do(hellion.move(self.enemy_start_location))
                    continue
            if self.FastReaper and not enemy_threats:
                if self.general:
                    if hellion.distance_to(self.general) > 7:
                        self.do(hellion.move(self.general))
                        continue
            elif hellion.distance_to(self.homeBase) > 10:
                self.do(hellion.move(self.homeBase.position))
                continue

        ## hellion tank
        for unit in hell_bats:
            if await self.avoid_own_nuke(unit):
                continue
            # if await self.avoid_enemy_siegetanks(unit):
            #     continue

            if enemy_threats:
                if unit.weapon_cooldown == 0:
                    self.do(unit.attack(enemy_threats.closest_to(unit).position))
                    continue
                else:
                    self.do(unit.move(enemy_threats.closest_to(unit).position.towards(unit, -4)))
                    continue
            if self.general:
                if unit.distance_to(self.general) > 10:
                    self.do(unit.attack(self.general.position))
                    continue
            elif unit.distance_to(self.homeBase) > 10:
                self.do(unit.move(self.homeBase.position))
                continue

    async def move_mines(self):
        if not self.enemy_start_location:
            return
        mines = self.mines
        mines_burrowed = self.mines_burrowed
        mines_burrowed = mines_burrowed.sorted(lambda x: x.distance_to(self.enemy_start_location), reverse=True)
        target_distance_to_enemy_home = self.homeBase.distance_to(self.enemy_start_location) - 15
        supply_limit = 100
        if self.agressive_mines:
            if self.mines_burrowed:
                the_mine = self.mines_burrowed.closest_to(self.enemy_start_location)
                target_distance_to_enemy_home = the_mine.distance_to(self.enemy_start_location) - 1
        cyclones = self.cyclones
        targets = self.allEnemyUnits.not_structure
        if cyclones.exists:
            master = cyclones.furthest_to(self.homeBase)
        elif self.marauders:
            master = self.marauders.furthest_to(self.homeBase).position.towards(self.enemy_start_location, 6)
        elif self.marines:
            master = self.marines.furthest_to(self.homeBase)
        else:
            master = None
        if self.agressive_mines and (self.mines_left <= 0 or (self.minerals > 2000 and self.supply_used > 190)):
            self.max_BC = 1
            self.liberator_left = 0
            #self.maxmedivacs = 0
            self.max_viking = 0
            #self.max_thor = 10
            self.agressive_mines = False
            #self.maxfactory += 1
            self.max_starports += 3
            self.activate_all_mines = True
            self.mines_left = 0
            await self._client.chat_send("I'm done with playing around. Lets end this!", team_only=False)
        for mine in mines:
            if (mine.tag in self.remembered_fired_mines_by_tag
                    and (self.already_pending(DRILLCLAWS) < 1 or mine.health_percentage < 1)):
                if (len(mine.orders) == 0 and mine.distance_to(self.homeBase) > 10):
                        self.do(mine.move(self.homeBase.position.random_on_distance(6)))
                elif not self.enemy_units.closer_than(25, mine):
                    self.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                elif len(mine.orders) == 0:
                    self.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                continue
            if await self.avoid_own_nuke(mine):
                continue
            if await self.avoid_enemy_siegetanks(mine):
                continue
            if self.agressive_mines or self.activate_all_mines:
                if not self.activate_all_mines and targets.closer_than(8, mine):
                    self.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                    continue
                if targets.closer_than(6, mine):
                    # print ("Mine range:",self._game_data.abilities[AbilityId.WIDOWMINEATTACK_WIDOWMINEATTACK.value]._proto.cast_range)
                    self.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                    continue
                if mines.amount > 10 and not mine.tag in self.remembered_fired_mines_by_tag and self.agressive_mines:
                    self.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                    break
            elif targets.closer_than(10, mine):
                self.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                continue
            if targets.closer_than(20, mine):
                target = targets.closest_to(mine)
                self.do(mine.move(target))
                continue
            if self.agressive_mines or self.activate_all_mines:
                if targets:
                    if targets.further_than(target_distance_to_enemy_home, self.enemy_start_location.position):
                        target = targets.closest_to(mine)
                        self.do(mine.move(target))
                        continue
                if self.leapfrog_mines:
                    if len(mine.orders) == 0:
                        self.do(mine.move(self.enemy_start_location, queue=True))
                        break
                    if mine.distance_to(self.enemy_start_location) < target_distance_to_enemy_home:
                        self.do(mine(AbilityId.BURROWDOWN_WIDOWMINE))
                elif self.general:
                    if mine.distance_to(self.general) > 16:
                        self.do(mine.move(self.general.position))
                continue
            if master and len(mine.orders) == 0:
                if mine.distance_to(master) > 3:
                    self.do(mine.move(master))
                    self.do(mine(AbilityId.BURROWDOWN_WIDOWMINE, queue=True))
                continue

        for mine in mines_burrowed:
            if self.mines_burrowed.amount == 1:
                continue
            if self.leapfrog_mines and mine.health_percentage < 1:
                self.leapfrog_mines = False
            abilities = await self.get_available_abilities(mine)
            if self.agressive_mines or self.activate_all_mines:
                if (not WIDOWMINEATTACK_WIDOWMINEATTACK in abilities
                        and (self.already_pending(DRILLCLAWS) < 1 or mine.health_percentage < 1)):
                    if mine.distance_to(self.homeBase) > 10 and self.enemy_units.closer_than(15, mine):
                        if not mine.tag in self.remembered_fired_mines_by_tag:
                            self.remembered_fired_mines_by_tag[mine.tag] = mine
                        if self.chat_once_mine:
                            self.chat_once_mine = False
                            if self.chat:
                                await self._client.chat_send("You would not shoot unarmed mine, would you?", team_only=False)
                        self.do(mine(AbilityId.BURROWUP_WIDOWMINE))
                    continue
                if mine.tag in self.remembered_fired_mines_by_tag:
                    del self.remembered_fired_mines_by_tag[mine.tag]
            if await self.avoid_own_nuke(mine):
                self.do(mine(AbilityId.BURROWUP_WIDOWMINE))
                break
            if self.agressive_mines and self.mines_burrowed.amount < 5:
                continue
            if self.activate_all_mines:
                limit = 100
            elif self.agressive_mines:
                limit = 10
            else:
                limit = 2
            if ((self.iteraatio % 10 == 0 or self.activate_all_mines)
                    and not self.allEnemyUnits.not_structure.closer_than(10, mine)
                    and self.mines.amount < limit):
                self.do(mine(AbilityId.BURROWUP_WIDOWMINE))
                break

    async def raise_lower_depots(self):
        # Raise depos when enemies are nearby
        if self.enemy_units_on_ground and (self.wall_in or self.ccANDoc.amount == 1):
            for depo in self.structures(SUPPLYDEPOTLOWERED).ready:
                if self.enemy_units_on_ground.closer_than(30, depo):
                    self.do(depo(MORPH_SUPPLYDEPOT_RAISE))
                    continue
        for depo in self.structures(SUPPLYDEPOT).ready:
            # if self.ccANDoc.amount == 1 and self.ccANDoc.amount >= 3:
            #     if depo.distance_to(self.midle_depo_position) < 4:
            #         continue
            if not self.enemy_units_on_ground.closer_than(30, depo):
                self.do(depo(MORPH_SUPPLYDEPOT_LOWER))
                break

    async def move_tanks(self):
        if (self.wall_in and self.wall_tank):
            return
        units_to_ignore = [ADEPTPHASESHIFT, EGG, LARVA, DRONE, SCV, PROBE]
        secondary_targets = self.enemy_structures.filter(lambda x: x.is_visible)
        secondary_target = None
        if self.general and secondary_targets:
            secondary_target = secondary_targets.closest_to(self.general)
        for tank in self.siegetanks:
            if await self.avoid_own_nuke(tank):
                continue
            if await self.avoid_enemy_siegetanks(tank):
                continue
            # check if enemy ground units exists
            if self.enemy_units_on_ground:
                enemyAttackRange = self.enemy_units_on_ground.closer_than(16, tank)
                # siegemode if close enough to enemy
                if self.canSiege and enemyAttackRange.exclude_type(units_to_ignore) and await self.can_cast(
                        tank, AbilityId.SIEGEMODE_SIEGEMODE):
                    self.do(tank(AbilityId.SIEGEMODE_SIEGEMODE))
                    self.canSiege = False
                    continue  # only one to siegemode at a time
                if tank.weapon_cooldown != 0:
                    self.do(tank(AbilityId.SIEGEMODE_SIEGEMODE))
                    self.canSiege = False
                else:
                    self.do(tank.attack(self.enemy_units_on_ground.closest_to(tank)))
                    continue

            if secondary_targets:
                if tank.weapon_cooldown != 0 and self.canSiege and self.siegetanks.amount > 1 and await self.can_cast(
                        tank, AbilityId.SIEGEMODE_SIEGEMODE):
                    self.do(tank(AbilityId.SIEGEMODE_SIEGEMODE))
                    self.canSiege = False
                    continue  # only one to siegemode at a time
                elif secondary_target:
                    self.do(tank.attack(secondary_target))
                    continue

            if self.general:
                target_position = self.general.position.towards(self.homeBase, 6)
                if tank.distance_to(target_position) > 6:
                    self.do(tank.attack(target_position))
                continue

            if tank.position.to2.distance_to((await self.get_outpost()).position.to2) > 8:
                self.do(tank.move(await self.get_outpost()))
                continue

        ## SIEGETANK deside target and if need to turn tank mode
        if self.wall_in:
            return
        artillery = self.siegetanks_sieged
        for tank in artillery:
            if await self.avoid_own_nuke(tank):
                self.do(tank(AbilityId.UNSIEGE_UNSIEGE))
                return
        if self.iteraatio % 20 == 0:
            artillery = artillery.sorted(lambda x: x.distance_to(self.start_location), reverse=False)
            enemyGroundUnits = self.allEnemyUnits.not_flying.filter(lambda x: x.is_visible)
            for x in range(0, len(artillery)):
                # no enemy in attack range
                if enemyGroundUnits.exists:
                    if enemyGroundUnits.closer_than(16, artillery[x]):
                        continue
                if await self.can_cast(artillery[x], AbilityId.UNSIEGE_UNSIEGE):
                    self.do(artillery[x](AbilityId.UNSIEGE_UNSIEGE))
                    break  # quit for loop
        else:
            cannonfodder = self.enemy_units_on_ground.exclude_type([DRONE, SCV, PROBE])
            for art in artillery:
                enemyAttackRange = cannonfodder.closer_than(13, art)
                # no enemy in attack range
                if enemyAttackRange.exists:
                    potential_targets = enemyAttackRange.sorted(lambda x: (x.health + x.shield), reverse=False)
                    target = potential_targets[0]
                    self.do(art.attack(target))
                    continue

    async def move_battle_ruiser(self):
        if not self.battlecruisers:
            return
        units_to_ignore = [ADEPTPHASESHIFT, EGG, LARVA, BROODLING]
        bcs = self.battlecruisers
        FreshMeat = self.allEnemyUnits.not_structure.filter(lambda x: x.type_id not in units_to_ignore)
        if self.iteraatio % 6 == 0:
            can_yamato = True
        else:
            can_yamato = False
        perform_assault = False
        if ((bcs.amount >= (self.max_BC) or self.vespene > 5000)
                and self.enemy_start_location and self.enemy_structures.exists):
            perform_assault = True
            for battle_ruiser in bcs:
                if not await self.has_ability(EFFECT_TACTICALJUMP, battle_ruiser):
                    perform_assault = False
                    break
            if self.can_assault:
                assault_target = self.enemy_start_location
            else:
                assault_target = random.choice(self.enemy_structures)
        if perform_assault and self.can_assault:
            self.can_assault = False
            if self.chat:
                await self._client.chat_send("Tactical jump time!", team_only=False)

        for battle_ruiser in bcs:
            if perform_assault and battle_ruiser.health > 200:
                self.do(battle_ruiser(AbilityId.EFFECT_TACTICALJUMP, assault_target.position))
                continue
            if battle_ruiser.distance_to(self.homeBase) < 10 and battle_ruiser.health_percentage < 1:
                if self.iteraatio % 50 == 0:
                    self.do(battle_ruiser.move(self.homeBase.position.random_on_distance(5)))
                continue
            if battle_ruiser.health < 200:
                if await self.has_ability(EFFECT_TACTICALJUMP, battle_ruiser):
                    self.do(battle_ruiser(AbilityId.EFFECT_TACTICALJUMP, self.homeBase.position.random_on_distance(5)))
                    print("batlecruiser emergency retreat")
                continue
            if await self.avoid_own_nuke(battle_ruiser):
                continue
            if can_yamato:
                targets = self.allEnemyUnits.closer_than(10, battle_ruiser).filter(
                    lambda x: (x.shield + x.health) > 100).filter(lambda x: x.can_attack_air)
                if targets and await self.has_ability(YAMATO_YAMATOGUN, battle_ruiser):
                    target = targets[0]
                    self.do(battle_ruiser(AbilityId.YAMATO_YAMATOGUN, target))
                    can_yamato = False
                    continue
            if not self.can_assault and not await self.has_ability(EFFECT_TACTICALJUMP, battle_ruiser):
                target = None
                if FreshMeat.amount > 3:
                    target = FreshMeat.closest_to(battle_ruiser)
                elif self.enemy_structures.filter(lambda x: x.is_visible):
                    target = self.enemy_structures.closest_to(battle_ruiser)
                if target:
                    self.do(battle_ruiser.move(target))
                    continue
            if self.allEnemyUnits.exists:
                target = self.allEnemyUnits.closest_to(battle_ruiser)
                self.do(battle_ruiser.move(target.position))
                continue
            if self.general and battle_ruiser.health_percentage >= 1:
                if battle_ruiser.distance_to(self.general) > 6:
                    self.do(battle_ruiser.move(self.general))
                continue
            elif battle_ruiser.distance_to(self.homeBase) > 10:
                self.do(battle_ruiser.move(self.homeBase.position))
                continue

    async def move_cyclones(self):
        units_to_ignore = [DRONE, SCV, PROBE]
        cyclones = self.cyclones
        enemy_threats = self.allEnemyUnits.filter(lambda x: x.can_attack_ground).exclude_type(units_to_ignore)
        if enemy_threats.closer_than(12, self.homeBase):
            retreatpoint = self.natural
        else:
            retreatpoint = self.homeBase

        pick_fight = True
        if self.enemy_structures.exists and self.cyclone_left <= 0 and self.cyclones.amount > 1:
            for cyclone in cyclones:
                if cyclone.health_percentage < 1:
                    pick_fight = False
                    break
        else:
            pick_fight = False

        if self.minerals < 1000:
            repair_cyclones = True
        else:
            repair_cyclones = False

        for cyclone in cyclones:
            if not self.gatekeeper:
                self.gatekeeper = cyclone
            if await self.avoid_own_nuke(cyclone):
                continue
            if await self.avoid_enemy_siegetanks(cyclone):
                continue
            if await self.has_ability(CANCEL_LOCKON, cyclone):
                if enemy_threats.exists:
                    if enemy_threats.closer_than(9, cyclone).exists:
                        self.do(cyclone.move(retreatpoint))
                        continue
                    else:
                        target = enemy_threats.closest_to(cyclone)
                        self.do(cyclone.move(target.position))
                        continue  # continue for loop, dont execute any of the following
                else:
                    continue  # continue for loop, dont execute any of the following

            if cyclone.distance_to(self.homeBase) < 10 and cyclone.health_percentage < 1 and repair_cyclones:
                continue
            if await self.has_ability(LOCKON_LOCKON, cyclone) and (cyclone.health_percentage > 1 / 2 or not repair_cyclones):
                if enemy_threats.exists:
                    closestEnemy = enemy_threats.closest_to(cyclone)
                    self.do(cyclone.attack(closestEnemy.position))
                    continue  # continue for loop, dont execute any of the following
                if pick_fight:
                    closestEnemy = self.enemy_structures.closest_to(cyclone)
                    self.do(cyclone.attack(closestEnemy.position))
                    continue  # continue for loop, dont execute any of the following
            if self.gatekeeper.tag == cyclone.tag and self.structures(MISSILETURRET) and cyclone.health_percentage >= 1:
                turret = self.structures(MISSILETURRET).closest_to(self.natural)
                if cyclone.distance_to(turret) > 3:
                    self.do(cyclone.move(turret.position))
                continue
            if self.thors.exists and not enemy_threats and (cyclone.health_percentage >= 1 or not repair_cyclones):
                closest_thor = self.thors.closest_to(cyclone)
                if cyclone.distance_to(closest_thor) > 10:
                    self.do(cyclone.move(closest_thor))
                continue
            if cyclone.health_percentage < 1 and repair_cyclones:
                cyclone_home = retreatpoint
            else:
                cyclone_home = self.natural
            if cyclone.distance_to(cyclone_home) > 15:
                self.do(cyclone.move(cyclone_home.position))
                continue  # continue for loop, dont execute any of the following

    async def move_marauders(self):
        if not self.marauders:
            return
        nuke_ready = False
        # for ghost in self.ghosts:
        #     if self.NukesLeft > 10 and await self.has_ability(TACNUKESTRIKE_NUKECALLDOWN, ghost):
        #         nuke_ready = True
        #         break
        if ((self.supply_used > 180 or nuke_ready)and not self.target_of_assault
                and not self.thors):
            if self.enemy_structures and not self.enemy_structures.visible:
                self.target_of_assault = self.enemy_structures.random.position
        if self.target_of_assault and self.enemy_structures.visible:
            self.target_of_assault = None
        outpost = await self.get_outpost()
        units_to_fear = self.allEnemyUnits.of_type([BANELING, ZEALOT])
        ArmoredTargets = self.enemy_units_on_ground.filter(lambda x: x.is_armored)
        if self.minerals < 8000:
            secondary_targets = self.enemy_structures.filter(lambda x: x.is_visible)
        else:
            secondary_targets = self.enemy_structures
        secondary_target = None
        if self.general and secondary_targets:
            secondary_target = secondary_targets.closest_to(self.general)

        if self.cc.not_ready:
            CC_under_construction = True
            target_CC = self.cc.not_ready.closest_to(self.homeBase)
        else:
            CC_under_construction = False
        marauder_range = self.marauders[0].ground_range + self.marauders[0].radius
        for marauder in self.marauders:
            if await self.avoid_own_nuke(marauder):
                continue
            if await self.avoid_enemy_siegetanks(marauder):
                continue
            # dodge melee units
            if (marauder.weapon_cooldown != 0 and (units_to_fear.closer_than(5, marauder))):
                self.do(marauder.move(self.homeBase))
                continue
            if marauder.health_percentage < 1 / 3 and self.supply_used < 190 and self.medivacs.amount > 0:
                if marauder.position.to2.distance_to(self.homeBase.position.to2) > 10:
                    self.do(marauder.move(self.homeBase))
                    continue  # continue for loop, don't execute any of the following
            # check if enemy ground units exists
            if self.enemy_units_on_ground.amount > 1:
                if ArmoredTargets:
                    target = ArmoredTargets.closest_to(marauder)
                    if target.distance_to(marauder) < 9:
                        self.do(marauder.attack(target))
                        continue
                enemies_in_range = self.enemy_units_on_ground.closer_than(marauder_range, marauder)
                if enemies_in_range:
                    enemies_in_range_sorted = enemies_in_range.sorted(lambda x: (x.health + x.shield), reverse=False)
                    self.do(marauder.attack(enemies_in_range_sorted[0]))
                    continue
                else:
                    target = self.enemy_units_on_ground.closest_to(marauder)
                    self.do(marauder.attack(target.position))
                    continue
            elif len(self.allEnemyUnits.flying) > 2:
                if marauder.position.to2.distance_to(self.homeBase.position.to2) > 10:
                    self.do(marauder.move(self.homeBase))
                    continue  # continue for loop, don't execute any of the following
            if secondary_targets:
                if secondary_target:
                    self.do(marauder.attack(secondary_target))
                    continue

            "don't abandon siegetanks"
            if self.siegetanks_sieged:
                front_siege = self.siegetanks_sieged.closest_to(self.enemy_start_location)
                defence_position = front_siege.position.towards(self.enemy_start_location, 5)
                if marauder.distance_to(defence_position) > 7:
                    self.do(marauder.move(defence_position.random_on_distance(5)))
                continue
            # if no enemies, but thor exists then follow it
            if self.general and self.thors:
                if marauder.distance_to(self.general) > 10:
                    self.do(marauder.move(self.general))
                    continue
            if self.target_of_assault:
                self.do(marauder.attack(self.target_of_assault.position))
                continue
            if CC_under_construction:
                if marauder.position.to2.distance_to(target_CC.position.to2) > 8:
                    self.do(marauder.move(target_CC))
                continue  # continue for loop, don't execute any of the following
            if marauder.position.to2.distance_to(outpost.position.to2) > 10:
                self.do(marauder.move(outpost))
                continue  # continue for loop, don't execute any of the following

    async def move_squad(self):
        if not self.squad_group:
            return
        if self.iteraatio % 5 == 0:
            defend_location = await self.get_next_expansion_to_defend()
        else:
            defend_location = None
        units_to_ignore_marine = [ADEPTPHASESHIFT, EGG, LARVA]
        squad_center = self.squad_group.center
        valid_enemies = (self.allEnemyUnits.filter(lambda x: x.type_id not in units_to_ignore_marine and x.distance_to(squad_center) < 15))
        all_units_firing = True
        marine_scan = True
        if valid_enemies:
            closest_enemy = valid_enemies.closest_to(squad_center)
        for unit in self.squad_group:
            if unit.weapon_cooldown == 0:
                all_units_firing = False
            if (unit.did_take_first_hit
                    and self.ccANDoc
                    and not self.allEnemyUnits.closer_than(20, unit)
                    and marine_scan):
                for cc in self.ccANDoc:
                    if await self.has_ability(SCANNERSWEEP_SCAN, cc):
                        self.do(self.homeBase(AbilityId.SCANNERSWEEP_SCAN, unit.position))
                        print("Scan for cloaked units!")
                        marine_scan = False
                        break
        for unit in self.squad_group:
            if valid_enemies:
                if all_units_firing:
                    self.do(unit.move(squad_center.towards(closest_enemy, -5)))
                    continue
                else:
                    self.do(unit.attack(closest_enemy))
                    continue
            elif defend_location:
                if squad_center.distance_to(defend_location) > 5:
                    self.do(unit.attack(defend_location))
        if defend_location:
            if squad_center.is_closer_than(5, defend_location) and self.has_creep(defend_location):
                scanner = self.orbitalcommand.closest_to(self.start_location)
                if scanner.energy > 50 and await self.has_ability(SCANNERSWEEP_SCAN, scanner):
                        self.do(scanner(AbilityId.SCANNERSWEEP_SCAN, defend_location))
                        await self._client.chat_send("Clear this mining site boys!.", team_only=False)
                        return

    async def move_marines(self):
        units_to_ignore_marine = [ADEPTPHASESHIFT, EGG, LARVA]
        units_to_fear = self.allEnemyUnits.of_type([ZERGLING, BANELING, ZEALOT])
        bunker = None
        visible_enemy_structures = self.enemy_structures.filter(lambda x: x.is_visible)
        marines_reloading = 0
        threat_to_home = None
        charge = False
        distance_to_main_ramp = self.start_location.distance_to(self.main_base_ramp.top_center)
        valid_enemies = (self.allEnemyUnits.filter(
            lambda x: not x.is_structure and x.type_id not in units_to_ignore_marine) | visible_enemy_structures.filter(
            lambda x: x.can_attack_ground or x.can_attack_air))
        if self.reapers:
            reaper = self.reapers.furthest_to(self.start_location)

        if self.marines.ready.amount >= 8 and not self.squad_group and not self.marine_drop and not self.wall_in:
            counter = 0
            for unit in self.marines.ready:
                self.add_unit_to_squad_group(unit)
                counter += 1
                if counter >= 6:
                    break
            print(counter, "marines added to hit squad.")

        if self.allEnemyUnits:  # and not self.careful_marines:
            if self.we_are_winning() or self.supply_used > 180:
                charge = True
            marines_health = 0
            enemy_health = 0
            for unit in self.marines:
                marines_health += unit.health
            for unit in self.allEnemyUnits.not_structure:
                enemy_health += unit.health
            if marines_health > enemy_health:
                charge = True
        if valid_enemies:
            threat_to_home = valid_enemies.closest_to(self.start_location)
        if self.bunkers.ready:
            for bunker_ in self.bunkers.ready.sorted_by_distance_to(self.start_location):
                if await self.has_ability(LOAD_BUNKER, bunker_):
                    bunker = bunker_
                    break
        marine_scan = True
        for marine in self.marines.filter(lambda x: not x.is_in_squad):
            if marine.weapon_cooldown != 0:
                marines_reloading += 1
            if (marine.did_take_first_hit and self.ccANDoc
                    and not self.allEnemyUnits.closer_than(20, marine) and marine_scan):
                for cc in self.ccANDoc:
                    if await self.has_ability(SCANNERSWEEP_SCAN, cc):
                        self.do(self.homeBase(AbilityId.SCANNERSWEEP_SCAN, marine.position))
                        print("Marine: Scan for cloaked units!")
                        marine_scan = False
                        break
        for marine in self.marines.filter(lambda x: not x.is_in_squad):
            if marine.weapon_cooldown != 0 and valid_enemies.closer_than(17, marine):  # Stim when in combat
                if (marine.health_percentage >= 1
                        and await self.can_cast(marine, AbilityId.EFFECT_STIM_MARINE)
                        and not marine.has_buff(BuffId.STIMPACK)):
                    self.do(marine(AbilityId.EFFECT_STIM_MARINE))
                    continue  # continue for loop, dont execute any of the following
            if (self.marine_drop
                    and self.dropship_sent
                    and valid_enemies.closer_than(marine.ground_range + marine.radius, marine)):
                targets = valid_enemies.closer_than(marine.ground_range + marine.radius, marine
                                                    ).sorted(lambda x: (x.health + x.shield), reverse=False)
                target = targets[0]
                self.do(marine.attack(target))
                continue
            if await self.avoid_own_nuke(marine):
                continue
            if await self.avoid_enemy_siegetanks(marine):
                continue

            # Back off marines if self.careful_marines or there is melee units
            if (self.marines.amount < 4
                    and marine.weapon_cooldown != 0
                    and self.enemy_units
                    and self.supplydepots.amount < 3):
                self.do(marine.move(self.homeBase.position.towards(self.enemy_units.closest_to(marine), -10)))
                continue

            if not charge and valid_enemies:
                if ((marines_reloading >= 8 and self.careful_marines)):
                    self.do(marine.move(marine.position.towards(valid_enemies.closest_to(marine), -1)))
                    continue
                if ((marines_reloading >= 4 or marine.weapon_cooldown != 0)
                    and units_to_fear.closer_than(8, marine)
                    and not self.wall_in):
                    self.do(marine.move(marine.position.towards(valid_enemies.closest_to(marine), -1)))
                    continue

            # retreat if low health
            if (marine.health_percentage < 1 / 3
                    and not self.home_in_danger
                    and self.maxmedivacs > 0
                    and self.max_starports > 0
                    and self.supply_used < 180):
                panic_targets = valid_enemies.closer_than(4, marine)
                if panic_targets:
                    targets = panic_targets.sorted(
                        lambda x: (x.health + x.shield), reverse=False)
                    weakest_valid_enemy = targets[0]
                    self.do(marine.attack(weakest_valid_enemy))
                    continue
                elif marine.distance_to(self.homeBase) > 15:
                    self.do(marine.move(self.homeBase.position))
                    continue
                else:
                    continue

            if valid_enemies:
                closest_valid_enemy = valid_enemies.closest_to(marine)
                if closest_valid_enemy.distance_to(marine) < 17:
                    if marines_reloading < 4 or not charge:
                        if closest_valid_enemy.distance_to(marine) < (marine.ground_range + marine.radius):
                            targets = valid_enemies.closer_than((marine.ground_range + marine.radius), marine).sorted(
                                lambda x: (x.health + x.shield), reverse=False)
                            closest_valid_enemy = targets[0]
                        self.do(marine.attack(closest_valid_enemy))
                        continue
                    else:
                        enemies_at_long_range = valid_enemies.closer_than(17, marine).sorted(
                            lambda x: (x.health + x.shield), reverse=False)
                        target = enemies_at_long_range[0]
                        self.do(marine.move(target.position.towards(marine, -2)))
                        continue
            if threat_to_home:  # this makes marines to run all across the map to home. remove?
                self.do(marine.attack(threat_to_home.position))
                continue  # continue for loop, don't execute any of the following
            if visible_enemy_structures:
                target_structure = visible_enemy_structures.closest_to(marine)
                if marines_reloading >= 4:
                    self.do(marine.move(target_structure.position))
                    continue  # continue for loop, don't execute any of the following
                else:
                    self.do(marine.attack(target_structure.position))
                    continue  # continue for loop, don't execute any of the following
            if bunker:
                self.do(marine.move(bunker.position))
                continue
            elif self.general:
                if marine.distance_to(self.general) > 7:
                    self.do(marine.move(self.general))
                    continue
            elif self.natural and not self.wall_in:
                marinehome = self.natural.towards(self.game_info.map_center, 6)
                if marine.distance_to(marinehome) > 10:
                    self.do(marine.move(marinehome))
                continue  # causes marines to jitter
            else:
                marinehome = self.homeBase
                if marine.distance_to(marinehome) > 10:
                    self.do(marine.move(marinehome))
                continue  # causes marines to jitter

    async def get_homeBase(self):
        if self.homeBase != None:
            return self.homeBase
        if self.ccANDoc:
            self.homeBase = self.ccANDoc.closest_to(self.start_location)
        if not self.homeBase:
            self.homeBase = self.start_location
        return self.homeBase

    async def get_outpost(self):
        if self.outpost != None:
            return self.outpost
        if not self.ccANDoc:
            return self.start_location
        if self.ccANDoc.amount == 2:
            self.outpost = self.ccANDoc.furthest_to(self.start_location)
        elif self.enemy_structures.exists:
            enemyOutpost = self.enemy_structures.closest_to(self.homeBase)
            self.outpost = self.ccANDoc.closest_to(enemyOutpost)
        else:
            ops = self.ccANDoc.sorted(lambda x: x.distance_to(self.start_location), reverse=True)
            self.outpost = ops[0]  # furthest commandcenter from starting position
        return self.outpost

    async def repair_planetaries(self):
        for PF in self.structures(UnitTypeId.PLANETARYFORTRESS):
            if PF.did_take_first_hit:
                for scv in self.scvs.closer_than(10, PF):
                    self.do(scv(EFFECT_REPAIR_SCV, PF))


    async def call_for_mules(self):
        if self.ccANDoc.ready:
            ##            if self.already_pending(COMMANDCENTER):
            ##                return
            random_cc = random.choice(self.ccANDoc.ready)
            if self.scan_cloaked_enemies:
                energy_limit_to_mule = 90
            else:
                energy_limit_to_mule = 60
            cloaked_enemy_units = self.enemy_units.filter(lambda x: x.is_cloaked)
            if cloaked_enemy_units:
                #print(cloaked_enemy_units.random)
                for oc in self.orbitalcommand.filter(lambda x: x.energy > 50):
                    self.do(oc(AbilityId.SCANNERSWEEP_SCAN,
                               cloaked_enemy_units.random.position))
            for oc in self.orbitalcommand.filter(lambda x: x.energy >= energy_limit_to_mule):
                mfs = None
                if self.scan_enemy_base and self.enemy_start_location != None and self.ccANDoc.amount >= 2:
                    self.do(oc(AbilityId.SCANNERSWEEP_SCAN,
                               self.enemy_start_location.towards(self.game_info.map_center, 4)))
                    self.scan_enemy_base = False
                elif not self.already_pending(COMMANDCENTER):
                    outpost = await self.get_outpost()
                    mfs = self.mineral_field.closer_than(10, outpost)
                if not mfs:
                    mfs = self.mineral_field.closer_than(10, random_cc)
                if mfs:
                    mf = max(mfs, key=lambda x: x.mineral_contents)
                    self.do(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))
                if self.reapers_left == 0 and not self.enemy_structures and not self.scan_enemy_base:
                    self.reapers_left = self.reapers_left - 1
                    self.scan_enemy_base = True

    async def evac_orbital(self):
        for cc in self.orbitalcommand:
            if (self.wall_in and not self.mineral_field.closer_than(7, cc)): # needs to be atleast 7 to pevent hamebase to lift up
            # if (not self.mineral_field.closer_than(7, cc)): # needs to be atleast 7 to pevent hamebase to lift up
                abilities = await self.get_available_abilities(cc)
                # print(abilities)
                #print(len(cc.orders))
                if len(cc.orders) != 0:
                    self.do(cc(CANCEL_QUEUECANCELTOSELECTION))
                self.do(cc(LIFT, queue=True))
                expand = await self.get_next_expansion()
                if not expand:
                    expand = random.choice(self.vespene_geyser)
                    expand = await self.find_placement(UnitTypeId.COMMANDCENTER,
                                                       near=expand.position.random_on_distance(8))
                self.do(cc(LAND, expand, queue=True))
                return
            is_in_expansion_location = False
            for expansion in self.expansion_locations:
                if cc.position.distance_to(expansion) < 3:
                    is_in_expansion_location = True
                    break
            if not is_in_expansion_location:
                if len(cc.orders) != 0:
                    self.do(cc(CANCEL_QUEUECANCELTOSELECTION))
                self.do(cc(LIFT, queue=True))

    async def build_workers(self, maxscv):
        "Make supplydepot after scv"
        if self.scvs.amount >= 13 and not self.already_pending(SUPPLYDEPOT) and self.supplydepots.amount == 0:
            return
        scvTotal = self.scvs.amount + (2 * self.ccANDoc.ready.amount)  # refineries hide scvs while gathering gas.

        "Slowdown scv production if under attack"
        if self.enemy_units.closer_than(self.defence_radius, self.homeBase).amount > 1:
            if self.already_pending(SCV) and not self.greedy_scv_consrtuction:
                return

        scv_in_production = 0
        for cc in self.orbitalcommand:
            if len(cc.orders) != 0:
                if cc.orders[0].ability.id in [AbilityId.COMMANDCENTERTRAIN_SCV]:
                    scv_in_production += 1
                    #scvTotal = scvTotal + len(cc.orders)

        if scv_in_production >= self.scv_build_speed:
            return
        if self.FastReaper == True and self.scvs.amount > 5:
            if self.supplydepots.amount == 0 and not self.already_pending(SUPPLYDEPOT):
                return

            "Wait until barracks production is started, before continuing scv production."
            "If we are worker rushed this rule needs to be ignored. (not self.home_in_danger)"
            if self.refineries.amount == 1 and self.barracks.amount == 0 and not self.home_in_danger:
                return
        if (self.can_afford(SCV) and self.supply_used < 190 and self.supply_left > 0 and self.mineral_field.filter(lambda x: x.is_visible)):
            if scvTotal < maxscv:
                for cc in self.ccANDoc.idle:
                    if (cc.assigned_harvesters > cc.ideal_harvesters and self.ccANDoc.amount != 1 and not self.greedy_scv_consrtuction):
                        continue
                    if (cc.health_percentage < 1
                            or not self.mineral_field.closer_than(10,cc)):
                        continue
                    self.do(cc.train(SCV))
                    return
            else:
                self.bonus_scv_in_start = 0

    async def closest_ramp_to(self, unit):
        ramp = min(
            (ramp for ramp in self.game_info.map_ramps),
            key=lambda r: unit.position.distance_to(r.top_center),
        )
        return ramp

    async def find_potential_supplydepot_locations(self, location):
        p = location.position
        return [
            Point2((p.x - 2.5, p.y - 2.5)),
            Point2((p.x - 2.5, p.y + 2.5)),
            Point2((p.x + 4.5, p.y - 2.5)),
            Point2((p.x + 4.5, p.y + 2.5)),
        ]

    async def find_placement_for_supplydepot(self):
        for structure in (self.barracks | self.factories | self.starports
                          | self.engineeringbays | self.armories
                          | self.ghost_academies | self.fusioncores):
            potential_supplydepot_locations = await self.find_potential_supplydepot_locations(structure)
            for location in potential_supplydepot_locations:
                if await self.can_place(SUPPLYDEPOT, location):
                    return location
        return None

    async def middle_depot_location(self):
        depot_placement_positions = self.main_base_ramp.corner_depots
        d1 = depot_placement_positions.pop()
        d2 = depot_placement_positions.pop()
        d = 2
        if d1.x < d2.x:
            x_position = d1.x + d
        else:
            x_position = d1.x - d
        if d2.y < d1.y:
            y_position = d2.y + d
        else:
            y_position = d2.y - d
        target_depot_location = Point2((x_position, y_position))
        if not await self.can_place(SUPPLYDEPOT, target_depot_location):
            if d1.x < d2.x:
                x_position = d2.x - d
            else:
                x_position = d2.x + d
            if d2.y < d1.y:
                y_position = d1.y - d
            else:
                y_position = d1.y + d
            target_depot_location = Point2((x_position, y_position))
        if await self.can_place(SUPPLYDEPOT, target_depot_location):
            return target_depot_location
        else:
            return None

    async def safkaa(self):
        if self.home_in_danger:
            return
        if self.minerals < 110 or not self.ccANDoc or not self.scvs:
            return
        if self.marine_drop and self.supplydepots.amount == 2 and not self.starports:
            return
        if self.super_greed and self.supplydepots:
            return
        if (self.supplydepots.amount == 1
                and self.ccANDoc.amount == 1
                and self.first_base_saturation < 0
                and not self.build_bunker):
            return
        if self.ccANDoc.ready.amount == 1:
            max_pending_sd = 1
        elif self.more_depots:
            max_pending_sd = 3
        else:
            max_pending_sd = 2
        if self.wall_in and self.supplydepots.amount < 3 and self.barracks:
            multiplier = 100
        elif self.FastReaper:
            multiplier = 3
        else:
            multiplier = 5
        sds_in_production = self.already_pending(SUPPLYDEPOT)

        if sds_in_production < max_pending_sd and self.supplydepots.amount < 20:
            if self.supply_left < (max_pending_sd - sds_in_production) * multiplier:
                if self.supplydepots.amount < 5:
                    depot_placement_positions = self.main_base_ramp.corner_depots
                    # Choose any depot location
                    if not self.midle_depo_position:
                        self.midle_depo_position = await self.middle_depot_location()
                    if depot_placement_positions:
                        for pos in depot_placement_positions:
                            if await self.can_place(SUPPLYDEPOT, pos):
                                await self.build(SUPPLYDEPOT, pos, build_worker=self.select_contractor(pos))
                                print("supply depos total", (len(self.supplydepots.ready) + sds_in_production + 1))
                                return
                if not self.wall_tank_pos:
                    closest_ramp = await self.closest_ramp_to(self.midle_depo_position)
                    self.wall_tank_pos = self.midle_depo_position.towards(closest_ramp.bottom_center, -6)
                if await self.can_place(SUPPLYDEPOT, self.midle_depo_position):
                    build_worker = self.select_contractor(self.midle_depo_position)
                    await self.build(SUPPLYDEPOT, self.midle_depo_position, build_worker)
                    return
                elif self.ccANDoc.ready.amount <= 3:
                    for command in self.ccANDoc:
                        build = True
                        for suply in self.supplydepots:
                            if suply.position.to2.distance_to(command.position.to2) < 11:
                                build = False
                                break
                        if build:
                            await self.build(SUPPLYDEPOT, near=command.position.towards(self.game_info.map_center, 8),
                                             build_worker=self.scvs.random)
                            print("Building supplydepot", (len(self.supplydepots.ready) + sds_in_production + 1))
                            return
                location = await self.find_placement_for_supplydepot()
                if location:
                    await self.build(SUPPLYDEPOT, location, build_worker=self.select_contractor(location))
                    print("Building supplydepot", (len(self.supplydepots.ready) + sds_in_production + 1))
                    return
                expand = random.choice(self.supplydepots)
                await self.build(SUPPLYDEPOT, near=expand.position.random_on_distance(10),
                                 build_worker=self.select_contractor(expand))
                print("Building supplydepot", (len(self.supplydepots.ready) + sds_in_production + 1))

    async def build_refinery(self):
        if self.home_in_danger:
            return
        if self.minerals < self.vespene + 100:  # we have enough vespene. No refinery needed.
            return
        if self.super_greed: # and self.refineries:
            return
        if not self.expand_for_vespene and self.vespene > 500:
            return
        if self.barracks or (self.FastReaper and self.supplydepots.exists) or (self.fast_vespene and self.supplydepots):
            if not self.rush_possible and self.mech_build:
                maxrefinery = 100
            elif self.ccANDoc.amount == 1:
                if self.refineries_in_first_base == 2 and self.barracks.ready:
                    maxrefinery = self.refineries_in_first_base
                elif self.refineries_in_first_base > 0:
                    maxrefinery = 1
                else:
                    maxrefinery = 0
            elif self.limit_vespene:
                if self.vespene > 300:
                    return
                if self.already_pending(REFINERY):
                    return
                if self.ccANDoc.amount == 1:
                    maxrefinery = self.refineries_in_first_base
                else:
                    maxrefinery = self.ccANDoc.amount * 2 - 2
            else:
                maxrefinery = 100

            if self.refineries.amount < maxrefinery:
                await self.execute_build_refinery()

    async def execute_build_refinery(self):
        if self.rush_possible and (self.ccANDoc.amount + self.townhalls_flying.amount) < 4:
            max_pending_refineries = 1
        else:
            max_pending_refineries = 2
        if self.minerals < 75:
            return
        for cc in self.ccANDoc.ready:
            if cc.health_percentage < 1:
                continue
            gasmines = self.vespene_geyser.closer_than(10.0, cc)
            for gasmine in gasmines:
                if not self.refineries.closer_than(1.0, gasmine).exists:
                    worker = self.select_build_worker(gasmine)
                    if worker is None:
                        return
                    if (self.already_pending(REFINERY) + self.already_pending(
                            UnitTypeId.REFINERYRICH)) >= max_pending_refineries:
                        return
                    self.do(worker.build(REFINERY, gasmine))
                    return

    "returns false in needs to save minerals"

    async def perform_barracks_switch(self):
        if not self.barracks_switch:
            return True
        if self.barracks_switch == True:
            if not self.barracks and not self.barracksflyings and self.can_afford(BARRACKS):
                await self.build_for_me()
            for doner in self.barracks.ready:
                if (doner.has_add_on
                        and not self.already_pending(BARRACKSTECHLAB)
                        and not self.already_pending(BARRACKSREACTOR)):
                    self.barracks_switch = doner.position
                    return False
        elif self.barracksflyings.idle:
            if self.can_afford(STARPORT):
                await self.build_for_me(STARPORT)
                self.barracks_switch = False
            return False
        else:
            for doner in self.barracks.ready.idle:
                self.do(doner(LIFT, queue=True))
                self.do(doner.move(self.barracks_switch.towards(self.game_info.map_center, 5), queue=True))
        return True

    async def fast_hellions_build_order(self):
        if not self.refineries and self.supplydepots:
            await self.execute_build_refinery()
            return
        if self.supplydepots.ready.exists:
            if len(self.barracks | self.barracksflyings) < 1:
                if self.can_afford(BARRACKS):
                    await self.build_for_me(BARRACKS)
                return
            elif (self.factories.amount + self.factoriesflying.amount) == 0:
                if self.can_afford(FACTORY) and not self.already_pending(FACTORY) and self.barracks.ready.exists:
                    await self.build_for_me(FACTORY)
                    return
            elif not self.armories:
                if self.can_afford(ARMORY) and self.factories.ready.exists and self.factory_reactors:
                    await self.build_for_me(ARMORY)
                return
            else:
                self.fast_hellions = False

    async def buildings(self, maxbarracks, iteration):
        if self.home_in_danger:
            return
        # if self.home_in_danger and self.supplydepots:
        #     if len(self.barracks | self.barracksflyings) < 1:
        #         if (not self.already_pending(BARRACKS)):
        #             if self.can_afford(BARRACKS):
        #                 await self.build_for_me(BARRACKS)
        #             return
        #     return
        if self.fast_hellions:
            await self.fast_hellions_build_order()
            return
        if not self.scvs:
            return
        if self.supplydepots.ready.exists:
            if self.barracks_switch and (self.marines.amount >= self.min_marine) and self.starports.amount >= 3:
                if not await self.perform_barracks_switch():
                    return
            if (not self.already_pending(MISSILETURRET)
                    and self.can_afford(MISSILETURRET)
                    and self.engineeringbays.ready.exists
                    and self.build_missile_turrets
                    and self.NukesLeft > 10
                    and len(self.structures(MISSILETURRET)) < 1):
                if not self.structures(MISSILETURRET).closer_than(10, self.homeBase):
                    await self.build(MISSILETURRET, near=self.homeBase.position.towards(self.game_info.map_center, 5),
                                     build_worker=self.scvs.random)
                    return
            if (len(self.barracks.ready | self.barracksflyings) + self.already_pending(UnitTypeId.BARRACKS)) < maxbarracks:
                if (not (not self.expand_for_vespene and self.structures(BARRACKS).amount >= self.max_barracks)):
                    pass
                if (not self.already_pending(BARRACKS)
                        or self.structures(BARRACKS).amount >= self.max_barracks
                        or self.FastReaper):
                    if self.can_afford(BARRACKS):
                        await self.build_for_me(BARRACKS)
                    return

            if self.super_greed:
                if self.enemy_units.closer_than(self.defence_radius, self.homeBase).amount > 1:
                    self.super_greed = False
                    await self._client.chat_send("I'm not ready. Come back after 6 minutes.", team_only=False)
                if self.supplydepots:
                    return

            if (self.FastReaper and not self.ReapersDone):
                return

            "build missile turrets to detect cloaked units."
            if (not self.already_pending(MISSILETURRET)
                    and self.can_afford(MISSILETURRET)
                    and self.engineeringbays.ready.exists):
                if self.build_missile_turrets:
                    for command in self.ccANDoc:
                        if not self.structures(MISSILETURRET).closer_than(10, command):
                            await self.build(MISSILETURRET, near=command.position.towards(self.game_info.map_center, 5),
                                             build_worker=self.scvs.random)
                            return
                if self.mineral_field_turret and self.ccANDoc.amount >= 2:
                    for command in self.ccANDoc:
                        if self.mineral_field.closer_than(10.0, command.position):
                            pos = self.mineral_field.closer_than(10.0, command.position).center
                            if not self.structures(MISSILETURRET).closer_than(5, pos):
                                await self.build(MISSILETURRET, near=pos, build_worker=self.scvs.random)
                                return

            if self.wall_tank:
                return

            elif (self.engineeringbays.amount < 1
                  and (self.fast_engineeringbay or self.ccANDoc.ready.amount >= 3)
                  and self.factories.ready):
                if self.can_afford(ENGINEERINGBAY) and not self.already_pending(ENGINEERINGBAY):
                    await self.build_for_me(ENGINEERINGBAY)
            elif (self.engineeringbays.amount < self.max_engineeringbays
                  and self.starports.ready
                  and self.armories):
                if self.can_afford(ENGINEERINGBAY) and not self.already_pending(ENGINEERINGBAY):
                    await self.build_for_me(ENGINEERINGBAY)

            elif (self.armories.ready.amount < 2
                  and not self.already_pending(ARMORY)
                  and self.engineeringbays.ready
                  and self.mech_build):
                if self.can_afford(ARMORY) and self.factories.ready.exists:
                    await self.build_for_me(ARMORY)

            elif ((self.factories.amount + self.factoriesflying.amount) < self.maxfactory
                  and (self.medivacs.amount >= 1 or (self.factories.amount + self.factoriesflying.amount) == 0)):
                if self.can_afford(FACTORY) and not self.already_pending(FACTORY) and self.barracks.ready.exists:
                    await self.build_for_me(FACTORY)
            elif ((self.factories.amount + self.factoriesflying.amount) < self.maxfactory
                  and self.maxmedivacs == 0 and self.starports.ready):
                if self.can_afford(FACTORY) and not self.already_pending(FACTORY) and self.barracks.ready.exists:
                    await self.build_for_me(FACTORY)
            elif ((self.factories.amount + self.factoriesflying.amount) < self.maxfactory
                  and self.max_starports == 0 and not self.factories.idle):
                if self.can_afford(FACTORY) and not self.already_pending(FACTORY) and self.barracks.ready.exists:
                    await self.build_for_me(FACTORY)

            elif (self.armories.ready.amount < 1
                  and not self.already_pending(ARMORY)
                  and self.engineeringbays
                  and self.build_armory
                  and self.factories.ready):
                if self.can_afford(ARMORY) and self.factories.ready.exists:
                    await self.build_for_me(ARMORY)

            elif (not self.fusioncores.ready
                  and self.starports
                  and self.last_phase
                  and (self.banshee_left - self.already_pending(BANSHEE)) <= 0
                  and self.max_BC > 0):
                if self.can_afford(FUSIONCORE) and not self.already_pending(FUSIONCORE):
                    await self.build_for_me(FUSIONCORE)

            elif ((self.starports.amount + self.starportflying.amount) < self.max_starports):
                if self.factories.ready.exists and self.can_afford(STARPORT) and not self.already_pending(STARPORT):
                    await self.build_for_me(STARPORT)

            elif (self.ghost_academies.amount < 2
                  and self.NukesLeft > 10
                  and self.starports.ready.amount > 0
                  and self.ccANDoc.ready.amount >=3):
                if self.can_afford(GHOSTACADEMY) and not self.already_pending(GHOSTACADEMY):
                    await self.build_for_me(GHOSTACADEMY)

            elif (self.factories.ready and not self.ghost_academies.exists and self.MaxGhost > 0 and self.supply_used > 150):
                if self.can_afford(GHOSTACADEMY) and not self.already_pending(GHOSTACADEMY):
                    await self.build_for_me(GHOSTACADEMY)

            elif (not self.fusioncores.ready.exists
                  and self.upgrade_liberator and self.already_pending(UnitTypeId.LIBERATOR)):
                if self.can_afford(FUSIONCORE) and not self.already_pending(FUSIONCORE):
                    await self.build_for_me(FUSIONCORE)

            # lift barracks or factory if threre is over 2 thors or tanks nearby
            if self.iteraatio % 50 == 0 and self.ccANDoc.ready.amount > 2:
                for sp in (self.factories.ready | self.barracks.ready | self.starports.ready):
                    machinery = (self.thors | self.siegetanks)
                    tooClose = machinery.closer_than(6, sp)
                    if len(tooClose) > 1:
                        self.do(sp(LIFT))
                        print("logistic factory lift")
                        break

    async def landbuildings(self):
        if not self.barracks_switch == False and not self.barracks_switch == True:
            return
        if self.doner_location:
            flyingStructures = self.barracksflyings
        else:
            flyingStructures = (self.factoriesflying | self.barracksflyings | self.starportflying)
        for flyStr in flyingStructures.idle:
            flyStrLoc = await self.find_placement_for_barracks()
            if flyStrLoc:
                self.do(flyStr(LAND, flyStrLoc))
                continue
            flyStrLoc = await self.find_placement(UnitTypeId.COMMANDCENTER,
                                                  near=flyStr.position.random_on_distance(10))
            if flyStrLoc:
                if self.doner_location:
                    if flyStrLoc.is_closer_than(8, self.doner_location):
                        return
                for x in range(-1, 1):
                    for y in range(-1, 1):
                        landLocation = flyStrLoc.position.offset((x, y))
                        if not await self.can_place(BARRACKS, landLocation):
                            return
                addonlocation = flyStrLoc.position.offset((3, -1))
                if await self.can_place(SUPPLYDEPOT, addonlocation):
                    self.do(flyStr(LAND, flyStrLoc))
        flyingStructures = (self.structures(COMMANDCENTERFLYING).idle | self.structures(ORBITALCOMMANDFLYING).idle)
        for cc in flyingStructures:
            expand = await self.get_next_expansion()
            if not expand:
                expand = random.choice(self.vespene_geyser)
                expand = await self.find_placement(UnitTypeId.COMMANDCENTER, near=expand.position.random_on_distance(8))
            self.do(cc(LAND, expand))
            continue

    async def military_units(self, maxreaper, maxbarracks):
        reaperTotal = 0
        marineTotal = 0
        marauderTotal = 0
        haamu = 0

        # count all reapers and marines alive and in production
        for barracks in self.barracks.ready:
            for order in barracks.orders:
                if order.ability.id in [AbilityId.BARRACKSTRAIN_REAPER]:
                    reaperTotal = reaperTotal + 1
                elif order.ability.id in [BARRACKSTRAIN_MARINE]:
                    marineTotal = marineTotal + 1
                elif order.ability.id in [BARRACKSTRAIN_MARAUDER]:
                    marauderTotal = marauderTotal + 1
                elif order.ability.id in [BARRACKSTRAIN_GHOST]:
                    haamu += 1
        reaperTotal = reaperTotal + self.reapers.amount
        marineTotal = marineTotal + self.marines.amount
        marauderTotal = marauderTotal + self.marauders.amount
        haamu = haamu + self.ghosts.amount

        # build units in barracs
        if self.home_in_danger:
            for barracks in self.barracks:
                if len(barracks.orders) < 2:
                    self.do(barracks.train(MARINE))
                return
        elif marineTotal < self.min_marine:
            minerals_for_marine = 75
        elif self.marines_last_resort:
            minerals_for_marine = 470
        else:
            minerals_for_marine = 300
        need_marines_for_bunker = False
        for bunker in self.bunkers.ready:
            if await self.has_ability(LOAD_BUNKER, bunker):
                need_marines_for_bunker = True
        if (self.already_pending(BARRACKSREACTOR)
                or self.already_pending(BARRACKSTECHLAB)
                or need_marines_for_bunker):
            can_build_add_on = False
        else:
            can_build_add_on = True
        for br in self.barracks.ready:
            if not (self.barracks_switch == False) and not (self.barracks_switch == True):
                continue
            machinery = (self.thors | self.siegetanks)
            tooClose = machinery.closer_than(6, br)
            ## prepare for lift if too many machines near
            if len(tooClose) > 1:
                continue
            # train reapers up to maxreaper
            if len(br.orders) >= 2:
                continue
            if len(br.orders) >= 1 and br.add_on_tag == 0:
                continue
            if reaperTotal == 3:
                self.ReapersDone = True
            if self.ReapersDone and reaperTotal < 3 and self.FastReaper or self.minerals > 2000:
                self.FastReaper = False
            if reaperTotal < maxreaper and self.refineries and not self.marine_drop and (self.reapers_left > 0 or maxreaper > 1):
                if self.can_afford(REAPER) and self.supply_left > 0:
                    self.do(br.train(REAPER))
                    print("Training reaper")
                    self.reapers_left = self.reapers_left - 1
                break
            if self.FastReaper and reaperTotal < maxreaper:
                break

            if (can_build_add_on
                    and br.add_on_tag == 0
                    and br.health_percentage >= 1
                    and (self.factories or self.barracks.amount > 2)):
                if self.wall_in and self.ccANDoc.amount == 1:
                    pass
                elif self.can_afford(BARRACKSREACTOR):
                    location = br.position.offset((2.5, -0.5))
                    if await self.can_place(AUTOTURRET, location):
                        if (not self.expand_for_vespene and self.barracks.ready.amount > self.max_barracks):
                            self.do(br.build(BARRACKSREACTOR))
                        elif self.barracks_reactor_first:
                            if self.structures(BARRACKSREACTOR).amount == 0:
                                self.do(br.build(BARRACKSREACTOR))
                            else:
                                self.do(br.build(BARRACKSTECHLAB))
                            break
                        elif self.structures(BARRACKSTECHLAB).amount != 0 and self.structures(
                                BARRACKSREACTOR).amount == 0:
                            self.do(br.build(BARRACKSREACTOR))
                        else:
                            self.do(br.build(BARRACKSTECHLAB))
                        break
                    else:
                        self.do(br(LIFT))
                        break
            if marauderTotal < self.maxmarauder and self.can_afford(MARAUDER) and await self.has_ability(
                    BARRACKSTRAIN_MARAUDER, br):
                self.do(br.train(MARAUDER))
                print("Training marauder")
                marauderTotal = marauderTotal + 1
                break
            if (haamu < self.MaxGhost and (not self.already_pending(GHOST) or self.NukesLeft > 10)
                    and self.can_afford(GHOST) and await self.has_ability(BARRACKSTRAIN_GHOST, br)):
                self.do(br.train(GHOST))
                print("Training ghost")
                break
            if marineTotal < self.max_marine:
                istechlab = False
                for addon in self.structures(BARRACKSTECHLAB):
                    if br.add_on_tag == addon.tag:
                        istechlab = True
                        break
                if self.minerals < minerals_for_marine or not self.can_feed(MARINE):
                    continue
                if self.supply_used > 190 and not (self.max_thor == 0 and self.max_BC == 0):
                    continue
                if not istechlab or (self.marauders.amount + self.already_pending(UnitTypeId.MARAUDER)) >= self.maxmarauder:
                    self.do(br.train(MARINE))
                    break

        tanks_in_production = 0
        hellions_in_production = 0
        cyclones_in_production = 0
        mines_in_production = 0
        for factory in self.factories.ready:
            for order in factory.orders:
                if order.ability.id in [AbilityId.FACTORYTRAIN_SIEGETANK]:
                    tanks_in_production += 1
                if order.ability.id in [AbilityId.FACTORYTRAIN_HELLION]:
                    hellions_in_production += 1
                if order.ability.id in [AbilityId.TRAIN_CYCLONE]:
                    cyclones_in_production += 1
                if order.ability.id in [AbilityId.FACTORYTRAIN_WIDOWMINE]:
                    mines_in_production += 1
        thorTotal = self.thors.amount + self.already_pending(UnitTypeId.THOR)
        siegeTankTotal = tanks_in_production + self.siegetanks.amount + self.siegetanks_sieged.amount
        machinery = (self.thors | self.siegetanks)
        for factory in self.factories.ready:
            if len(factory.orders) > 1:
                continue
            if len(factory.orders) == 1:
                for reactor in self.factory_reactors:
                    if not factory.add_on_tag == reactor.tag:
                        continue

            if machinery.closer_than(6, factory).amount > 1:
                continue
            # build techlabs for factories

            if (self.hellion_left > 3 or self.agressive_mines) and factory.add_on_tag == 0:
                if not self.structures(FACTORYREACTOR):
                    location = factory.position.offset((2.5, -.5))
                    if await self.can_place(SUPPLYDEPOT, location):
                        if not self.structures(FACTORYREACTOR):
                            self.do(factory.build(FACTORYREACTOR))
                    elif self.iteraatio % 6 == 0:
                        self.do(factory(LIFT))
                    break

            has_reactor = False
            for reactor in self.factory_reactors:
                if factory.add_on_tag == reactor.tag:
                    has_reactor = True
                    break
            has_techlab = False
            for techlab in self.factory_techlabs:
                if factory.add_on_tag == techlab.tag:
                    has_techlab = True
                    break
            if self.agressive_mines and has_reactor:
                if (self.can_afford(WIDOWMINE)
                        and self.can_feed(WIDOWMINE)):
                    self.do(factory.train(WIDOWMINE))
                    print("Training mine")
                    break
                continue
            if self.mines_left > 0 and not self.already_pending(WIDOWMINE) and (not self.mines or has_reactor):
                if self.can_afford(WIDOWMINE) and self.can_feed(WIDOWMINE):
                    self.do(factory.train(WIDOWMINE))
                    print("Training mine")
                    break
                continue
            if (self.hellion_left > 0
                    and not self.wall_tank
                    and (not self.already_pending(HELLION) or factory.add_on_tag in self.factory_reactors.tags)):
                if (self.can_afford(HELLION)
                        and self.can_feed(HELLION)
                        and await self.has_ability(FACTORYTRAIN_HELLION, factory)):
                    self.do(factory.train(HELLION))
                    print("Training hellion")
                    break
                continue
            elif (len(factory.orders) == 0 and self.factory_reactors
                  and (self.hellion_left <= 0 and not self.agressive_mines)):
                for reactor in self.factory_reactors:
                    if factory.add_on_tag == reactor.tag:
                        self.do(factory(LIFT))
                        break
            elif factory.add_on_tag == 0 and not self.marine_drop:
                if self.can_afford(FACTORYTECHLAB) and factory.health_percentage >= 1:
                    location = factory.position.offset((2.5, -.5))
                    if await self.can_place(SUPPLYDEPOT, location):
                        self.do(factory.build(FACTORYTECHLAB))
                    elif self.iteraatio % 6 == 0:
                        self.do(factory(LIFT))
                    break
            if self.mines_left > 0 and not self.already_pending(UnitTypeId.WIDOWMINE) and self.factories.amount > 1:
                if self.can_afford(WIDOWMINE) and self.can_feed(WIDOWMINE):
                    self.do(factory.train(WIDOWMINE))
                    print("Training mine")
                    break
            else:
                if (self.cyclone_left > 0
                        and (cyclones_in_production == 0 or siegeTankTotal >= self.maxsiege)
                        and self.supply_used < 190
                        and len(factory.orders) == 0 and has_techlab):
                    if self.can_afford(CYCLONE) and self.can_feed(CYCLONE):
                        self.do(factory.train(CYCLONE))
                        print("Training cyclone")
                        break
                if (self.can_afford(SIEGETANK) and self.can_feed(SIEGETANK) and len(factory.orders) == 0
                        and siegeTankTotal < self.maxsiege
                        and (self.supply_used < 190 or (self.max_thor == 0 and self.max_BC == 0))):
                    if self.wall_in and siegeTankTotal >= 2:
                        pass
                    else:
                        self.do(factory.train(SIEGETANK))
                        print("Training siegetank")
                        break
                if (self.can_afford(THOR) and self.can_feed(THOR) and not self.wall_in
                        and self.armories.ready.exists and thorTotal < self.max_thor):
                    self.do(factory.train(THOR))
                    print("Training THOR")
                    break

        banshees_in_production = 0
        medis_in_production = 0
        vikings_in_production = 0
        ravens_in_production = 0
        enemy_airunits = [UnitTypeId.VIKING, UnitTypeId.VIKINGASSAULT]
        enemy_airunits = self.enemy_units.of_type(enemy_airunits)
        if enemy_airunits and self.adaptive_viking_count:
            enemy_airunits_amount = enemy_airunits.amount + 3
            if enemy_airunits_amount > self.max_viking:
                self.max_viking = enemy_airunits_amount
                print("Increase viking count to:", self.max_viking)
        for starport in self.starports.ready:
            for order in starport.orders:
                order_id = order.ability.id
                if order_id in [AbilityId.STARPORTTRAIN_BANSHEE]:
                    banshees_in_production += 1
                if order_id in [AbilityId.STARPORTTRAIN_MEDIVAC]:
                    medis_in_production += 1
                if order_id in [AbilityId.STARPORTTRAIN_VIKINGFIGHTER]:
                    vikings_in_production += 1
                if order_id in [AbilityId.STARPORTTRAIN_RAVEN]:
                    ravens_in_production += 1
        mediTotal = self.medivacs.amount + medis_in_production
        vikingTotal = self.vikings.amount + self.vikingassault.amount + vikings_in_production
        ravenTotal = self.units(RAVEN).amount + ravens_in_production
        if self.marine_drop:
            build_medivacs = False
        else:
            build_medivacs = True

        for starport in self.starports.ready:
            tooClose = machinery.closer_than(6, starport)
            #            self.do(starport(AbilityId.RALLY_BUILDING, self.homeBase))
            if len(starport.orders) > 1:
                continue
            if len(tooClose) > 1:
                continue
            if self.can_afford(BANSHEE) and await self.has_ability(STARPORTTRAIN_BANSHEE, starport) and len(
                    starport.orders) != 0:
                continue
            elif starport.add_on_tag == 0 and starport.health_percentage >= 1:
                if (self.can_afford(STARPORTTECHLAB)
                        and self.build_starportreactor
                        and not self.structures(STARPORTREACTOR)
                        and not self.already_pending(STARPORTREACTOR)):
                    location = starport.position.offset((2.5, -0.5))
                    if await self.can_place(SUPPLYDEPOT, location):
                        self.do(starport.build(STARPORTREACTOR))
                        break
                    elif self.iteraatio % 6 == 0:
                        self.do(starport(LIFT))
                        break
            if ((mediTotal < self.maxmedivacs
                 and self.upgrade_marine
                 and build_medivacs
                 and not self.already_pending(MEDIVAC))
                    or (mediTotal < 1 and self.maxmedivacs > 0)):
                if self.can_afford(MEDIVAC) and self.can_feed(MEDIVAC):
                    print("Training medivac")
                    self.do(starport.train(MEDIVAC))
                break
            elif vikingTotal < 0 and self.max_viking > 0:
                if self.can_afford(VIKINGFIGHTER) and self.can_feed(VIKINGFIGHTER):
                    self.do(starport.train(VIKINGFIGHTER))
                    print("Training viking")
                    break
            elif starport.add_on_tag == 0 and starport.health_percentage >= 1:
                if self.can_afford(STARPORTTECHLAB):
                    location = starport.position.offset((2.5, -0.5))
                    if await self.can_place(SUPPLYDEPOT, location):
                        self.do(starport.build(STARPORTTECHLAB))
                        break
                    elif self.iteraatio % 6 == 0:
                        self.do(starport(LIFT))
                        break
            elif self.raven_left > 0 and ravenTotal <= 0 and await self.has_ability(STARPORTTRAIN_RAVEN, starport):
                if self.can_afford(RAVEN) and self.can_feed(RAVEN):
                    self.do(starport.train(RAVEN))
                    print("Training raven")
                    break
            elif self.faster_tanks and self.factories.idle and siegeTankTotal < 2:
                break
            elif (vikingTotal < self.max_viking
                  and self.supply_used < 190
                  and not (self.delay_vikings and self.banshee_left)):
                if (self.can_afford(VIKINGFIGHTER) and self.can_feed(VIKINGFIGHTER)):
                    self.do(starport.train(VIKINGFIGHTER))
                    print("Training viking")
                    break
            elif (self.banshee_left - banshees_in_production) > 0:
                if (not self.enemy_has_air2air_units
                        and self.allEnemyUnits.filter(lambda x: x.is_flying and x.can_attack_air)):
                    self.enemy_has_air2air_units = True
                if (vikingTotal < 20 and self.enemy_has_air2air_units
                        and (vikingTotal < ((self.banshees.amount + banshees_in_production) * 2)
                        or self.allEnemyUnits.filter(lambda x: x.is_flying and x.can_attack_air))):
                    if self.can_afford(BANSHEE) and self.can_feed(VIKINGFIGHTER):
                        self.do(starport.train(VIKINGFIGHTER))
                        print("Training viking")
                        break
                elif self.can_afford(BANSHEE) and self.can_feed(BANSHEE) and await self.has_ability(
                        STARPORTTRAIN_BANSHEE, starport) and len(starport.orders) == 0:
                    print("Training banshee")
                    self.do(starport.train(BANSHEE))
                    break
            elif (self.liberator_left - self.already_pending(UnitTypeId.LIBERATOR) > 0
                  and self.can_afford(LIBERATOR) and self.can_feed(LIBERATOR)):
                self.do(starport.train(LIBERATOR))
                print("Training liberator")
                continue
            if (thorTotal >= 1 or self.max_thor == 0) and self.max_BC > 0:
                if self.can_afford(BATTLECRUISER) and self.can_feed(BATTLECRUISER) and await self.has_ability(
                        STARPORTTRAIN_BATTLECRUISER, starport):
                    self.do(starport.train(BATTLECRUISER))
                    self.marines_last_resort = True
                    print("Training battlecruiser")
                    break

    async def train_liberator(self):
        if self.marine_drop:
            return True
        if not self.build_one_liberator:
            return True
        if self.already_pending(LIBERATOR):
            return True
        if not self.all_liberators:
            for starport in self.starports.ready:
                if self.can_afford(LIBERATOR) and self.can_feed(LIBERATOR):
                    print("Training liberator")
                    self.do(starport.train(LIBERATOR))
                    return False
                else:
                    return False
        return True

    async def on_unit_created(self, unit: Unit):
        if unit.type_id in [BANSHEE]:
            self.banshee_left = self.banshee_left - 1
        if unit.type_id in [HELLION]:
            self.hellion_left = self.hellion_left - 1
        if unit.type_id in [WIDOWMINE]:
            self.mines_left = self.mines_left - 1
        if unit.type_id in [CYCLONE]:
            self.cyclone_left = self.cyclone_left - 1
        if unit.type_id in [RAVEN]:
            self.raven_left = self.raven_left - 1
        if unit.type_id in [LIBERATOR]:
            self.liberator_left -= 1

    async def do_research(self):
        if self.wall_in:
            return True
        if self.upgrade_mech:
            for facility in self.armories.ready:
                if len(facility.orders) > 0:
                    continue
                abilities = await self.get_available_abilities(facility)
                for upgrade_level in range(1, 4):
                    upgrade_armor_id = getattr(sc2.constants,
                                               "ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL" + str(upgrade_level))
                    upgrade_vehicleweapon_id = getattr(sc2.constants,
                                                       "ARMORYRESEARCH_TERRANVEHICLEWEAPONSLEVEL" + str(upgrade_level))
                    upgrade_shipweapon_id = getattr(sc2.constants,
                                                    "ARMORYRESEARCH_TERRANSHIPWEAPONSLEVEL" + str(upgrade_level))
                    if upgrade_armor_id in abilities and self.can_afford(upgrade_armor_id):
                        self.do(facility(upgrade_armor_id))
                        return False
                    if upgrade_vehicleweapon_id in abilities and self.can_afford(
                            upgrade_vehicleweapon_id) and self.upgrade_vehicle_weapons:
                        self.do(facility(upgrade_vehicleweapon_id))
                        return False
                    if upgrade_shipweapon_id in abilities and self.can_afford(
                            upgrade_shipweapon_id) and self.max_starports > 0:
                        self.do(facility(upgrade_shipweapon_id))
                        return False

        for facility in self.structures(FACTORYTECHLAB).ready.idle:
            if self.wall_in:
                break
            abilities = await self.get_available_abilities(facility)
            if RESEARCH_INFERNALPREIGNITER in abilities and self.can_afford(
                    RESEARCH_INFERNALPREIGNITER) and self.researsh_blueflame:
                self.do(facility(AbilityId.RESEARCH_INFERNALPREIGNITER))
                print("upgrade INFERNALPREIGNITERS")
                continue
            if (RESEARCH_DRILLINGCLAWS in abilities
                    and self.can_afford(RESEARCH_DRILLINGCLAWS)
                    and (self.mines_left > 0 or self.mines.amount > 4)):
                self.do(facility(AbilityId.RESEARCH_DRILLINGCLAWS))
                continue
            if RESEARCH_CYCLONELOCKONDAMAGE in abilities and self.can_afford(
                    RESEARCH_CYCLONELOCKONDAMAGE) and self.cyclones.amount >= 2:
                self.do(facility(AbilityId.RESEARCH_CYCLONELOCKONDAMAGE))
                continue
        if self.max_BC > 0:
            for facility in self.fusioncores.ready.idle:
                abilities = await self.get_available_abilities(facility)
                if (RESEARCH_BATTLECRUISERWEAPONREFIT in abilities
                        and self.can_afford(RESEARCH_BATTLECRUISERWEAPONREFIT)
                        and self.liberator_left <= 0):
                    self.do(facility(AbilityId.RESEARCH_BATTLECRUISERWEAPONREFIT))
                    continue
        if self.upgrade_marine:
            for facility in self.structures(BARRACKSTECHLAB).ready.idle:
                abilities = await self.get_available_abilities(facility)
                if not self.already_pending(STIMPACK) and self.research_stimpack:
                    if self.can_afford(BARRACKSTECHLABRESEARCH_STIMPACK):
                        print("upgrade STIMPACK")
                        self.do(facility(AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK))
                    if self.expand_for_vespene:
                        return False
                    else:
                        return True
                elif self.already_pending(STIMPACK) < 1 and self.research_stimpack:
                    continue
                elif not self.already_pending(SHIELDWALL):
                    if self.can_afford(RESEARCH_COMBATSHIELD):
                        print("upgrade COMBATSHIELD")
                        self.do(facility(AbilityId.RESEARCH_COMBATSHIELD))
                    return False
                elif not self.already_pending(PUNISHERGRENADES):
                    if self.can_afford(RESEARCH_CONCUSSIVESHELLS):
                        print("upgrade CONCUSSIVESHELLS")
                        self.do(facility(AbilityId.RESEARCH_CONCUSSIVESHELLS))
                    return False

        for facility in self.engineeringbays.ready.idle:
            if not self.upgrade_marine:
                continue
            if self.wall_in:
                continue
            abilities = await self.get_available_abilities(facility)
            if self.build_planetaries:
                if not self.structures(UnitTypeId.PLANETARYFORTRESS):
                    return True
                if RESEARCH_HISECAUTOTRACKING in abilities and self.can_afford(RESEARCH_HISECAUTOTRACKING):
                    self.do(facility(AbilityId.RESEARCH_HISECAUTOTRACKING))
                    return False
                if RESEARCH_TERRANSTRUCTUREARMORUPGRADE in abilities and self.can_afford(
                        RESEARCH_TERRANSTRUCTUREARMORUPGRADE):
                    self.do(facility(AbilityId.RESEARCH_TERRANSTRUCTUREARMORUPGRADE))
                    return False
                if self.minerals < 150:
                    return False
            for upgrade_level in range(1, 4):
                if upgrade_level == 2 and not self.armories.ready:
                    self.build_armory = True
                    break
                upgrade_weapon_id = getattr(sc2.constants,
                                            "ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL" + str(upgrade_level))
                upgrade_weapon_research_id = getattr(sc2.constants, "TERRANINFANTRYWEAPONSLEVEL" + str(upgrade_level))
                upgrade_armor_id = getattr(sc2.constants,
                                           "ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL" + str(upgrade_level))
                upgrade_armor_research_id = getattr(sc2.constants, "TERRANINFANTRYARMORSLEVEL" + str(upgrade_level))
                if not self.already_pending(upgrade_weapon_research_id) and not (
                        upgrade_weapon_research_id in self.state.upgrades):
                    if self.can_afford(upgrade_weapon_id):
                        print("upgrade", upgrade_weapon_research_id)
                        self.do(facility(upgrade_weapon_id))
                    return False
                if not self.already_pending(upgrade_armor_research_id) and not (
                        upgrade_armor_research_id in self.state.upgrades):
                    if self.can_afford(upgrade_armor_id):
                        print("upgrade", upgrade_armor_research_id)
                        self.do(facility(upgrade_armor_id))
                    return False
            if (RESEARCH_TERRANSTRUCTUREARMORUPGRADE in abilities
                    and self.can_afford(RESEARCH_TERRANSTRUCTUREARMORUPGRADE)
                    and self.minerals > 250
                    and self.vespene > 250):
                self.do(facility(AbilityId.RESEARCH_TERRANSTRUCTUREARMORUPGRADE))
                self.upgrade_mech = True
                return False

        for facility in self.ghost_academies.ready:
            if len(facility.orders) >= 1:
                continue
            if self.NukesLeft <= 0:
                continue
            if not self.ghosts and not self.already_pending(UnitTypeId.GHOST):
                continue
            abilities = await self.get_available_abilities(facility)
            if not self.already_pending(PERSONALCLOAKING):
                if RESEARCH_PERSONALCLOAKING in abilities:
                    if self.can_afford(RESEARCH_PERSONALCLOAKING):
                        self.do(facility(AbilityId.RESEARCH_PERSONALCLOAKING))
                return False
            elif BUILD_NUKE in abilities:
                if self.can_afford(BUILD_NUKE):
                    self.do(facility(AbilityId.BUILD_NUKE))
                    self.NukesLeft = self.NukesLeft - 1
                return False

        for facility in self.structures(STARPORTTECHLAB).ready.idle:
            abilities = await self.get_available_abilities(facility)
            #print(abilities)
            if self.upgrade_banshee and RESEARCH_BANSHEECLOAKINGFIELD in abilities:
                if self.can_afford(RESEARCH_BANSHEECLOAKINGFIELD):
                    self.do(facility(AbilityId.RESEARCH_BANSHEECLOAKINGFIELD))
                return False
            if self.upgrade_banshee and RESEARCH_BANSHEEHYPERFLIGHTROTORS in abilities:
                if self.can_afford(RESEARCH_BANSHEEHYPERFLIGHTROTORS):
                    self.do(facility(AbilityId.RESEARCH_BANSHEEHYPERFLIGHTROTORS))
                return False
            if self.upgrade_liberator and RESEARCH_ADVANCEDBALLISTICS in abilities:
                if self.can_afford(RESEARCH_ADVANCEDBALLISTICS):
                    self.do(facility(AbilityId.RESEARCH_ADVANCEDBALLISTICS))
                return False
        return True

    def findOppId(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--OpponentId', type=str, nargs="?", help='Opponent Id')
        args, unknown = parser.parse_known_args()
        if args.OpponentId:
            return args.OpponentId
        return None

    def on_end(self, result):
        print(str(result))


##        if 'Victory' in str(result):
##            self._training_data.saveVictory(self.opp_id, self.strategy)


def main():
    maps = [
        "AcropolisLE",
        # "Bandwidth" ,
        # "CrystalCavern" ,
        # "DigitalFrontier" ,
        "DiscoBloodbathLE" ,
        # "Ephemeron" ,
        "EphemeronLE" ,
        # "OldSunshine" ,
        # "Opponent Stats" ,
        # "PrimusQ9",
        # "Reminiscence" ,
        # "Sanglune" ,
        # "TheTimelessVoid" ,
        "ThunderbirdLE" ,
        # "Treachery" ,
        "TritonLE" ,
        "WintersGateLE" ,
        "WorldofSleepersLE" ,
        # "Urzagol" ,
    ]
    mapname = random.choice(maps)
    opponents = [Race.Protoss, Race.Zerg, Race.Terran]
    #opponents = [Race.Protoss]
    opponent = random.choice(opponents)
    #    mapname = ("DarknessSanctuaryLE")

    ##    sc2.run_game(sc2.maps.get(mapname), [
    ##        Human(Race.Terran),
    ##        Bot(Race.Terran, ANIbot())
    ##        ], realtime=True, save_replay_as="ANIvsHUMAN.SC2Replay")

    sc2.run_game(sc2.maps.get(mapname), [
        Bot(Race.Terran, ANIbot()),
        Computer(random.choice(opponents), Difficulty.VeryHard)
        #        Computer(random.choice(opponents), Difficulty.CheatInsane)
    ], realtime=False, save_replay_as="ANI.SC2Replay")


if __name__ == '__main__':
    main()
