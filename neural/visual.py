import cv2
import numpy as np


class Visual:
    def __init__(self, game_info):
        print('map size: ' + str(game_info.map_size))
        self.map_size = game_info.map_size


    def render(self, units, enemy_units):
        game_data = np.zeros((self.map_size[1],self.map_size[0],3),np.uint8)
        for y in range(self.map_size[1]):
            for x in range(self.map_size[0]):
                # game_data[y,x] = 0 if
                pass
        for unit in units:
            position = unit.position
            cv2.circle(game_data,(int(position[0]),int(position[1])),1,(50,200,0),-1)  # BGR
        for unit in enemy_units:
            position = unit.position
            cv2.circle(game_data,(int(position[0]),int(position[1])),1,(50,0,200),-1)  # BGR
        # flip horizontally to make our final fix in visual representation:
        flipped = cv2.flip(game_data,0)
        resized = cv2.resize(flipped,dsize=None,fx=4,fy=4)

        cv2.imshow('Visual',resized)
        cv2.waitKey(1)