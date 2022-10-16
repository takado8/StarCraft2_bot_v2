#- VER 1_33
#--------------------------------changes----------------------------------------
#- reinstall enemy_main_destroyed to resolve dependancy issue
#- improve worker rush response
#- transfer all worker rush defense functions to separate module
#- move fillextractor to macro module

#---------------------------- TO DO ---------------------------------------------#
#- move target coords to army
#- basic running when outnumbered
#- still crashing on death
#- fix getting stuck at 96 gas sometimes vs dronerush

import sc2
from sc2.bot_ai import BotAI
from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from sc2.score import ScoreDetails as score
from sc2.position import Point2
from math import sqrt
from build import build 
from macro import macro
from army import army
from worker_rush_defense import workerRushDefense 

class WorthlessBot(BotAI):
    def __init__(self):
        self._build = build()
        self._macro = macro()
        self.workerRushDefense = workerRushDefense()
        self.army = army()
        self.enemy_main_destroyed = False
        self.first_wave = True
        self.wave_size = 6
        self.enemy_ramp_coords = (0,0)
        self.attack_flag = False
        self.expo_number = 0
        self.building_air = False
        self.lategame = False
        self.push_started = False
 

    async def on_start(self):
        self._client.game_step = 2

    async def start_step(self):

        await self.chat_send("greetings, stranger...")

        hatch: Unit = self.townhalls[0] 
        self.base_coords = hatch.position 
        self.enemy_base_coords = self.enemy_start_locations[0]
        self.army.target_coords = self.enemy_base_coords 
        self.army.air_target_coords = self.enemy_base_coords
        
        if self.base_coords[0] < self.game_info.map_center[0]: self.upper_left = True
        else: self.upper_left = False

        self.ordered_expansions = self.get_expo_list()
        self._macro.do_worker_split(self)
        expo_coords = await self.get_next_expansion()


        first_ovie = self.units(UnitTypeId.OVERLORD).random
        self.do(first_ovie.move(expo_coords))

        for ramp in self.game_info.map_ramps:
            if self.enemy_ramp_coords==(0,0): self.enemy_ramp_coords=ramp.top_center
            current_dist=self.distance(self.army.target_coords, self.enemy_ramp_coords)
            distance_to_enemy = self.distance(ramp.top_center,self.enemy_base_coords)
            if distance_to_enemy < current_dist:
                self.enemy_ramp_coords = ramp.top_center                           

    async def on_step(self, iteration): 
        #-------------------------FIRST STEP INITIALIZATION---------------------#
        if iteration == 0:
            await self.start_step()

        #---------------------GATHER THIS FRAMES UNIT INFO-----------------------#
        self.army.updateArmyInfo(self)

        #-------------------Do Worker Related Management------------------------------#
        await self.distribute_workers()
        self.extractor_magic()
        self.workerRushDefense.run(self)
        if self.workerRushDefense.isActive : 
            self._build.pause()
            self.workerRushDefense.doWRDMacro(self)

        #-------------RUN OPENER ------------------#
        await self._build.run(self)

        #------------------IF BUILD IS OVER FOLLOW GENERAL MACRO CYCLE------------#
        #else: 
        if self._build.build_order[self._build.build_step] == 'END': 
            await self.do_macro_cycle()
            self.build_army()

        #----------either way, perform basic upkeep and unit control--------------#

        await self.inject()
        self.cancel_logic()

        self.set_army_target() 
        self.control_army() 


        if self.time>300 and not self.lategame: 
            self.lategame = True
            print("Entering Lategame")

        # ---------------------DEATH THROES-----------------------------------#
        if not self.townhalls:
            for unit in self.units.exclude_type({UnitTypeId.EGG, UnitTypeId.LARVA}):
                self.do(unit.attack(self.enemy_start_locations[0]))
            return


    async def do_macro_cycle(self):
        # add core buidling rebuilding functions here, incase early buildings are sniped
        # If we have no extractor (and we still plan on using gas), build extractor
        # If we have no spawning pool, try to build spawning pool

        #build a queen for eatch hatcher
        if self.already_pending(UnitTypeId.QUEEN)==0 and self.structures(UnitTypeId.SPAWNINGPOOL).ready :
            if self.can_afford(UnitTypeId.QUEEN):
                for t in self.townhalls :
                    if not self.units(UnitTypeId.QUEEN).closer_than(6,t):
                        self.do(t.train(UnitTypeId.QUEEN),subtract_cost=True)
                 
        # build ovies
        if self.supply_left < 2 and self.already_pending(UnitTypeId.OVERLORD) < 1 and self.supply_cap < 200:
            self.train(UnitTypeId.OVERLORD, 1)

        #macro hatch
        if self.minerals >= 420:
            for d in range(4, 15):
                pos = self.base_coords.towards(self.game_info.map_center, d)
                if await self.can_place(UnitTypeId.HATCHERY, pos):
                    self.do(self.workers.random.build(UnitTypeId.HATCHERY, pos), subtract_cost=True)
                    break
        
        #air transition
        if self.building_air : 
            if self.townhalls:
                if not self.already_pending(UnitTypeId.LAIR) and self.can_afford(UnitTypeId.LAIR) and not self.structures(UnitTypeId.LAIR):
                    hatch: Unit = self.townhalls[0] 
                    self.do(hatch(AbilityId.UPGRADETOLAIR_LAIR), subtract_cost=True) 

            if not self.already_pending(UnitTypeId.SPIRE) and self.can_afford(UnitTypeId.SPIRE) and not self.structures(UnitTypeId.SPIRE):
                print ('building spire')
                for d in range(4, 15):  
                    pos = self.base_coords.towards(self.game_info.map_center + (0,70), d)
                    if await self.can_place(UnitTypeId.SPIRE, pos):
                        self.do(self.workers.random.build(UnitTypeId.SPIRE, pos), subtract_cost=True)

        #enable the second stage of our build
        if self.lategame : 
            pending_drones = self.already_pending(UnitTypeId.DRONE)
            if self.can_afford(UnitTypeId.DRONE) and (self.supply_workers + pending_drones) < 14: 
                print("DRONIN TIME")
                self.train(UnitTypeId.DRONE)
            #banelings
    
    def control_army(self):

        #initial startup
        if not self.push_started:
            if self.army.lings:
                if len(self.army.lings) >= self.wave_size:
                    self.army.isAttacking = True 
                    self.push_started = True 

        #attack if attacking
        if self.army.isAttacking:
            self.army.attack(self)

    def getEnemyWorkers(self):
        return self.enemy_units.filter(lambda u: u.type_id == UnitTypeId.DRONE
                                                            or u.type_id == UnitTypeId.SCV
                                                            or u.type_id == UnitTypeId.PROBE)

    def set_army_target(self):

        if self.army.lings:
            if self.army.lings.closer_than(3, self.army.target_coords):  
                forward_lings = self.army.lings.closer_than( 3, self.army.target_coords ) #3 allows for lings outside of townhall

                if self.enemy_structures: # if there are currently visible enemy structures
                    nearby_structures = self.enemy_structures.closer_than(3 , forward_lings.random).not_flying 
                
                    # if target building no longer exists on ground
                    if not nearby_structures :      
                        self.attack_flag = True
                        if not self.enemy_main_destroyed: self.enemy_main_destroyed = True

                        # if there are still notflying structures visible on the map select closest one and attack
                        if self.enemy_structures.not_flying:  
                            self.army.target_coords = self.enemy_structures.closest_to(self.army.target_coords).position
                            print('switching target to random building')
                        elif self.enemy_structures.flying and not self.building_air: 
                            print('initiating air switch') 
                            self.army.air_target_coords = self.enemy_structures.flying.closest_to(self.army.air_target_coords).position
                            self.building_air = True

                # search procedure when no enemy structures are visible
                else : 
                    self.expo_number = (self.expo_number + 1) % len(self.ordered_expansions) 
                    next_expo = self.ordered_expansions[self.expo_number]
                    self.army.target_coords = next_expo
                    self.attack_flag = True
                    print('going to next expo at: ', self.army.target_coords)


    def get_expo_list(self): 
        ordered_expos = sorted(
            self.expansion_locations, key=lambda expansion: expansion.distance_to(self.enemy_base_coords)
        )
        return ordered_expos

    def cancel_logic(self):
        if len(self.structures.not_ready)>0:
            still_building = self.structures.not_ready
            for s in still_building:
                if s.health_percentage < 0.05 :
                    self.do(s(AbilityId.CANCEL))

    def extractor_magic(self):
        if not self.workers: return
        if not self.townhalls: return
        hatch: Unit = self.townhalls[0]

        # empty extractors
        if not self.lategame: #dont empty extractors lategame
            if self.vespene >= 88 or self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) > 0 or self.workerRushDefense.isActive: #amess
                gas_drones = self.workers.filter(lambda w: w.is_carrying_vespene and len(w.orders) < 2)
                for drone in gas_drones:
                    minerals: Units = self.mineral_field.closer_than(10, hatch)
                    if minerals:
                        mineral = minerals.closest_to(drone)
                        self.do(drone.gather(mineral, queue=True))

        # fill extractors
        if self.gas_buildings.ready and not self.workerRushDefense.isActive: 
            extractor: Unit = self.gas_buildings.first 

            #ling speed
            if self.vespene < 88 and self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0 :
                self._macro.fill_extractor(extractor, self)

            #air transition 
            if self.building_air : 
                self._macro.fill_extractor(extractor, self)

            #switch gas on when our lategame trigger happens
            if self.lategame : 
                self._macro.fill_extractor(extractor, self)


    def build_army(self):
        if not self.building_air :
            if self.structures(UnitTypeId.SPAWNINGPOOL).ready and self.larva and self.can_afford(UnitTypeId.ZERGLING):
                self.train(UnitTypeId.ZERGLING, self.larva.amount)
        else :
            if self.structures(UnitTypeId.SPIRE).ready and self.larva and self.can_afford(UnitTypeId.CORRUPTOR) :
                self.train(UnitTypeId.CORRUPTOR, self.larva.amount)


    async def inject(self):
        if self.units(UnitTypeId.QUEEN):
            for queen in self.units(UnitTypeId.QUEEN):
                hatch: Unit = self.townhalls.closest_to(queen.position)
                if hatch: 
                    if queen.energy >= 25 and not hatch.has_buff(BuffId.QUEENSPAWNLARVATIMER):
                        self.do(queen(AbilityId.EFFECT_INJECTLARVA, hatch))

    def distance(self, a, b):
        xdist = a[0] - b[0]
        ydist = a[1] - b[1]
        return sqrt( xdist**2 + ydist**2 )