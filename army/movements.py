from sc2.ids.unit_typeid import UnitTypeId as unit


class Movements:
    def __init__(self,ai):
        self.ai = ai

    async def attack_formation(self):
        enemy_units = self.ai.enemy_units()
        en = enemy_units.filter(lambda x: x.type_id not in self.ai.units_to_ignore and (x.can_attack_ground or
                                                                                        x.can_attack_air))
        enemy = en
        if enemy.amount > 2:
            if enemy.closer_than(40,self.ai.start_location).amount > 7:
                await self.ai.defend()
                return
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


        start = self.ai.army.find_by_tag(self.ai.leader_tag)#self.ai.army.closest_to(destination)
        self.ai.destination = destination

        # point halfway
        dist = start.distance_to(destination)
        if dist > 12:
            point = start.position.towards(destination,dist / 2)
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
        _range = 7 if self.ai.army.amount < 24 else 12
        nearest = self.ai.army.closer_than(_range,start.position)

        if en.exists and en.closer_than(12,start.position).exists:
            flag = False
        else:
            flag = True

        if nearest.amount > self.ai.army.amount * 0.60 and flag:
            for man in self.ai.army:
                if enemy is not None and not enemy.in_attack_range_of(man).exists:
                    if man.type_id == unit.STALKER:
                        if not await self.ai.blink(man,enemy.closest_to(man).position.towards(man.position,6)):
                            self.ai.do(man.attack(enemy.closest_to(man)))
                    else:
                        closest_en = enemy.closest_to(man)
                        self.ai.do(man.attack(closest_en))
                elif enemy is None:
                    self.ai.do(man.attack(position))
        else:
            # center = nearest.center
            for man in self.ai.army.filter(lambda man_: man_.distance_to(start) > _range / 2):
                self.ai.do(man.move(start))
