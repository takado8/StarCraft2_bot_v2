#TO DO
#MAKE drones return after defending

import sc2
from sc2.constants import UnitTypeId, AbilityId
from sc2.bot_ai import BotAI
from sc2.unit import Unit
from sc2.units import Units

class workerRushDefense:
    def __init__(self):
        self.isActive = False
        self.defending = False
        self.workerTarget = None

    def run(self, bot): #call this in botai code
        if not self.defending:
            self.checkForWorkerRush(bot)
        else: 
            self.defendWorkerRush(bot)

    def checkForWorkerRush(self,bot):
        if bot.enemy_units:
            enemyWorkers = bot.getEnemyWorkers() #make this only rely on sc2 lib
            if enemyWorkers:
                if not self.isActive:
                    if len(enemyWorkers.closer_than(32,bot.base_coords))>3:
                        self.isActive = True
                        print("Worker Rush Detected")
                else:
                    if len(enemyWorkers.closer_than(7,bot.base_coords))>2:
                        self.defending = True
                        #if not self.isActive: self.isActive = True
                        print("Defending Worker Rush")


    def defendWorkerRush(self,bot):
        if bot.workers:
            enemyWorkers = bot.getEnemyWorkers()
            if enemyWorkers:
                self.workerTarget = enemyWorkers.center
                if len(enemyWorkers.closer_than(160,bot.base_coords))==0 : 
                    self.stopDefendWorkerRush(bot)
                else: #this is our actual defense. executes when ever enemy worers are not out of range
                    self.controlDrones(bot)
                    self.controlLings(bot)

            else: 
                self.stopDefendWorkerRush(bot)
    
    def controlDrones(self, bot):
        for dr in bot.workers:
            if dr.health_percentage >= 0: #we have enough health to be aggressive
                if dr.weapon_cooldown == 0: #our attack is off cooldown
                    bot.do(dr.attack(self.workerTarget))
                else:
                    if dr.health_percentage <=0.5: #rig
                        closest_mineral_patch = bot.mineral_field.closest_to(dr)
                        bot.do(dr.gather(closest_mineral_patch))
            else:
                #print(dr.orders[0].ability.id)
                #there is no default action here. it goes straight to  checking for harvest tag
                if not (dr.orders[0].ability.id==AbilityId.HARVEST_GATHER or dr.orders[0].ability.id==AbilityId.HARVEST_RETURN ):
                    closest_mineral_patch = bot.mineral_field.closest_to(dr)
                    bot.do(dr.gather(closest_mineral_patch))

    
    def controlLings(self,bot):
        for zl in bot.army.lings:
            if zl.weapon_cooldown == 0:
                bot.do(zl.attack(self.workerTarget))
            else :
                if zl.health_percentage <= 0.5:
                    bot.do(zl.move(bot.base_coords))

    def stopDefendWorkerRush(self, bot):
        print("Not Currently Defending")
        self.defending = False
        for dr in bot.workers:
            #if dr.is_carrying_resource:
            closest_mineral_patch = bot.mineral_field.closest_to(dr)
            if dr.is_carrying_resource:
                bot.do(dr.return_resource(queue = False))
                bot.do(dr.gather(bot.mineral_field.closest_to(bot.base_coords),queue = True))

            else:
                bot.do(dr.gather(bot.mineral_field.closest_to(bot.base_coords),queue = False))

    def doWRDMacro(self, bot):
        # if no supply build overlords
        if bot.supply_left < 1 and bot.already_pending(UnitTypeId.OVERLORD) < 1 and bot.supply_cap < 200:
            if bot.can_afford(UnitTypeId.OVERLORD) and bot.larva:
                bot.train(UnitTypeId.OVERLORD, 1)
        # if spawning pool is ready build lings
        elif bot.supply_workers >= 16 :
            if bot.structures(UnitTypeId.SPAWNINGPOOL) : #if any pools exist
                if bot.structures(UnitTypeId.SPAWNINGPOOL).ready:
                    if bot.can_afford(UnitTypeId.ZERGLING) and bot.larva.amount > 0:
                        print("DEFENSIVE LINGS")
                        bot.train(UnitTypeId.ZERGLING)
        #else build drones 
        else :
            if bot.can_afford(UnitTypeId.DRONE) and bot.larva.amount > 0:
                print("DRONIN TIME")
                bot.train(UnitTypeId.DRONE)
