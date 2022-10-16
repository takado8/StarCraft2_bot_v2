import sc2, sys
from __init__ import run_ladder_game
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
import random
from LiftBot import LiftBot
from WorkerRush import WorkerRush


# Load bot
from WorthlessBot import WorthlessBot

bot = Bot(Race.Zerg, WorthlessBot())
#enemybot = Bot(Race.Terran, LiftBot())
enemybot = Bot(Race.Terran, WorkerRush())

allmaps = [
    'AcropolisLE',
    'DiscoBloodbathLE',
    'EphemeronLE',
    'ThunderbirdLE',
    'WintersGateLE',
    'WorldofSleepersLE',
]


_realtime = False
_difficulty = Difficulty.CheatInsane
_opponent = random.choice([Race.Zerg, Race.Terran, Race.Protoss, Race.Random])
#_opponent = Race.Protoss

# Start game
if __name__ == '__main__':
    if "--LadderServer" in sys.argv:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        run_ladder_game(bot)
    else:
        # Local game
        print("Starting local game...")      
        
        sc2.run_game(sc2.maps.get('DiscoBloodbathLE'), [
        #sc2.run_game(sc2.maps.get(random.choice(allmaps)), [
            bot,
            enemybot
            #Computer(_opponent, _difficulty)
        ], realtime=_realtime)
