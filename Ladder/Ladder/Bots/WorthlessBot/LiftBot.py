import sc2
from sc2.bot_ai import BotAI
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2

class LiftBot(BotAI):
    def __init__(self):
        self._float_pos = Point2([1,1])

    async def on_start(self):
        self._client.game_step = 8

    async def start_step(self):

        await self.chat_send("SPOT ME BRO")                     

    async def on_step(self, iteration): 
    
        if iteration == 0:
            await self.start_step()

        if not self.structures.flying :
            cc = self.structures(UnitTypeId.COMMANDCENTER).random
            print('lift')
            self.do(cc(AbilityId.LOADALL_COMMANDCENTER))
            self.do(cc(AbilityId.LIFT_COMMANDCENTER))
        #else: 
        #    cc = self.structures(UnitTypeId.COMMANDCENTERFLYING).random
        #    self.do(cc.move(self._float_pos))
        #await self.distribute_workers()

