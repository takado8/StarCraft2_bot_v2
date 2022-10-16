import sc2, sys
from __init__ import run_ladder_game
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer

# Load bot
from ANI import ANIbot
bot = Bot(Race.Terran, ANIbot())

# Start game
if __name__ == '__main__':
    if "--LadderServer" in sys.argv:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        run_ladder_game(bot)
    else:
        # Local game
        print("Starting local game...")
        sc2.run_game(sc2.maps.get("AutomatonLE"), [
            bot,
            Computer(Race.Terran, Difficulty.Harder)
        ], realtime=False)
