from sc2.constants import FakeEffectID
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2
from sc2.ids.effect_id import EffectId as effect
from sc2.units import Units


class Micro:
    def __init__(self, ai):
        self.ai = ai

    async def standard(self):
        enemy = self.ai.enemy_units()
        if not enemy.exists:
            return

        def chunk(lst,n):
            for i in range(0,len(lst),n):
                yield lst[i:i + n]
        # stalkers // mixed
        whole_army = self.ai.army.exclude_type(unit.CARRIER)
        dist = 7
        group_size = 5
        c = int(len(whole_army) / group_size)
        chunks = c if c > 0 else 1
        part_army = chunk(whole_army, chunks)
        for army_l in part_army:
            army = Units(army_l, self.ai)
            if army.exists:
                # leader = self.ai.leader
                # if leader is None:
                if self.ai.destination is not None:
                    leader = army.closest_to(self.ai.destination)
                else:
                    leader = army.random
                threats = enemy.filter(
                    lambda unit_: unit_.can_attack_ground and unit_.distance_to(leader) <= dist and
                                  unit_.type_id not in self.ai.units_to_ignore)
                if self.ai.attack:
                    threats.extend(self.ai.enemy_structures().filter(lambda _x: _x.can_attack_ground or _x.type_id in
                                                                        [unit.NEXUS, unit.HATCHERY, unit.COMMANDCENTER]))
                if threats.exists:
                    closest_enemy = threats.closest_to(leader)
                    priority = threats.filter(lambda x1: x1.type_id in [unit.COLOSSUS, unit.DISRUPTOR, unit.HIGHTEMPLAR,
                        unit.MEDIVAC, unit.SIEGETANKSIEGED, unit.SIEGETANK, unit.THOR])
                    if priority.exists:
                        targets = priority.sorted(lambda x1: x1.health + x1.shield)
                        if targets[0].health_percentage * targets[0].shield_percentage == 1:
                            target = priority.closest_to(leader)
                        else:
                            target = targets[0]
                    else:
                        targets = threats.sorted(lambda x1: x1.health + x1.shield)
                        if targets[0].health_percentage * targets[0].shield_percentage == 1:
                            target = closest_enemy
                        else:
                            target = targets[0]
                    if target.distance_to(leader) > leader.distance_to(closest_enemy) + 4:
                        target = closest_enemy
                    pos = leader.position.towards(closest_enemy.position,-8)
                    if not self.ai.in_pathing_grid(pos):
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
                        if abs(delta_x) > abs(delta_y):  # check x direction
                            if delta_x > 0:  # dont run left
                                left_legal = False
                            else:  # dont run right
                                right_legal = False
                        else:  # check y dir
                            if delta_y > 0:  # dont run up
                                up_legal = False
                            else:  # dont run down
                                down_legal = False

                        x_ = x
                        y_ = y
                        counter = 0
                        paths_length = []
                        # left
                        if left_legal:
                            while self.ai.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                x_ -= 1
                            paths_length.append((counter,(x_,y_)))
                            counter = 0
                            x_ = x
                        # right
                        if right_legal:
                            while self.ai.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                x_ += 1
                            paths_length.append((counter,(x_,y_)))
                            counter = 0
                            x_ = x
                        # up
                        if up_legal:
                            while self.ai.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                y_ -= 1
                            paths_length.append((counter,(x_,y_)))
                            counter = 0
                            y_ = y
                        # down
                        if down_legal:
                            while self.ai.in_pathing_grid(Point2((x_,y_))):
                                counter += 1
                                y_ += 1
                            paths_length.append((counter,(x_,y_)))

                        max_ = (-2,0)
                        for path in paths_length:
                            if path[0] > max_[0]:
                                max_ = path
                        if max_[0] < 4:  # there is nowhere to run - fight.
                            pos = None
                        else:
                            pos = Point2(max_[1])
                    # placement = None
                    # while placement is None:
                    #     placement = await self.ai.find_placement(unit.PYLON,pos,placement_step=1)

                    for st in army:
                        if st.shield_percentage < 0.1:
                            if st.health_percentage < 0.15:
                                self.ai.do(st.move(pos))
                                continue
                            else:
                                d = 4
                        else:
                            d = 2

                        if pos is not None and st.weapon_cooldown > 0 and \
                            closest_enemy.ground_range <= st.ground_range and threats.amount * 2 > army.amount:
                            if not await self.ai.blink(st, pos):
                                self.ai.do(st.move(st.position.towards(pos,d)))
                        else:
                            if st.distance_to(target) > 6:
                                if not await self.ai.blink(st,target.position.towards(st,6)):
                                    self.ai.do(st.attack(target))

        #  Sentry region  #
        sents = self.ai.army(unit.SENTRY)
        if sents.exists:
            # sentry = sents.in_closest_distance_to_group(self.ai.army)
            m = -1
            for se in sents:
                close = sents.closer_than(7, se).amount
                if close > m:
                    m = close
                    sentry = se
            force_fields = []
            guardian_shield_on = False
            for eff in self.ai.state.effects:
                if eff.id == FakeEffectID.get(unit.FORCEFIELD.value):
                    force_fields.append(eff)
                elif not guardian_shield_on and eff.id == effect.GUARDIANSHIELDPERSISTENT:
                    guardian_shield_on = True
            threats = self.ai.enemy_units().filter(
                lambda unit_: unit_.can_attack_ground and unit_.distance_to(sentry) <= 16 and
                              unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids)

            enemy_army_center = None
            has_energy_amount = sents.filter(lambda x2: x2.energy >= 50).amount
            points = []
            if self.ai.strategy.type == 'macro':
                thr = 4
                ff = 7
            else:
                thr = 2
                ff = 1
            if has_energy_amount > 0 and len(force_fields) < ff and threats.amount > thr:  # and self.ai.time - self.ai.force_field_time > 1:
                # self.ai.force_field_time = self.ai.time
                enemy_army_center = threats.center
                gap = 2
                if self.ai.strategy.type == 'defend_rush':
                    points.append(self.ai.main_base_ramp.protoss_wall_warpin)
                else:
                    points.append(enemy_army_center)
                    points.append(Point2((enemy_army_center.x - gap, enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x + gap, enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x, enemy_army_center.y - gap)))
                    points.append(Point2((enemy_army_center.x, enemy_army_center.y + gap)))
            for se in self.ai.units(unit.SENTRY):
                abilities = await self.ai.get_available_abilities(se)
                if threats.amount > thr and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities:
                    self.ai.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                    guardian_shield_on = True
                if ability.FORCEFIELD_FORCEFIELD in abilities and enemy_army_center is not None and len(points) > 0:
                    self.ai.do(se(ability.FORCEFIELD_FORCEFIELD, points.pop(0)))
                else:
                    army_center = self.ai.army.closer_than(9,se)
                    if army_center.exists:
                        army_center = army_center.center
                        if se.distance_to(army_center) > 3:
                            if not threats.exists:
                                self.ai.do(se.move(army_center))
                            else:
                                self.ai.do(se.move(army_center.towards(threats.closest_to(se),-1)))

        # Carrier
        for cr in self.ai.army(unit.CARRIER):
            threats = self.ai.enemy_units().filter(lambda z: z.distance_to(cr) < 12 and z.type_id not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                # target2 = None
                priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                if priority.exists:
                    # closest = priority.closest_to(cr)
                    # if cr.distance_to(closest) < 7:
                    #     self.ai.do(cr.move(cr.position.towards(closest,-3)))
                    # else:
                    if priority.amount > 2:
                        priority = sorted(priority[:int(len(priority)/2)], key=lambda z: z.health+z.shield)
                    target2 = priority[0]
                else:
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    self.ai.do(cr.attack(target2))

        # zealot
        for zl in self.ai.army(unit.ZEALOT):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(zl) < 9).sorted(lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(zl)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(zl) > \
                    closest.distance_to(zl) + 4 or not self.ai.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                if ability.EFFECT_CHARGE in await self.ai.get_available_abilities(zl):
                    self.ai.do(zl(ability.EFFECT_CHARGE, target))
                self.ai.do(zl.attack(target))

    async def personal(self):
        enemy = self.ai.enemy_units()
        if not enemy.exists:
            return
        whole_army = self.ai.army.exclude_type(unit.CARRIER)
        dist = 9
        for man in whole_army:
            threats = enemy.filter(
                lambda unit_: unit_.can_attack_ground and unit_.distance_to(man) <= dist and
                              unit_.type_id not in self.ai.units_to_ignore)
            if self.ai.attack:
                threats.extend(self.ai.enemy_structures().filter(lambda _x: _x.can_attack_ground or _x.type_id in
                                                                    [unit.NEXUS, unit.HATCHERY, unit.COMMANDCENTER]))
            if threats.exists:
                closest_enemy = threats.closest_to(man)
                priority = threats.filter(lambda x1: x1.type_id in [unit.COLOSSUS, unit.DISRUPTOR, unit.HIGHTEMPLAR,
                    unit.MEDIVAC, unit.SIEGETANKSIEGED, unit.SIEGETANK, unit.THOR])
                if priority.exists:
                    targets = priority.sorted(lambda x1: x1.health + x1.shield)
                    if targets[0].health_percentage * targets[0].shield_percentage == 1:
                        target = priority.closest_to(man)
                    else:
                        target = targets[0]
                else:
                    targets = threats.sorted(lambda x1: x1.health + x1.shield)
                    if targets[0].health_percentage * targets[0].shield_percentage == 1:
                        target = closest_enemy
                    else:
                        target = targets[0]
                if target.distance_to(man) > man.distance_to(closest_enemy) + 4:
                    target = closest_enemy
                pos = man.position.towards(closest_enemy.position,-8)
                if not self.ai.in_pathing_grid(pos):
                    # retreat point, check 4 directions
                    enemy_x = closest_enemy.position.x
                    enemy_y = closest_enemy.position.y
                    x = man.position.x
                    y = man.position.y
                    delta_x = x - enemy_x
                    delta_y = y - enemy_y
                    left_legal = True
                    right_legal = True
                    up_legal = True
                    down_legal = True
                    if abs(delta_x) > abs(delta_y):  # check x direction
                        if delta_x > 0:  # dont run left
                            left_legal = False
                        else:  # dont run right
                            right_legal = False
                    else:  # check y dir
                        if delta_y > 0:  # dont run up
                            up_legal = False
                        else:  # dont run down
                            down_legal = False

                    x_ = x
                    y_ = y
                    counter = 0
                    paths_length = []
                    # left
                    if left_legal:
                        while self.ai.in_pathing_grid(Point2((x_,y_))):
                            counter += 1
                            x_ -= 1
                        paths_length.append((counter,(x_,y_)))
                        counter = 0
                        x_ = x
                    # right
                    if right_legal:
                        while self.ai.in_pathing_grid(Point2((x_,y_))):
                            counter += 1
                            x_ += 1
                        paths_length.append((counter,(x_,y_)))
                        counter = 0
                        x_ = x
                    # up
                    if up_legal:
                        while self.ai.in_pathing_grid(Point2((x_,y_))):
                            counter += 1
                            y_ -= 1
                        paths_length.append((counter,(x_,y_)))
                        counter = 0
                        y_ = y
                    # down
                    if down_legal:
                        while self.ai.in_pathing_grid(Point2((x_,y_))):
                            counter += 1
                            y_ += 1
                        paths_length.append((counter,(x_,y_)))

                    max_ = (-2,0)
                    for path in paths_length:
                        if path[0] > max_[0]:
                            max_ = path
                    if max_[0] < 4:  # there is nowhere to run - fight.
                        pos = None
                    else:
                        pos = Point2(max_[1])
                # placement = None
                # while placement is None:
                #     placement = await self.ai.find_placement(unit.PYLON,pos,placement_step=1)

                # for st in army:
                if man.shield_percentage < 0.15:
                    if man.health_percentage < 0.15:
                        self.ai.do(man.move(pos))
                        continue
                    else:
                        d = 4
                else:
                    d = 2

                if pos is not None and man.weapon_cooldown > 0 and \
                    closest_enemy.ground_range <= man.ground_range and threats.amount * 2.6 > whole_army.amount:
                    if not await self.ai.blink(man, pos):
                        self.ai.do(man.move(man.position.towards(pos,d)))
                else:
                    if man.distance_to(target) > 6:
                        if not await self.ai.blink(man,target.position.towards(man,6)):
                            self.ai.do(man.attack(target))

        #  Sentry region  #
        sents = self.ai.army(unit.SENTRY)
        if sents.exists:
            # sentry = sents.in_closest_distance_to_group(self.ai.army)
            m = -1
            for se in sents:
                close = sents.closer_than(7, se).amount
                if close > m:
                    m = close
                    sentry = se
            force_fields = []
            guardian_shield_on = False
            for eff in self.ai.state.effects:
                if eff.id == FakeEffectID.get(unit.FORCEFIELD.value):
                    force_fields.append(eff)
                elif not guardian_shield_on and eff.id == effect.GUARDIANSHIELDPERSISTENT:
                    guardian_shield_on = True
            threats = self.ai.enemy_units().filter(
                lambda unit_: unit_.can_attack_ground and unit_.distance_to(sentry) <= 16 and
                              unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids)

            enemy_army_center = None
            has_energy_amount = sents.filter(lambda x2: x2.energy >= 50).amount
            points = []
            if self.ai.strategy.type == 'macro':
                thr = 4
                ff = 7
            else:
                thr = 2
                ff = 1
            if has_energy_amount > 0 and len(force_fields) < ff and threats.amount > thr:  # and self.ai.time - self.ai.force_field_time > 1:
                # self.ai.force_field_time = self.ai.time
                enemy_army_center = threats.center
                gap = 2
                if self.ai.strategy.type == 'defend_rush':
                    points.append(self.ai.main_base_ramp.protoss_wall_warpin)
                else:
                    points.append(enemy_army_center)
                    points.append(Point2((enemy_army_center.x - gap, enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x + gap, enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x, enemy_army_center.y - gap)))
                    points.append(Point2((enemy_army_center.x, enemy_army_center.y + gap)))
            for se in self.ai.units(unit.SENTRY):
                abilities = await self.ai.get_available_abilities(se)
                if threats.amount > thr and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities:
                    self.ai.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                    guardian_shield_on = True
                if ability.FORCEFIELD_FORCEFIELD in abilities and enemy_army_center is not None and len(points) > 0:
                    self.ai.do(se(ability.FORCEFIELD_FORCEFIELD, points.pop(0)))
                else:
                    army_center = self.ai.army.closer_than(9,se)
                    if army_center.exists:
                        army_center = army_center.center
                        if se.distance_to(army_center) > 3:
                            if not threats.exists:
                                self.ai.do(se.move(army_center))
                            else:
                                self.ai.do(se.move(army_center.towards(threats.closest_to(se),-1)))

        # Carrier
        for cr in self.ai.army(unit.CARRIER):
            threats = self.ai.enemy_units().filter(lambda z: z.distance_to(cr) < 12 and z.type_id not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                # target2 = None
                priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                if priority.exists:
                    # closest = priority.closest_to(cr)
                    # if cr.distance_to(closest) < 7:
                    #     self.ai.do(cr.move(cr.position.towards(closest,-3)))
                    # else:
                    if priority.amount > 2:
                        priority = sorted(priority[:int(len(priority)/2)], key=lambda z: z.health+z.shield)
                    target2 = priority[0]
                else:
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    self.ai.do(cr.attack(target2))

        # zealot
        for zl in self.ai.army(unit.ZEALOT):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(zl) < 9).sorted(lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(zl)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(zl) > \
                    closest.distance_to(zl) + 5 or not self.ai.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                if ability.EFFECT_CHARGE in await self.ai.get_available_abilities(zl):
                    self.ai.do(zl(ability.EFFECT_CHARGE, target))
                self.ai.do(zl.attack(target))