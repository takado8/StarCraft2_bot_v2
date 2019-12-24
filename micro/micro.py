import sc2
from sc2.constants import FakeEffectID
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.units import Units
from sc2.position import Point2
from sc2.ids.effect_id import EffectId as effect


class Micro:
    army_ids = [unit.ADEPT,unit.STALKER,unit.ZEALOT,unit.SENTRY,unit.OBSERVER,unit.IMMORTAL,unit.ARCHON,
                unit.HIGHTEMPLAR,unit.DISRUPTOR,unit.WARPPRISM,unit.VOIDRAY]
    units_to_ignore = [unit.LARVA,unit.EGG]
    workers_ids = [unit.SCV, unit.PROBE, unit.DRONE]

    def __init__(self, ai: sc2.BotAI):
        self.ai: sc2.BotAI = ai

    async def general_micro(self):
        enemy = self.ai.enemy_units()
        if not enemy.exists:
            return

        def chunk(lst,n):
            for i in range(0,len(lst),n):
                yield lst[i:i + n]
        # stalkers // mixed
        whole_army = self.ai.units().filter(lambda x: x.type_id in self.army_ids)

        dist = 12
        group_size = 5
        c = int(len(whole_army) / group_size)
        chunks = c if c > 0 else 1
        part_army = chunk(whole_army, chunks)
        for army_l in part_army:
            army = Units(army_l, self.ai)
            if army.exists:
                # leader = self.leader
                # if leader is None:
                leader = army.random
                threats = self.ai.enemy_units().filter(
                    lambda unit_: unit_.can_attack_ground and unit_.distance_to(leader) <= dist and
                                  unit_.type_id not in self.units_to_ignore)
                threats.extend(self.ai.enemy_structures().filter(lambda x: x.can_attack_ground or x.type_id in
                                                                        [unit.NEXUS, unit.HATCHERY, unit.COMMANDCENTER]))
                if threats.exists:
                    closest_enemy = threats.closest_to(leader)
                    target = threats.filter(lambda x: x in [unit.COLOSSUS, unit.DISRUPTOR, unit.HIGHTEMPLAR,
                                                            unit.MEDIVAC, unit.SIEGETANKSIEGED, unit.SIEGETANK])
                    if target.exists:
                        target = target.sorted(lambda x: x.health + x.shield)[0]
                    else:
                        target = threats.sorted(lambda x: x.health + x.shield)[0]
                    if target.health_percentage * target.shield_percentage == 1 or target.distance_to(leader) > \
                            leader.distance_to(closest_enemy) + 3:
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
                    #     placement = await self.find_placement(unit.PYLON,pos,placement_step=1)
                    for st in army:
                        if pos is not None and st.weapon_cooldown > 0 and \
                            closest_enemy.ground_range <= st.ground_range and threats.amount * 2 > army.amount:
                            if not await self.blink(st, pos):
                                self.ai.do(st.move(st.position.towards(pos,2)))
                        else:
                            if st.distance_to(target) > 6:
                                if not await self.blink(st,target.position.towards(st,6)):
                                    self.ai.do(st.attack(target))

        #  Sentry region  #
        sents = whole_army(unit.SENTRY)
        if sents.exists:
            # sentry = sents.in_closest_distance_to_group(self.army)
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
                              unit_.type_id not in self.units_to_ignore and unit_.type_id not in self.workers_ids)

            enemy_army_center = None
            has_energy_amount = sents.filter(lambda x: x.energy >= 50).amount
            points = []
            if threats.amount > 7:#self.build_type == 'macro':
                thr = 4
                ff = 7
            else:
                thr = 2
                ff = 1
            if has_energy_amount > 0 and len(force_fields) < ff and threats.amount > thr:  # and self.time - self.force_field_time > 1:
                # self.force_field_time = self.time
                enemy_army_center = threats.center
                gap = 2
                if threats.closer_than(5, self.ai.main_base_ramp.top_center).exists:#self.build_type == 'defend_rush':
                    points.append(self.ai.main_base_ramp.protoss_wall_warpin)
                else:
                    points.append(enemy_army_center)
                    points.append(Point2((enemy_army_center.x - gap, enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x + gap, enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x, enemy_army_center.y - gap)))
                    points.append(Point2((enemy_army_center.x, enemy_army_center.y + gap)))
            for se in sents:
                abilities = await self.ai.get_available_abilities(se)
                if threats.amount > thr and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities:
                    self.ai.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                    guardian_shield_on = True
                if ability.FORCEFIELD_FORCEFIELD in abilities and enemy_army_center is not None and len(points) > 0:
                    self.ai.do(se(ability.FORCEFIELD_FORCEFIELD, points.pop(0)))
                else:
                    army_center = whole_army.closer_than(9,se)
                    if army_center.exists:
                        army_center = army_center.center
                        if se.distance_to(army_center) > 3:
                            if not threats.exists:
                                self.ai.do(se.move(army_center))
                            else:
                                self.ai.do(se.move(army_center.towards(threats.closest_to(se),-1)))
        # zealot
        for zl in whole_army(unit.ZEALOT):
            threats = self.ai.enemy_units().filter(lambda x: x.distance_to(zl) < 9).sorted(lambda x: x.health + x.shield)
            if threats.exists:
                closest = threats.closest_to(zl)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(zl) > \
                    closest.distance_to(zl) + 4 or not self.ai.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                self.ai.do(zl.attack(target))

    async def blink(self, stalker, target):
        abilities = await self.ai.get_available_abilities(stalker)
        if ability.EFFECT_BLINK_STALKER in abilities:
            self.ai.do(stalker(ability.EFFECT_BLINK_STALKER, target))
            return True
        else:
            return False