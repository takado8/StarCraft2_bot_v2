#---------------------------- TO DO ---------------------------------------------#
#- macro tricks. mineral boosting, 


import sc2
from sc2.bot_ai import BotAI
from sc2.units import Units
from sc2.unit import Unit

class macro:
    def __init__(self):
        self.wtf = None

    def do_worker_split(self, bot_ai):
        for drone in bot_ai.workers:
           closest_mineral_patch = bot_ai.mineral_field.closest_to(drone)
           bot_ai.do(drone.gather(closest_mineral_patch))

    def fill_extractor(self, extractor, BotAI):
        if extractor.surplus_harvesters < 0: 
            the_chosen_ones = BotAI.workers.closer_than(8, extractor).gathering
            if the_chosen_ones: 
                the_chosen_one = the_chosen_ones.random
                if not the_chosen_one.is_carrying_resource :
                    BotAI.do(the_chosen_one.gather(extractor))

    # async def inject(self, bot):
    #     if not bot.townhalls: return
    #     if not bot.units(UnitTypeID.QUEEN): return

    #     for queen in bot.units(UnitTypeId.QUEEN):
    #         hatch: Unit = bot.townhalls.closest_to(queen.position)
    #         #shoul also check if another queen is queed to inject it
    #         if queen.energy >= 25 and not hatch.has_buff(BuffId.QUEENSPAWNLARVATIMER): 
    #             bot.do(queen(AbilityId.EFFECT_INJECTLARVA, hatch))