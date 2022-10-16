import argparse
import json
import os
import sys
from sc2 import Race


class EnemyInfo:
    def __init__(self, ai):
        self.ai = ai
        self.opponent_id = None
        self.dir_path = None
        self.opponent_file_path = None
        self.enemy = None

    async def get_opponent_id(self):
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('--OpponentId',type=str,nargs="?",help='Opponent Id')
            args,unknown = parser.parse_known_args()
            if args.OpponentId:
                return str(args.OpponentId)
            else:
                print('opponent id is none.')
                await self.ai.chat_send('opponent id is none.')
                return None
        except Exception as ex:
            print('error: Cannot read opponent id.')
            print(ex)
            return None

    async def pre_analysis(self):
        try:
            self.opponent_id = await self.get_opponent_id()
            if self.opponent_id:
                self.opponent_id = self.opponent_id[:7]
                dir_ = os.path.realpath(sys.argv[0]) if sys.argv[0] else None
                if dir_:
                    self.dir_path = os.path.dirname(os.path.abspath(dir_))
                else:
                    print('dir error')
                    return
                print('opponent id: '+ str(self.opponent_id))
                self.opponent_file_path = os.path.join(self.dir_path,'data','enemy_info',self.opponent_id + '.json')
                print('opponent_file_path: ' + self.opponent_file_path)
                if os.path.isfile(self.opponent_file_path):
                    print('file exists.')
                    # enemy = None
                    with open(self.opponent_file_path, 'r') as file:
                        self.enemy = json.load(file)
                    # await self.ai.chat_send(str(self.enemy))
                    if self.enemy['last_game']['result'] is 1:   # last game won, play the same strategy
                        strategy_chosen = self.enemy['last_game']['strategy']
                    else:    # last game lost
                        if self.ai.enemy_race == Race.Zerg:
                            available_strats = ['adept_defend', 'adept_proxy', 'air']
                        else:
                            available_strats = ['stalker_proxy', 'air']
                        max_ = -1
                        strategy_chosen = None
                        for strategy in self.enemy['scoreboard']:
                            if strategy != self.enemy['last_game']['strategy'] and strategy in available_strats:
                                win = self.enemy['scoreboard'][strategy]['win']
                                total = self.enemy['scoreboard'][strategy]['total']
                                if total == 0:
                                    win_rate = 1
                                elif win == 0:
                                    win_rate = 0.3 / total
                                else:
                                    win_rate = win / total
                                if win_rate > max_:
                                    max_ = win_rate
                                    strategy_chosen = strategy
                    return strategy_chosen
                else:
                    print('file does not exist')
                    print('new opponent')
                    await self.ai.chat_send("new opponent.")
            else:
                print("opponent_id is None")
                await self.ai.chat_send("opponent_id is None")
        except Exception as ex:
            print('error.')
            await self.ai.chat_send('recognition error')
            print(ex)

    def post_analysis(self, score):
        if self.enemy is None:
            self.enemy = {
                'id': self.opponent_id,
                'last_game': {'strategy': '', 'result': 0},
                'scoreboard': {
                    'stalker_proxy': {'win': 0,'total': 0},
                    'adept_defend': {'win': 0,'total': 0},
                    '2b_archons': {'win': 0,'total': 0},
                    'adept_proxy': {'win': 0,'total': 0},
                    'air': {'win': 0,'total': 0},
                    '2b_colossus': {'win': 0,'total': 0},
                    'macro': {'win': 0,'total': 0},
                    'bio': {'win': 0,'total': 0},
                    'dt': {'win': 0,'total': 0},
                    'stalker_defend': {'win': 0,'total': 0}
                }
            }
        # load general stats file
        general_stats_path = os.path.join(self.dir_path,'data','enemy_info','general_stats.json')
        if os.path.isfile(general_stats_path):
            with open(general_stats_path,'r') as file:
                general_stats = json.load(file)
        else:
            general_stats = {
                    'total': {'win': 0,'total': 0},
                    'stalker_proxy': {'win': 0,'total': 0},
                    'adept_defend': {'win': 0,'total': 0},
                    '2b_archons': {'win': 0,'total': 0},
                    'adept_proxy': {'win': 0,'total': 0},
                    'air': {'win': 0,'total': 0},
                    '2b_colossus': {'win': 0,'total': 0},
                    'macro': {'win': 0,'total': 0},
                    'bio': {'win': 0,'total': 0},
                    'dt': {'win': 0,'total': 0},
                    'stalker_defend': {'win': 0,'total': 0}
            }
        # update scoreboard
        self.enemy['scoreboard'][self.ai.starting_strategy]['total'] += 1
        general_stats[self.ai.starting_strategy]['total'] += 1
        general_stats['total']['total'] += 1
        if score:
            self.enemy['scoreboard'][self.ai.starting_strategy]['win'] += 1
            general_stats[self.ai.starting_strategy]['win'] += 1
            general_stats['total']['win'] += 1

        self.enemy['last_game']['strategy'] = self.ai.starting_strategy
        self.enemy['last_game']['result'] = score
        print('writing enemy info to ' + self.opponent_file_path)
        with open(self.opponent_file_path,'w+') as file:
            json.dump(self.enemy, file)
        print('done.')
        print('writing general stats to ' + general_stats_path)
        with open(general_stats_path,'w+') as file:
            json.dump(general_stats, file)
        print('done.')