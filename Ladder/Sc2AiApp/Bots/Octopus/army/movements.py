from sc2.ids.unit_typeid import UnitTypeId as unit


class Movements:
    def __init__(self,ai):
        self.ai = ai

    async def attack_formation_brand_new_newest_thee_most_new_shit_in_whole_wide_world(self):
        enemy_units = self.ai.enemy_units()
        enemy = enemy_units.filter(lambda x: x.type_id not in self.ai.units_to_ignore and (x.can_attack_ground or x.can_attack_air))
        enemy.extend(self.ai.enemy_structures().filter(lambda b: b.type_id in self.ai.bases_ids or b.can_attack_ground or b.can_attack_air))
        if self.ai.enemy_main_base_down or (self.ai.army.closer_than(20,self.ai.enemy_start_locations[0]).amount > 17 and
                not self.ai.enemy_structures().exists):
            if not self.ai.enemy_main_base_down:
                await self.ai.chat_send('enemy main base down.')
                self.ai.enemy_main_base_down = True
            self.ai.scan()
            enemy_units.extend(self.ai.enemy_structures())
            if enemy_units.exists:
                for man in self.ai.army.exclude_type(unit.OBSERVER):
                    self.ai.do(man.attack(enemy_units.closest_to(man)))
            return
        if enemy.amount > 2:
            if enemy.closer_than(25,self.ai.start_location).amount > 5:
                destination = enemy.closest_to(self.ai.start_location).position
            else:
                destination = enemy.further_than(30, self.ai.start_location)
                if destination:
                    destination = destination.closest_to(self.ai.start_location).position
                elif self.ai.enemy_structures().exists:
                    enemy = self.ai.enemy_structures()
                    destination = enemy.closest_to(self.ai.start_location).position
                else:
                    enemy = None
                    destination = self.ai.enemy_start_locations[0].position
        elif self.ai.enemy_structures().exists:
            enemy = self.ai.enemy_structures()
            destination = enemy.closest_to(self.ai.start_location).position
        else:
            enemy = None
            destination = self.ai.enemy_start_locations[0].position

        if self.ai.leader_tag is None or self.ai.army.find_by_tag(self.ai.leader_tag) is None:
            self.ai.leader_tag = self.ai.army.closest_to(destination).tag

        leader = self.ai.army.find_by_tag(self.ai.leader_tag)
        self.ai.destination = destination

        # point halfway
        dist = leader.distance_to(destination)
        step = 23
        if dist > step:
            point = leader.position.towards(destination, step)
        else:
            point = destination
        position = None
        i = 0
        while position is None:
            i += 1
            position = await self.ai.find_placement(unit.PYLON,near=point.random_on_distance(i * 2),max_distance=5,
                                                                        placement_step=2, random_alternative=False)
            if i > 7:
                print("can't find position for army.")
                return
        # if everybody's here, we can go
        army = self.ai.army
        _range = 7 if army.amount < 27 else 14
        nearest = []
        i = 3
        pos = leader.position
        while not self.ai.in_pathing_grid(pos) and i < 6:
            pos = leader.position.random_on_distance(i)
            i += 1
            j = 1
            while not self.ai.in_pathing_grid(pos) and j < 3:
                # print('func j: ' + str(j))
                pos = pos.random_on_distance(j)
                j += 1
        for man in army:
            if man.distance_to(leader) <= _range:  # with army
                nearest.append(man)
                if enemy and not enemy.in_attack_range_of(man).exists:
                    # go help someone who is fighting
                    h = army.filter(lambda x: x.is_attacking)
                    if h.exists:
                        self.ai.do(man.attack(enemy.closest_to(h.closest_to(man))))
            else:   # away. join army
                self.ai.do(man.move(pos))
        if len(nearest) > len(self.ai.army) * 0.55:  # take next position
            if enemy and enemy.closer_than(11, leader).exists:
                return
            for man in army:
                self.ai.do(man.attack(position))

    async def rush(self):
        enemy_units = self.ai.enemy_units()
        enemy = enemy_units.filter(lambda x: x.type_id not in self.ai.units_to_ignore and (x.can_attack_ground or x.can_attack_air))
        enemy.extend(self.ai.enemy_structures().filter(lambda b: b.type_id in self.ai.bases_ids or b.can_attack_ground or b.can_attack_air))
        if self.ai.enemy_main_base_down or (self.ai.army.closer_than(20,self.ai.enemy_start_locations[0]).amount > 17 and
                not self.ai.enemy_structures().exists):
            if not self.ai.enemy_main_base_down:
                self.ai.enemy_main_base_down = True
            self.ai.scan()
            # enemy_units.extend(self.ai.enemy_structures())
            # if enemy_units.exists:
            #     for man in self.ai.army.exclude_type(unit.OBSERVER):
            #         self.ai.do(man.attack(enemy_units.closest_to(man)))
            # return
        if enemy.amount > 2:
            if enemy.closer_than(25,self.ai.start_location).amount > 5:
                destination = enemy.closest_to(self.ai.start_location).position
            else:
                destination = enemy.further_than(30, self.ai.start_location)
                if destination:
                    destination = destination.closest_to(self.ai.start_location).position
                elif self.ai.enemy_structures().exists:
                    enemy = self.ai.enemy_structures()
                    destination = enemy.closest_to(self.ai.start_location).position
                else:
                    enemy = None
                    destination = self.ai.enemy_start_locations[0].position
        elif self.ai.enemy_structures().exists:
            enemy = self.ai.enemy_structures()
            destination = enemy.closest_to(self.ai.start_location).position
        else:
            enemy = None
            destination = self.ai.enemy_start_locations[0].position

        if self.ai.leader_tag is None or self.ai.army.find_by_tag(self.ai.leader_tag) is None:
            self.ai.leader_tag = self.ai.army.closest_to(destination).tag

        leader = self.ai.army.find_by_tag(self.ai.leader_tag)
        self.ai.destination = destination

        # point halfway
        dist = leader.distance_to(destination)
        step = 23
        if dist > step:
            point = leader.position.towards(destination, step)
        else:
            point = destination
        position = None
        i = 0
        while position is None:
            i += 1
            position = await self.ai.find_placement(unit.PYLON,near=point.random_on_distance(i * 2),max_distance=5,
                                                                        placement_step=2, random_alternative=False)
            if i > 7:
                print("can't find position for army.")
                return
        # if everybody's here, we can go
        army = self.ai.army
        _range = 7 if army.amount < 27 else 14
        nearest = []
        i = 3
        pos = leader.position
        while not self.ai.in_pathing_grid(pos) and i < 6:
            pos = leader.position.random_on_distance(i)
            i += 1
            j = 1
            while not self.ai.in_pathing_grid(pos) and j < 3:
                # print('func j: ' + str(j))
                pos = pos.random_on_distance(j)
                j += 1
        for man in army:
            if man.distance_to(leader) <= _range:  # with army
                nearest.append(man)
                if enemy and not enemy.in_attack_range_of(man).exists:
                    # go help someone who is fighting
                    h = army.filter(lambda x: x.is_attacking)
                    if h.exists:
                        self.ai.do(man.attack(enemy.closest_to(h.closest_to(man))))
            else:   # away. join army
                self.ai.do(man.attack(pos))
        if len(nearest) > len(self.ai.army) * 0.55:
            if enemy and enemy.closer_than(11, leader).exists:
                return
            for man in army:
                self.ai.do(man.attack(position))

    async def voidrays_rush(self):
        enemy_units = self.ai.enemy_units()
        enemy = enemy_units.filter(lambda x: x.type_id not in self.ai.units_to_ignore and (x.can_attack_ground or
                                                                                        x.can_attack_air))

        if self.ai.enemy_main_base_down or self.ai.army.closer_than(12,self.ai.enemy_start_locations[0]).amount > 20 and self.ai.enemy_structures.amount == 0:
            if not self.ai.enemy_main_base_down:
                self.ai.enemy_main_base_down = True
            self.ai.scan()
            enemy_units.extend(self.ai.enemy_structures())
            if enemy_units.exists:
                for man in self.ai.army.exclude_type(unit.OBSERVER):
                    self.ai.do(man.attack(enemy_units.closest_to(man)))
            return
        if enemy.amount > 2:
            # if enemy.closer_than(40,self.ai.start_location).amount > 7:
            #     await self.ai.defend()
            #     return
            if self.ai.destination is not None:
                destination = enemy.closest_to(self.ai.destination).position
            else:
                destination = enemy.closest_to(self.ai.start_location).position
        elif self.ai.enemy_structures().exists:
            enemy = self.ai.enemy_structures()
            if self.ai.destination is not None:
                destination = enemy.closest_to(self.ai.destination).position
            else:
                destination = enemy.closest_to(self.ai.start_location).position
            # destination = enemy.closest_to(self.ai.start_location).position
        else:
            enemy = None
            destination = self.ai.enemy_start_locations[0].position

        if self.ai.leader_tag is None or self.ai.army.find_by_tag(self.ai.leader_tag) is None:
            self.ai.leader_tag = self.ai.army.closest_to(destination).tag

        leader = self.ai.army.find_by_tag(self.ai.leader_tag)     # self.ai.army.closest_to(destination)
        self.ai.destination = destination

        # point halfway
        dist = leader.distance_to(destination)
        if dist > 12:
            point = leader.position.towards(destination,dist / 2)
        else:
            point = destination
        position = None
        i = 0
        while position is None:
            i += 1
            position = await self.ai.find_placement(unit.PYLON,near=point.random_on_distance(i * 3),max_distance=15,
                                                 placement_step=5,
                                                 random_alternative=False)
            if i > 8:
                print("can't find position for army.")
                return
        # if everybody's here, we can go
        army = self.ai.army
        _range = 7 if army.amount < 20 else 12
        nearest = []
        i = 3
        pos = leader.position
        while not self.ai.in_pathing_grid(pos) and i < 6:
            pos = leader.position.random_on_distance(i)
            i += 1
            j = 1
            while not self.ai.in_pathing_grid(pos) and j < 3:
                # print('func j: ' + str(j))
                pos = pos.random_on_distance(j)
                j += 1
        for man in army:
            if man.distance_to(leader) <= _range:  # with army
                nearest.append(man)
                if enemy and not enemy.in_attack_range_of(man).exists:
                    # go help someone who is fighting
                    h = army.filter(lambda x: x.is_attacking)
                    if h.exists:
                        self.ai.do(man.attack(enemy.closest_to(h.closest_to(man))))
            else:   # away. join army
                self.ai.do(man.attack(pos))
        if len(nearest) > len(self.ai.army) * 0.3:
            if enemy and enemy.closer_than(7, leader).exists:
                return
            for man in army:
                self.ai.do(man.attack(position))

    async def attack_formation_new(self):
        enemy_units = self.ai.enemy_units()
        en = enemy_units.filter(lambda x: x.type_id not in self.ai.units_to_ignore and (x.can_attack_ground or
                                                                                        x.can_attack_air))
        enemy = en
        if self.ai.army.closer_than(12,self.ai.enemy_start_locations[0]).amount > 20 and self.ai.enemy_structures.amount == 0:
            if not self.ai.enemy_main_base_down:
                self.ai.enemy_main_base_down = True
            self.ai.scan()
            if enemy_units.exists:
                for man in self.ai.army.exclude_type(unit.OBSERVER):
                    self.ai.do(man.attack(enemy_units.closest_to(man)))
            return
        if enemy.amount > 2:
            # if enemy.closer_than(40,self.ai.start_location).amount > 7:
            #     await self.ai.defend()
            #     return
            if self.ai.destination is not None:
                destination = enemy.closest_to(self.ai.destination).position
            else:
                destination = enemy.closest_to(self.ai.start_location).position
        elif self.ai.enemy_structures().exists:
            enemy = self.ai.enemy_structures()
            if self.ai.destination is not None:
                destination = enemy.closest_to(self.ai.destination).position
            else:
                destination = enemy.closest_to(self.ai.start_location).position
            # destination = enemy.closest_to(self.ai.start_location).position
        else:
            enemy = None
            destination = self.ai.enemy_start_locations[0].position

        if self.ai.leader_tag is None or self.ai.army.find_by_tag(self.ai.leader_tag) is None:
            self.ai.leader_tag = self.ai.army.closest_to(destination).tag


        start = self.ai.army.find_by_tag(self.ai.leader_tag)     # self.ai.army.closest_to(destination)
        self.ai.destination = destination

        # point halfway
        dist = start.distance_to(destination)
        if dist > 6:
            point = start.position.towards(destination,dist / 2)
        else:
            point = destination
        position = None
        i = 0
        while position is None:
            i += 1
            position = await self.ai.find_placement(unit.PYLON,near=point.random_on_distance(i * 3),max_distance=15,
                                                 placement_step=1,
                                                 random_alternative=False)
            if i > 8:
                print("can't find position for army.")
                return
        # if everybody's here, we can go
        _range = 6 if self.ai.army.amount < 20 else 12
        nearest = self.ai.army.closer_than(_range,start.position)

        if en.exists and en.closer_than(8,start.position).exists:
            flag = False
        else:
            flag = True

        if flag:
            if nearest.amount > self.ai.army.amount * 0.7:
                for man in self.ai.army.filter(lambda man_: not man_.is_attacking):
                    # if enemy is not None and not enemy.in_attack_range_of(man).exists:
                    #     if man.type_id == unit.STALKER:
                    #         if not await self.ai.blink(man,enemy.closest_to(man).position.towards(man.position,6)):
                    #             self.ai.do(man.attack(enemy.closest_to(man)))
                    #     else:
                    #         closest_en = enemy.closest_to(man)
                    #         self.ai.do(man.attack(closest_en))
                    # if enemy is None:
                    self.ai.do(man.attack(position))
            else:
                # center = nearest.center
                for man in self.ai.army.filter(lambda man_: man_.distance_to(start) > _range / 2
                                                            and not man_.is_attacking):
                    self.ai.do(man.move(start))