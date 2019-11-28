import sc2
import random
from sc2 import run_game, maps, Race, Difficulty, Result, AIBuild
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.player import Bot, Computer
from sc2 import units
from sc2.ids.buff_id import BuffId as buff
from sc2.ids.upgrade_id import UpgradeId as upgrade
from sc2.position import Point2
import numpy as np
import cv2
from dqn import DQN



reward_val = {'kill': 0.1,'die': -0.1,'win': 0.3,'loose': -0.3}


class DeepCraft(sc2.BotAI):
    army_ids = [unit.ADEPT, unit.STALKER, unit.ZEALOT]
    units_to_ignore = [unit.LARVA, unit.EGG]
    workers_ids = [unit.SCV, unit.PROBE, unit.DRONE]
    army = []
    known_enemies = []
    visual = None
    # game_map = None

    step_reward = 0
    action_dict = {0: 'attack_closest', 1: 'attack_low_hp', 2: 'up', 3: 'down', 4: 'left',5: 'right'}
    states = []
    actions_list = []
    rewards = []

    dqn = None

    async def on_start(self):
        pass

    async def on_step(self, iteration):
        # memory of enemy

        for enemy in self.enemy_units():
            if enemy.tag not in self.known_enemies:
                # print('new enemy!')
                self.known_enemies.append(enemy.tag)
                # print('enemy count: ' + str(len(self.known_enemies)))

        # army
        self.army = self.units().filter(lambda x: x.type_id in self.army_ids)
        # draw map for network input.
        state = self.draw_map()

        self.states.append(self.input_from_game_state(state))
        # get decision
        action = random.randint(0,5)#self.dqn.get_decision(input_img=state)
        self.actions_list.append(action)
        await self.execute_action(action)
        # reward
        self.rewards.append(self.step_reward)
        self.step_reward = 0


    async def execute_action(self, action):
        if len(self.army) > 0:
            leader = None
            if len(self.army) > 2:
                for man in self.army:
                    close = self.army.closer_than(10,man)
                    if close.exists and close.amount >= len(self.army) * 0.33:
                        leader = man.position
                        break
                if leader is None:
                    leader = self.army.random.position
                else:
                    leader = close.center
            else:
                leader = self.army.random.position
            if action == 0:  # attack closest
                if self.enemy_units().exists:
                    target = self.enemy_units().closest_to(leader)
                    for man in self.army:
                        self.do(man.attack(target))
            elif action == 1:  # attack low hp
                if self.enemy_units().exists:
                    target = self.enemy_units().sorted(lambda x: x.health + x.shield)[0]
                    for man in self.army:
                        self.do(man.attack(target))
            else:  # move
                x = leader.x
                y = leader.y
                if action == 2:  # up
                    y += 5
                elif action == 3:  # down
                    y -= 5
                elif action == 4:  # left
                    x -= 5
                elif action == 5:  # right
                    x += 5
                position = Point2((x,y))
                placement = None
                while placement is None:
                    placement = await self.find_placement(unit.PYLON,position,placement_step=1)
                for man in self.army:
                    self.do(man.move(placement))

    async def on_unit_destroyed(self,unit_tag):
        if unit_tag in self.known_enemies:
            # print('enemy unit died!')
            self.known_enemies.remove(unit_tag)
            # reward ++
            self.step_reward += reward_val['kill']
        elif unit_tag in self.army.tags:
            # print('friendly unit died!')
            # reward --
            self.step_reward += reward_val['die']

    def input_from_game_state(self, state_img):
        img = np.array(state_img)
        img = img.reshape(-1,64,64,3)
        img = img / 255
        return img

    def draw_map(self):
        x = self.game_info.map_size[0]
        y = self.game_info.map_size[1]
        # print('map size: x: ' + str(x) + ' y: ' + str(y))
        game_map = np.zeros((x,y,3),np.uint8)
        # print(game_map.shape)
        for i in range(x):
            for j in range(y):
                if self.in_pathing_grid(Point2((i,j))):
                    game_map[i,j] = (255,255,255)
        game_map = 255 - game_map

        for _unit in self.units():
            position = _unit.position
            red = 255 * ((_unit.health + _unit.shield) / 200)  # encode units health
            green = 255
            blue = (_unit.weapon_cooldown / 50) * 255  # ready to shot, or not
            # print('cd: '+str(_unit.weapon_cooldown))
            cv2.circle(game_map,(int(position[1]),int(position[0])),1,(blue,green,red),-1)  # BGR
            # game_data[10*int(position[1]),10*int(position[0])] = (50,200,0)
        for _unit in self.enemy_units():
            position = _unit.position
            red = 255 * ((_unit.health + _unit.shield) / 200)  # encode units health
            green = 0
            blue = 20  # ready to shot. always 0 anyway
            # game_data[10*int(position[1]),10*int(position[0])] = (50,0,200)
            cv2.circle(game_map,(int(position[1]),int(position[0])),1,(blue,green,red),-1)  # BGR

        resized = cv2.flip(cv2.resize(game_map,dsize=None,fx=4,fy=4),0)
        cv2.imshow('Visual',resized)
        cv2.waitKey(1)
        return game_map


def botVsComputer(ai):
    maps_set = ["zealots","roaches", "Bandwidth", "Reminiscence", "TheTimelessVoid", "PrimusQ9", "Ephemeron",
                "Sanglune", "Urzagol"]
    training_maps = ["DefeatZealotswithBlink", "ParaSiteTraining"]
    races = [sc2.Race.Protoss, sc2.Race.Zerg, sc2.Race.Terran]
    map_index = random.randint(0, 6)
    race_index = random.randint(0, 2)
    res = run_game(map_settings=maps.get(maps_set[0]), players=[
        Bot(race=Race.Protoss, ai=ai, name='Octopus'),
        Computer(race=races[1], difficulty=Difficulty.Hard, ai_build=AIBuild.Macro)
    ], realtime=False)
    return res


def prep_data(states, actions, rewards):
    res = []
    print('actions len: ' + str(len(actions)))
    for j in range(len(actions)):
        full_state = {'state': states[j], 'action': actions[j],'reward': rewards[j+1],
                      'new_state': states[j+1]}
        if full_state is None:
            print('FULL STATEEE EEE')
            continue
        res.append(full_state)
    print('data len: ' + str(len(res)))
    return res


dqn = DQN()
for i in range(10):
    ai = DeepCraft()
    ai.states = []
    ai.actions_list = []
    ai.rewards = []
    ai.dqn = dqn
    result = botVsComputer(ai)
    if result == Result.Victory:
        ai.rewards.append(reward_val['win'])
    else:
        ai.rewards.append(reward_val['loose'])
    ai.states.append(None)
    print('states: ' + str(len(ai.states)))
    print('actions: ' + str(len(ai.actions_list)))
    print('rewards: ' + str(len(ai.rewards)))

    # fake_states = [None if x is None else c for c, x in enumerate(ai.states,0)]
    data = prep_data(ai.states,ai.actions_list,ai.rewards)
    # print('data len: '+ str(len(data)))
    # i = 0
    # for k in range(len(data)):# in data:
    #     print(str(k) + '. ' +str(data[k]['state']) + ', ' + str(data[k]['action']) + ', ' + str(data[k]['reward']) + ', ' + str(data[k]['new_state']))
    # print('new_state none: ' + str(data[len(data)-1]['new_state']))
    dqn.replay_memory.extend(data)
    print('repl mem size: ' + str(len(dqn.replay_memory)))
    # print('>>> result: ' + str(result))
    # train on memory
    for _ in range(20):
        dqn.train()
    dqn.main_model.save('model.ml')
