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
# from dqn import DQN
from neural import constants
from collections import deque

reward_val = {'kill': 0.1,'die': -0.1,'win': 0.3,'loose': -0.3}
# branch power build


class DeepCraft(sc2.BotAI):
    ID = 0
    army_ids = [unit.ADEPT, unit.STALKER, unit.ZEALOT]
    units_to_ignore = [unit.LARVA, unit.EGG]
    workers_ids = [unit.SCV, unit.PROBE, unit.DRONE]
    army = []
    known_enemies = []
    visual = None
    # game_map = None
    already_reseting = False
    step_reward = 0
    action_dict = {0: 'attack_closest', 1: 'attack_low_hp', 2: 'up', 3: 'down', 4: 'left',5: 'right'}
    states = []
    actions_list = []
    rewards = []
    training_interval = 2
    training_counter = 0
    #dqn = DQN()
    total_kills = deque(maxlen=10)
    kills = 0
    avgs = []
    game_counter = 0
    cc = 0

    async def on_start(self):
        pass

    async def on_step(self, iteration):
        # memory of enemy

        # for enemy in self.enemy_units():
        #     if enemy.tag not in self.known_enemies:
        #         # print('new enemy!')
        #         self.known_enemies.append(enemy.tag)
        #         # print('enemy count: ' + str(len(self.known_enemies)))

        # army
        self.army = self.units().filter(lambda x: x.type_id in self.army_ids)
        # draw map for network input.
        state = self.draw_map()

        self.states.append(self.input_from_game_state(state))
        # get decision
        action = random.randint(0,6)#self.dqn.get_decision(input_img=self.input_from_game_state(state))
        self.actions_list.append(action)
        # await self.execute_action(action)
        # reward
        self.rewards.append(self.step_reward)
        self.step_reward = 0
        # reset if end
        await self.train_and_reset()
        await self.micro_units()

    async def train_and_reset(self):
        if self.army.amount == 0 or self.enemy_units().amount == 0 and not self.already_reseting and not (len(self.army) == len(self.enemy_units()) == 0):
            print(self.cc)
            self.cc += 1
            self.already_reseting = True
            if self.army.amount == 0:
                result = 'loose'
            else:
                result = 'win'
            print('--------------------------------------------')
            print('game '+ str(self.game_counter) + '. ' + result)
            print('kills: ' + str(self.kills))
            self.total_kills.append(self.kills)
            avg = 0
            for e in self.total_kills:
                avg += e
            avg = avg / len(self.total_kills)
            print('Last 10 games avg kill: ' + str(avg))
            print('--------------------------------------------')
            self.avgs.append(avg)
            # if self.game_counter % 100 == 0:
            #     plot.plot([x for x in range(len(self.avgs))],self.avgs)
            self.game_counter += 1
            data = self.prep_data(result)
            # if len(data) > 2:
            #     self.dqn.replay_memory.extend(data)
            #     # if self.training_counter == self.training_interval:
            #     #     self.training_counter = 0
            #     self.dqn.train()
            #     self.dqn.main_model.save('model.ml')
            #     # self.training_counter += 1
            self.states = []
            self.actions_list = []
            self.rewards = []
            await self.chat_send('reset')
            self.already_reseting = False
            self.kills = 0

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
            print('enemy unit died!')
            self.known_enemies.remove(unit_tag)
            # reward ++
            self.step_reward += reward_val['kill']
            self.kills +=1
        elif unit_tag in self.army.tags:
            # print('friendly unit died!')
            # reward --
            self.step_reward += reward_val['die']

    def prep_data(self, game_result):
        res = []
        if game_result == 'win':
            self.rewards.append(reward_val['win'])
        else:
            self.rewards.append(reward_val['loose'])
        self.states.append(None)
        # print('actions len: ' + str(len(self.actions_list)))
        for j in range(len(self.actions_list)):
            full_state = {'state': self.states[j],'action': self.actions_list[j],'reward': self.rewards[j + 1],
                          'new_state': self.states[j + 1], 'id': self.ID}
            res.append(full_state)
            self.ID += 1
        # print('data len: ' + str(len(res)))
        return res

    def input_from_game_state(self, state_img):
        img = np.array(state_img)
        img = img.reshape(constants.INPUT_SHAPE.insert(0,-1))
        # img = img.reshape(tuple([-1,64,64,3]))
        # img = img / 255
        print('shape: ' + str(img.shape) + '  < ---------------------------------------')
        cv2.imshow('Visual',img)
        cv2.waitKey(1)
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
            # cv2.circle(game_map,(int(position[1]),int(position[0])),1,(blue,green,red),-1)  # BGR
            game_map[int(position[0]),int(position[1])] = (blue,green,red)
        for _unit in self.enemy_units():
            position = _unit.position
            red = 255 * ((_unit.health + _unit.shield) / 200)  # encode units health
            green = 0
            blue = 20  # ready to shot. always 0 anyway
            game_map[int(position[0]),int(position[1])] = (blue,green,red)
            # cv2.circle(game_map,(int(position[1]),int(position[0])),1,(blue,green,red),-1)  # BGR

        game_map = self.crop_image_only_outside(game_map)
        resized = cv2.resize(game_map,dsize=None,fx=4,fy=4)
        flipped = cv2.flip(resized,0)
        print('shape: ' + str(resized.shape) + '  < ------------1111---------------------')

        # cv2.imshow('Visual',resized)
        # cv2.waitKey(1)

        return resized

    def crop_image_only_outside(self, img,tol=100):

        # img is 2D or 3D image data
        # tol  is tolerance
        mask = img < tol
        if img.ndim == 3:
            mask = mask.all(2)
        m,n = mask.shape
        mask0,mask1 = mask.any(0),mask.any(1)
        col_start,col_end = mask0.argmax(),n - mask0[::-1].argmax()
        row_start,row_end = mask1.argmax(),m - mask1[::-1].argmax()
        return img[row_start:row_end,col_start:col_end]

    async def micro_units(self):
        army = self.units(unit.STALKER)
        if army.exists:
            # leader = self.leader
            # if leader is None:
            leader = army.random
            threats = self.enemy_units().filter(
                lambda unit_: unit_.can_attack_ground and unit_.distance_to(leader) <= 12 and
                              unit_.type_id not in self.units_to_ignore)
            # threats.extend(self.enemy_structures().filter(lambda x: x.can_attack_ground))
            if threats.exists:
                closest_enemy = threats.closest_to(leader)
                target = threats.sorted(lambda x: x.health + x.shield)[0]
                if target.health_percentage * target.shield_percentage == 1 or target.distance_to(leader) > \
                        leader.distance_to(closest_enemy) + 4:
                    target = closest_enemy
                pos = leader.position.towards(closest_enemy.position,-8)
                if not self.in_pathing_grid(pos):
                    # retreat point, check 4 directions
                    enemy_x = closest_enemy.position.x
                    enemy_y = closest_enemy.position.y
                    x = leader.position.x
                    y = leader.position.y
                    delta_x = x - enemy_x
                    delta_y = y - enemy_y
                    left_legal = True
                    right_legal = True
                    up_legal = True
                    down_legal = True
                    if abs(delta_x) > abs(delta_y):   # check x direction
                        if delta_x > 0:  # dont run left
                            left_legal = False
                        else:      # dont run right
                            right_legal = False
                    else:     # check y dir
                        if delta_y > 0:    # dont run up
                            up_legal = False
                        else:      # dont run down
                            down_legal = False
                    x_ = x
                    y_ = y
                    counter = 0
                    paths_length = []
                    # left
                    if left_legal:
                        while self.in_pathing_grid(Point2((x_,y_))):
                            counter += 1
                            x_ -= 1
                        paths_length.append((counter, (x_,y_)))
                        counter = 0
                        x_ = x
                    # right
                    if right_legal:
                        while self.in_pathing_grid(Point2((x_,y_))):
                            counter += 1
                            x_ += 1
                        paths_length.append((counter, (x_,y_)))
                        counter = 0
                        x_ = x
                    # up
                    if up_legal:
                        while self.in_pathing_grid(Point2((x_,y_))):
                            counter += 1
                            y_ -= 1
                        paths_length.append((counter, (x_,y_)))
                        counter = 0
                        y_ = y
                    # down
                    if down_legal:
                        while self.in_pathing_grid(Point2((x_,y_))):
                            counter += 1
                            y_ += 1
                        paths_length.append((counter, (x_,y_)))
                    max_ = (-2,0)
                    for path in paths_length:
                        if path[0] > max_[0]:
                            max_ = path
                    if max_[0] < 4:    # there is nowhere to run - fight.
                        pos = None
                    else:
                        pos = Point2(max_[1])
                # placement = None
                # while placement is None:
                #     placement = await self.find_placement(unit.PYLON,pos,placement_step=1)

                for st in army:
                    if pos is not None and st.weapon_cooldown > 0 and \
                        closest_enemy.ground_range <= st.ground_range and threats.amount * 2 > army.amount:
                        if not await self.blink(st, pos):
                            self.do(st.move(pos))
                    else:
                        if st.distance_to(target) > 6:
                            if not await self.blink(st,target.position):
                                self.do(st.attack(target))

    async def blink(self, stalker, target):
        abilities = await self.get_available_abilities(stalker)
        if ability.EFFECT_BLINK_STALKER in abilities:
            self.do(stalker(ability.EFFECT_BLINK_STALKER, target))
            return True
        else:
            return False

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
    ], realtime=True)
    return res


ai = DeepCraft()
botVsComputer(ai)

