import sc2
from sc2.unit import Unit
from sc2.units import Units
from sc2.bot_ai import BotAI
from sc2.constants import UnitTypeId, UpgradeId

class army:

    def __init__(self):
        self.isAttacking = False
        self.isGrouping = False
        self.isRetreating = False
        self.isDefending = True
        self.activeForces = None 
        self.myLings = None
        self.air_target_coords = None
        self.target_coords = None
        

    def updateArmyInfo(self, BotAI):
        self.myLings = BotAI.units(UnitTypeId.ZERGLING)
        self.myCorruptors = BotAI.units(UnitTypeId.CORRUPTOR)
        return

    def attack(self, BotAI):
        if self.lings:
            for zl in self.lings:
                if zl.is_idle:                  
                    if not BotAI.enemy_main_destroyed:
                        BotAI.do(zl.attack(BotAI.enemy_ramp_coords,queue=False))
                    BotAI.do(zl.attack(self.target_coords,queue=True)) # just amove
                elif BotAI.attack_flag:
                    BotAI.do(zl.attack(self.target_coords,queue=False)) # just amove

        if self.corruptors:
            for cr in self.corruptors:
                if cr.is_idle:
                    BotAI.do(cr.attack(self.air_target_coords,queue=False)) # just amove
                   
                #put this on flag
                if BotAI.enemy_structures.flying : 
                    self.air_target_coords = BotAI.enemy_structures.flying.closest_to(self.air_target_coords).position
                    BotAI.do(cr.attack(BotAI.enemy_structures.flying.closest_to(self.air_target_coords).position))



    #@property 
    #def activeForces(self) -> Units:
    #    return None #slambda filter for all army units 

    @property
    def lings(self) -> Units:
        return self.myLings

    @property
    def corruptors(self) -> Units:
        return self.myCorruptors