import random
from sc2 import run_game, maps, Race, Difficulty, Result, AIBuild
import sc2
from sc2.constants import FakeEffectID
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.player import Bot, Computer
from sc2.units import Units
from sc2.ids.buff_id import BuffId as buff
from sc2.ids.upgrade_id import UpgradeId as upgrade
from sc2.ids.effect_id import EffectId as effect
from sc2.position import Point2
from coords import coords as cd
from player_vs import player_vs_computer
from strategy.carrier_madness import CarrierMadness
from strategy.macro import Macro
from strategy.stalker_hunt import StalkerHunt


class Octopus(sc2.BotAI):
    enemy_attack = False
    second_ramp = None
    builds = ['rush', 'macro', 'defend_rush']
    build_type = 'rush'
    enemy_main_base_down = False
    first_attack = False
    attack = False
    after_first_attack = False
    army_ids = [unit.ADEPT, unit.STALKER, unit.ZEALOT, unit.SENTRY, unit.OBSERVER, unit.IMMORTAL, unit.ARCHON,
                unit.HIGHTEMPLAR, unit.DISRUPTOR, unit.WARPPRISM, unit.VOIDRAY, unit.CARRIER]
    units_to_ignore = [unit.LARVA, unit.EGG]
    workers_ids = [unit.SCV, unit.PROBE, unit.DRONE]
    proper_nexus_count = 1
    army = []
    known_enemies = []
    game_map = None
    leader = None
    defend_position = None
    destination = None
    prev_nexus_count = 0
    coords = None

    strategy = None


    async def on_start(self):
        print('start loc: ' + str(self.start_location.position))
        self.coords = cd['map1'][self.start_location.position]
        # self.strategy = CarrierMadness(self)
        # self.strategy = Macro(self)
        self.strategy = StalkerHunt(self)

    async def on_end(self, game_result: Result):
        print('start pos: ' + str(self.start_location.position))
        for gateway in self.structures().exclude_type({unit.NEXUS, unit.ASSIMILATOR}):
            print(str(gateway.type_id)+' coords: ' + str(gateway.position))

    async def on_step(self, iteration):
        self.assign_defend_position()
        self.army = self.units().filter(lambda x: x.type_id in self.army_ids)

        self.train_workers()
        await self.distribute_workers()
        await self.morph_gates()

        await self.pylon_first_build()
        await self.pylon_next_build()
        await self.expand()

        if self.structures(unit.NEXUS).amount >= self.proper_nexus_count or self.already_pending(unit.NEXUS) or self.minerals > 400:
            self.cybernetics_core_upgrades()
            await self.twilight_upgrades()
            self.forge_upgrades()
            await self.twilight_council_build()
            await self.robotics_build()
            await self.stargate_build()
            await self.forge_build()
            await self.cybernetics_core_build()
            await self.gate_build()
            self.build_assimilators()
            self.robotics_train()
            self.strategy.stargate_train()
            self.gate_train()
            await self.strategy.warpgate_train()

        await self.nexus_buff()

        # counter attack
        if self.enemy_units().exists and self.enemy_units().closer_than(40,self.defend_position).amount > 2:
            self.enemy_attack = True
        if self.enemy_attack and self.enemy_units().amount < 5:
            self.enemy_attack = False
            self.after_first_attack = True
            self.attack = True
        # normal attack
        if self.build_type == 'rush' and not self.first_attack and upgrade.WARPGATERESEARCH in self.state.upgrades:
            self.first_attack = True
            self.attack = True
        if self.build_type == 'rush' and self.structures(unit.CYBERNETICSCORE).ready.exists:
            await self.proxy()
        await self.warp_prism()

        # retreat
        if self.attack and self.army.amount < (4 if self.build_type == 'rush' else 18):
            self.attack = False
            if self.build_type == 'rush':
                self.strategy = Macro(self)
                self.build_type = 'macro'
        # attack
        if self.attack:
            await self.attack_formation()
        else:
            await self.defend()
        await self.micro_units()


    # ============================================= Builders
    async def gate_build(self):
        await self.strategy.gate_build()

    async def stargate_build(self):
        await self.strategy.stargate_build()

    async def forge_build(self):
        await self.strategy.forge_build()

    async def robotics_build(self):
        await self.strategy.robotics_build()

    async def twilight_council_build(self):
        await self.strategy.twilight_build()

    async def pylon_first_build(self):
        await self.strategy.pylon_first_build()

    async def pylon_next_build(self):
        await self.strategy.pylon_next_build()

    async def proxy(self):
        await self.strategy.proxy()

    async def cybernetics_core_build(self):
        await self.strategy.cybernetics_build()

    def build_assimilators(self):
        self.strategy.assimilator_build()

    async def expand(self):
        await self.strategy.expand()

    # ============================================= Upgraders
    def cybernetics_core_upgrades(self):
        self.strategy.cybernetics_upgrades()

    def forge_upgrades(self):
        self.strategy.forge_upgrades()

    async def twilight_upgrades(self):
        await self.strategy.twilight_upgrades()

    # ============================================= Trainers
    def train_workers(self):
        self.strategy.nexus_train()

    def gate_train(self):
        self.strategy.gate_train()

    def robotics_train(self):
        self.strategy.robotics_train()

    async def warpgate_train(self):
        await self.strategy.warpgate_train()

    # ============================================= Army

    async def micro_units(self):
        await self.strategy.micro()

    async def attack_formation(self):
        await self.strategy.movements()

    # ============================================= none

    def forge_upg_priority(self):
        if self.structures(unit.TWILIGHTCOUNCIL).ready.exists:
            upgds = [upgrade.PROTOSSGROUNDWEAPONSLEVEL1,upgrade.PROTOSSGROUNDARMORSLEVEL2,upgrade.PROTOSSSHIELDSLEVEL1]
        else:
            upgds = [upgrade.PROTOSSGROUNDWEAPONSLEVEL1,upgrade.PROTOSSGROUNDARMORSLEVEL1,upgrade.PROTOSSSHIELDSLEVEL1]
        done = True
        for u in upgds:
            if u not in self.state.upgrades:
                done = False
                break
        if not done:
            if self.structures(unit.FORGE).ready.idle.exists:
                return True
        return False

    async def warp_prism(self):
        if self.attack:
            dist = self.enemy_start_locations[0].distance_to(self.game_info.map_center) * 0.75
            for warp in self.units(unit.WARPPRISM):
                if warp.distance_to(self.enemy_start_locations[0]) <= dist:
                    abilities = await self.get_available_abilities(warp)
                    if ability.MORPH_WARPPRISMPHASINGMODE in abilities:
                        self.do(warp(ability.MORPH_WARPPRISMPHASINGMODE))
        else:
            for warp in self.units(unit.WARPPRISMPHASING):
                abilities = await self.get_available_abilities(warp)
                if ability.MORPH_WARPPRISMTRANSPORTMODE in abilities:
                    self.do(warp(ability.MORPH_WARPPRISMTRANSPORTMODE))

    async def defend(self):
        enemy = self.enemy_units()
        if enemy.exists:
            dist = 40
        else:
            dist = 6
        for man in self.army:
            if man.distance_to(self.defend_position) > dist:
                self.do(man.move(Point2(self.defend_position).random_on_distance(random.randint(1,3))))

    def assign_defend_position(self):
        nex = self.structures(unit.NEXUS)
        enemy = self.enemy_units()
        # start = self.start_location.position
        # self.defend_position = self.coords['defend_pos']
        self.defend_position = self.main_base_ramp.top_center.towards(self.main_base_ramp.bottom_center,-6)

        if self.prev_nexus_count != nex.amount or enemy.exists:
            if nex.amount < 2:
                self.defend_position = self.main_base_ramp.top_center.towards(self.main_base_ramp.bottom_center, -6)
            elif nex.amount == 2:

                self.defend_position = self.coords['defend_pos']
            else:
                min1 = 999
                ramp = None
                if enemy.exists and enemy.closer_than(50,self.start_location).amount > 0:
                    nex = nex.closest_to(enemy.closest_to(self.enemy_start_locations[0]))
                else:
                    nex = nex.furthest_to(self.start_location)
                p = nex.position.towards(Point2(self.coords['defend_pos']),7)
                for rmp in self.game_info.map_ramps:
                    d = p.distance_to(rmp.top_center)

                    if d < min1:
                        min1 = d
                        ramp = rmp
                if min1 < 15:
                    self.defend_position = ramp.top_center.towards(ramp.bottom_center, -1)
                else:
                    self.defend_position = nex.position.towards(self.game_info.map_center,5)

    def get_proper_pylon(self):
        properPylons = self.structures().filter(lambda unit_: unit_.type_id == unit.PYLON and unit_.is_ready and
            unit_.distance_to(self.start_location.position) < 30 and unit_.distance_to(self.defend_position) > 4)
        if properPylons.exists:
            min_neighbours = 99
            pylon = properPylons.random
            for pyl in properPylons:
                neighbours = self.structures().filter(lambda unit_: unit_.distance_to(pyl) < 6).amount
                if neighbours < min_neighbours:
                    min_neighbours = neighbours
                    pylon = pyl
            return pylon
        else:
            print('cant find proper pylon')
            return None

    async def morph_gates(self):
        for gateway in self.structures(unit.GATEWAY).ready:
            abilities = await self.get_available_abilities(gateway)
            if ability.MORPH_WARPGATE in abilities and self.can_afford(ability.MORPH_WARPGATE):
                self.do(gateway(ability.MORPH_WARPGATE))

    async def nexus_buff(self):
        if not self.structures(unit.NEXUS).exists:
            return
        for nexus in self.structures(unit.NEXUS).ready:
            abilities = await self.get_available_abilities(nexus)
            if ability.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                target = self.structures().filter(lambda x: x.type_id == unit.NEXUS
                               and x.is_ready and not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                if target.exists:
                    target = target.random
                else:
                    target = self.structures().filter(lambda x: x.type_id == unit.CYBERNETICSCORE
                        and x.is_ready and not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                    if target.exists:
                        target = target.random
                    else:
                        target = self.structures().filter(lambda x: x.type_id == unit.FORGE and x.is_ready
                                        and not x.is_idle and not x.has_buff(buff.CHRONOBOOSTENERGYCOST))
                        if target.exists:
                            target = target.random
                        else:
                            target = self.structures().filter(lambda x: (x.type_id == unit.GATEWAY or x.type_id == unit.WARPGATE)
                                                                   and x.is_ready and not x.is_idle and not x.has_buff(
                                buff.CHRONOBOOSTENERGYCOST))
                            if target.exists:
                                target = target.random
                if target:
                    self.do(nexus(ability.EFFECT_CHRONOBOOSTENERGYCOST, target))

    async def adept_hunt(self):
        adepts = self.army(unit.ADEPT).ready
        destination = self.enemy_start_locations[0]
        if adepts.amount > 3:
            for adept in adepts:
                targets = self.enemy_units().filter(lambda x: x.type_id in self.workers_ids and x.distance_to(adept) < 12)
                if targets.exists:

                    closest = targets.closest_to(adept)
                    target = targets.sorted(lambda x: x.health + x.shield)[0]
                    if target.health_percentage * target.shield_percentage == 1 or \
                            target.distance_to(adept) > closest.distance_to(adept) + 4:
                        target = closest
                    self.do(adept.attack(target))
                elif ability.ADEPTPHASESHIFT_ADEPTPHASESHIFT in await self.get_available_abilities(adept) and\
                        adept.distance_to(destination) > 12:
                    self.do(adept(ability.ADEPTPHASESHIFT_ADEPTPHASESHIFT, destination))
                else:
                    self.do(adept.move(destination))
            for shadow in self.units(unit.ADEPTPHASESHIFT):
                self.do(shadow.move(destination))



    async def blink(self, stalker, target):
        abilities = await self.get_available_abilities(stalker)
        if ability.EFFECT_BLINK_STALKER in abilities:
            self.do(stalker(ability.EFFECT_BLINK_STALKER, target))
            return True
        else:
            return False


def test(real_time=0):
    results = []
    score_board = {Race.Protoss: {'win': {}, 'loose':{}}, Race.Zerg: {'win': {}, 'loose':{}},Race.Terran:
        {'win': {}, 'loose':{}}}
    win = 0
    loose = 0
    r = 1
    for i in range(r):
        try:
            result = botVsComputer(real_time)
            result_str = str(result[0]) + ' ' + str(result[2]) + ' ' + str(result[1])
            print(result_str)
            if result[0] == Result.Victory:
                if result[1] not in score_board[result[2]]['win'].keys():
                    score_board[result[2]]['win'][result[1]] = 1
                else:
                    score_board[result[2]]['win'][result[1]] += 1
                win += 1
            else:
                if result[1] not in score_board[result[2]]['loose'].keys():
                    score_board[result[2]]['loose'][result[1]] = 1
                else:
                    score_board[result[2]]['loose'][result[1]] += 1
                loose += 1
        except Exception as ex:
            print('Error.')
            print(ex)

    print('================= Results ===================')
    for res in results:
        print(res)
    print('=============================================')
    print('win: ' + str(win) + '/' + str(r))
    print('vs Protoss:')
    for key in score_board[Race.Protoss]['win']:
        print(str(key) + ': ' + str(score_board[Race.Protoss]['win'][key]) + ' / ' + str(score_board[Race.Protoss]['loose'][key]))
    print('vs Zerg:')
    for key in score_board[Race.Zerg]['win']:
        print(str(key) + ': ' + str(score_board[Race.Zerg]['win'][key]) + ' / ' + str(score_board[Race.Zerg]['loose'][key]))
    print('vs Terran: ')
    for key in score_board[Race.Terran]['win']:
        print(str(key) + ': ' + str(score_board[Race.Terran]['win'][key]) + ' / ' + str(score_board[Race.Terran]['loose'][key]))
    print('=============================================')


def botVsComputer(real_time):
    maps_set = ['blink', "zealots", "AcropolisLE", "DiscoBloodbathLE", "ThunderbirdLE", "TritonLE", "Ephemeron",
                "WintersGateLE", "WorldofSleepersLE"]
    races = [Race.Protoss, Race.Zerg, Race.Terran]
    # computer_builds = [AIBuild.Rush]
    # computer_builds = [AIBuild.Air]
    computer_builds = [AIBuild.Macro, AIBuild.Power]
    build = random.choice(computer_builds)
    # map_index = random.randint(0, 6)
    race_index = random.randint(0, 2)
    res = run_game(map_settings=maps.get(maps_set[2]), players=[
        Bot(race=Race.Protoss, ai=Octopus(), name='Octopus'),
        Computer(race=races[0], difficulty=Difficulty.VeryHard, ai_build=build)
    ], realtime=bool(real_time))
    return res, build, races[race_index]


if __name__ == '__main__':
    test(real_time=1)
    # player_vs_computer()
