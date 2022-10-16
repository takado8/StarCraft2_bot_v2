#- VER 1_33
#--------------------------------changes----------------------------------------

#-----------------------TO DO -----------------------------------------#

import sc2
from sc2.bot_ai import BotAI
from sc2.units import Units
from sc2.unit import Unit
from sc2.constants import UnitTypeId, UpgradeId

class build:
    def __init__(self):
        self.expo_drone = None
        self.build_step = 0
        self.paused = False
        self.build_order = [ 
            'drone',
            'extractor',
            'pool',
            'drone',
            'drone',
            'drone',
            'ovie',
            'queen',
            'speed',
            'ling',
            'ling',
            'ling',
            'ling',
            'ling',
            'ovie',
            'ling',
            'ling',
            'hatch',
            "END",
        ]     

    async def run(self, bot):
        if not self.paused:
            if self.build_order[self.build_step] != 'END':
                await self.do_build(bot)


    async def do_build(self, bot_ai):
        if self.build_order[self.build_step]=='drone':
            if bot_ai.can_afford(UnitTypeId.DRONE):
                bot_ai.train(UnitTypeId.DRONE)
                self.build_step+=1
                print("built drone. next step: ", self.build_order[self.build_step])

        elif self.build_order[self.build_step]=='extractor':
            if bot_ai.already_pending(UnitTypeId.EXTRACTOR)==0:
                if bot_ai.minerals > 60 :  
                    drone = bot_ai.workers.random
                    target = bot_ai.vespene_geyser.closest_to(drone)
                    if await bot_ai.can_place(UnitTypeId.EXTRACTOR, target.position):

                        self.gas1_coords = target.position
                        free_workers = bot_ai.workers.filter(lambda w: w.is_carrying_resource == False  and len(w.orders) < 2)
                        drone = free_workers.closest_to(target.position)
                        bot_ai.do(drone.build(UnitTypeId.EXTRACTOR, target), subtract_cost= True)
                        self.build_step+=1
                        print("built extractor. next step: ", self.build_order[self.build_step])
            #else : 
                #self.build_step+=1
                #print("built extractor. next step: ", self.build_order[self.build_step])

        elif self.build_order[self.build_step]=='pool':
            if bot_ai.already_pending(UnitTypeId.SPAWNINGPOOL) == 0:
                if bot_ai.can_afford(UnitTypeId.SPAWNINGPOOL):
                    for d in range(4, 15):
                        pos = bot_ai.base_coords.towards(bot_ai.game_info.map_center+[0,-70], d)
                        if await bot_ai.can_place(UnitTypeId.SPAWNINGPOOL, pos):
                            free_workers=bot_ai.workers.filter(lambda w: w.is_carrying_resource == False  and len(w.orders) < 2)
                            drone = free_workers.closest_to(pos)
                            bot_ai.do(drone.build(UnitTypeId.SPAWNINGPOOL, pos), subtract_cost=True)
            else: 
                self.build_step+=1
                print("built pool. next step: ", self.build_order[self.build_step])

        elif self.build_order[self.build_step]=='ovie':
            if bot_ai.already_pending(UnitTypeId.OVERLORD) < 1: 
                if bot_ai.can_afford(UnitTypeId.OVERLORD):
                    bot_ai.train(UnitTypeId.OVERLORD)
            else:
                self.build_step+=1
                print("built ovie. next step: ", self.build_order[self.build_step])

        elif self.build_order[self.build_step]=='queen':
            if (
                bot_ai.units(UnitTypeId.QUEEN).amount + bot_ai.already_pending(UnitTypeId.QUEEN) == 0
                and bot_ai.structures(UnitTypeId.SPAWNINGPOOL).ready
            ):
                if bot_ai.can_afford(UnitTypeId.QUEEN):
                    bot_ai.train(UnitTypeId.QUEEN)
                    self.build_step+=1
                    print("built queen. next step: ", self.build_order[self.build_step])
        
        elif self.build_order[self.build_step]=='ling':
            if bot_ai.can_afford(UnitTypeId.ZERGLING) and bot_ai.structures(UnitTypeId.SPAWNINGPOOL).ready :
                bot_ai.train(UnitTypeId.ZERGLING)
                self.build_step+=1
                print("built ling. next step: ", self.build_order[self.build_step])
        
        elif self.build_order[self.build_step]=='speed':
            if bot_ai.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0 and bot_ai.can_afford(
                UpgradeId.ZERGLINGMOVEMENTSPEED
            ):
                spawning_pools_ready = bot_ai.structures(UnitTypeId.SPAWNINGPOOL).ready
                if spawning_pools_ready:
                    bot_ai.research(UpgradeId.ZERGLINGMOVEMENTSPEED)
                    self.build_step+=1
                    print("started speed. next step: ", self.build_order[self.build_step])

        elif self.build_order[self.build_step]=='hatch': 
            if bot_ai.already_pending(UnitTypeId.HATCHERY) < 1: 
                if bot_ai.minerals >= 200 :
                    expo_coords = await bot_ai.get_next_expansion()
                    free_workers=bot_ai.workers.filter(lambda w: w.is_carrying_resource == False  and len(w.orders) < 2)
                    if not self.expo_drone:
                        self.expo_drone=free_workers.closest_to(expo_coords) 
                        bot_ai.do(self.expo_drone.move(expo_coords))

                    if bot_ai.can_afford(UnitTypeId.HATCHERY) :
                        build_coords = await bot_ai.find_placement(UnitTypeId.HATCHERY,expo_coords,placement_step = 2)
                        self.nat_coords = build_coords
                        if await bot_ai.can_place(UnitTypeId.HATCHERY, build_coords) :
                            bot_ai.do(self.expo_drone.build(UnitTypeId.HATCHERY, build_coords), subtract_cost= True)

            else :      
                self.build_step += 1
                print("built hatch. next step: ", self.build_order[self.build_step])
                
        elif self.build_order[self.build_step]=='END' :
            print('OOPS')
        return

    def pause(self):
        if not self.paused:
            self.paused = True
            print('build paused')

    def unpause(self):
        if self.paused:
            self.paused = False
            print('build unpaused')