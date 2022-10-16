import neural.model as model
from collections import deque
import numpy as np
import random
import collections


REPLAY_MEMORY_MAX_SIZE = 512
REPLAY_MEMORY_MIN_SIZE = 256
BATCH_SIZE = 128
TARGET_MODEL_UPDATE_INTERVAL = 5

DISCOUNT_RATE = 0.99
# EXPLORATION_RATE_DECAY = 0.0003
EXPLORATION_RATE_MIN = 0.001


class DQN:
    def __init__(self):
        # gets trained every step
        try:
            self.main_model = model.load_model('model.ml')
        except:
            self.main_model = model.newCNNNetwork()
        # gets main_models weights every n steps
        self.target_model = model.newCNNNetwork()
        self.target_model.set_weights(self.main_model.get_weights())
        self.replay_memory = deque(maxlen=REPLAY_MEMORY_MAX_SIZE)
        self.target_model_update_counter = 0
        self.exploration_rate = 0.75

    def train(self):
        # print('replay mem size:' + str(len(self.replay_memory)))
        # check replay memory size
        if len(self.replay_memory) >= REPLAY_MEMORY_MIN_SIZE:
            # train
            # get random batch
            batch_original = random.sample(self.replay_memory, BATCH_SIZE)
            # predict for each state a q value
            new_states = []
            final_states = []
            # repeat = ([item for item,count in collections.Counter([x['id'] for x in batch_original]).items() if count > 1])
            # if len(repeat) > 0:
            #     print("REPEAT!")
            batch = []
            for full_state in batch_original:
                if full_state['new_state'] is None:
                    final_states.append(full_state)
                else:
                    batch.append(full_state)
                    new_states.append(full_state['new_state'])
            xs = [x['state'] for x in batch]  # x for normal states
            xs.extend([x['state'] for x in final_states])  # add states of final states
            xs = np.array(xs)
            xs = xs.reshape(xs.shape[0],64,64,3)
            new_states = np.array(new_states)
            new_states = new_states.reshape(new_states.shape[0],64,64,3)

            ys = []
            total_qs = self.main_model.predict(xs, batch_size=32)
            total_new_qs = self.target_model.predict(new_states, batch_size=32)
            i = 0
            for data in batch:
                # predict q values for given state
                qs = total_qs[i]   # self.main_model.predict(data['state'], batch_size=1)[0]
                # calculate new q value
                # if data['new_state'] is None:  # final step
                #     new_q = data['reward']  # reward
                # else:
                # predict max future q value for next state
                max_future_q = np.max(total_new_qs[i])   # np.max(self.target_model.predict(data['new_state'], batch_size=1)[0])
                new_q = data['reward'] + DISCOUNT_RATE * max_future_q
                # print(qs)
                # print(qs.shape)
                qs[data['action']] = new_q
                # xs.append(data['state'])
                ys.append(qs)
                i += 1

            for data in final_states:
                qs = total_qs[i]
                new_q = data['reward']
                qs[data['action']] = new_q
                ys.append(qs)
                i += 1

            # xs = np.array(xs)
            # xs = xs.reshape(xs.shape[0], 64, 64, 3)
            ys = np.array(ys)
            # train main_model with batch, x = states, y = new q values
            # print('starting training....')
            self.main_model.fit(x=xs, y=ys,epochs=1, batch_size=32, verbose=1, shuffle=False)
            # update target_model every n steps
            if self.target_model_update_counter == TARGET_MODEL_UPDATE_INTERVAL:
                self.target_model_update_counter = 0
                self.target_model.set_weights(self.main_model.get_weights())
            self.target_model_update_counter += 1

    def get_decision(self, input_img):
        if random.uniform(0,1) > self.exploration_rate:
            return np.argmax(self.main_model.predict(input_img, batch_size=1))
        else:
            return random.randint(0,3)
