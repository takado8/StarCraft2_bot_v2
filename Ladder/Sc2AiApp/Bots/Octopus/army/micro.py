from sc2.constants import FakeEffectID
from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.position import Point2
from sc2.ids.effect_id import EffectId as effect
from sc2.units import Units
from sc2 import Race


class Micro:
    def __init__(self, ai):
        self.ai = ai

    def __in_grid(self, pos):
        try:
            return self.ai.in_pathing_grid(pos)
        except:
            return False

    async def new(self):
        enemy = self.ai.enemy_units()
        if not enemy.exists:
            return

        def chunk(lst,n):
            for k in range(0,len(lst),n):
                yield lst[k:k + n]

        # stalkers // mixed
        whole_army = self.ai.army.exclude_type({unit.ZEALOT, unit.DARKTEMPLAR, unit.WARPPRISM, unit.WARPPRISMPHASING,
                                                unit.SENTRY})
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
                    lambda unit_: (unit_.can_attack_ground or unit_.type_id == unit.DISRUPTOR)
                                  and unit_.distance_to(leader) <= dist and
                                  unit_.type_id not in self.ai.units_to_ignore)
                if self.ai.attack:
                    threats.extend(self.ai.enemy_structures().filter(lambda _x: _x.can_attack_ground or _x.can_attack_air or
                                                                     _x.type_id in self.ai.bases_ids))
                if threats.exists:
                    closest_enemy = threats.closest_to(leader)
                    priority = threats.filter(lambda x1: x1.type_id in [unit.COLOSSUS, unit.DISRUPTOR, unit.HIGHTEMPLAR,
                        unit.MEDIVAC, unit.SIEGETANKSIEGED, unit.SIEGETANK, unit.THOR])
                    if priority.exists:
                        targets = priority.sorted(lambda x1: x1.health + x1.shield)
                        if self.ai.enemy_race == Race.Protoss:
                            a = targets[0].shield_percentage
                        else:
                            a = 1
                        if targets[0].health_percentage * a == 1:
                            target = priority.closest_to(leader)
                        else:
                            target = targets[0]
                    else:
                        targets = threats.sorted(lambda x1: x1.health + x1.shield)
                        if self.ai.enemy_race == Race.Protoss:
                            a = targets[0].shield_percentage
                        else:
                            a = 1
                        if targets[0].health_percentage * a == 1:
                            target = closest_enemy
                        else:
                            target = targets[0]
                    if target.distance_to(leader) > leader.distance_to(closest_enemy) + 4:
                        target = closest_enemy

                    i = 3
                    pos = leader.position.towards(closest_enemy.position,-i)
                    while not self.__in_grid(pos) and i < 12:
                        # print('func i: ' + str(i))
                        pos = leader.position.towards(closest_enemy.position,-i)
                        i += 1
                        j = 1
                        while not self.__in_grid(pos) and j < 9:
                            # print('func j: ' + str(j))
                            pos = pos.random_on_distance(j)
                            j+=1
                    for st in army:
                        if st.shield_percentage < 0.25:
                            if st.health_percentage < 0.35:
                                self.ai.do(st.move(pos))
                                continue
                            else:
                                d = 4
                        else:
                            d = 2

                        if pos is not None and st.weapon_cooldown > 0:
                            if not await self.ai.blink(st, pos):
                                self.ai.do(st.move(st.position.towards(pos,d)))
                        elif not st.is_attacking:
                            self.ai.do(st.attack(target))

        #  Sentry region  #
        sents = self.ai.army(unit.SENTRY)
        if sents.exists:
            m = -1
            sentry = None
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
                lambda unit_: unit_.can_attack_ground or unit_.can_attack_air and unit_.distance_to(sentry) <= 9 and
                              unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids)
            has_energy_amount = sents.filter(lambda x2: x2.energy >= 50).amount
            points = []

            if has_energy_amount > 0 and len(force_fields) < 5 and threats.amount > 4:  # and self.ai.time - self.ai.force_field_time > 1:
                enemy_army_center = threats.center.towards(sentry, -1)
                gap = 3
                points.append(enemy_army_center)
                points.append(Point2((enemy_army_center.x - gap, enemy_army_center.y)))
                points.append(Point2((enemy_army_center.x + gap, enemy_army_center.y)))
                points.append(Point2((enemy_army_center.x, enemy_army_center.y - gap)))
                points.append(Point2((enemy_army_center.x, enemy_army_center.y + gap)))
            for se in self.ai.units(unit.SENTRY):
                abilities = await self.ai.get_available_abilities(se)
                if threats.amount > 4 and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities\
                        and se.distance_to(threats.closest_to(se)) < 7:
                    self.ai.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                    guardian_shield_on = True
                if ability.FORCEFIELD_FORCEFIELD in abilities and len(points) > 0:
                    self.ai.do(se(ability.FORCEFIELD_FORCEFIELD, points.pop(0)))
                else:
                    army_nearby = self.ai.army.closer_than(9,se)
                    if army_nearby.exists:
                        if threats.exists:
                            self.ai.do(se.move(army_nearby.center.towards(threats.closest_to(se),-4)))

        # Carrier
        for cr in self.ai.army(unit.CARRIER):
            threats = self.ai.enemy_units().filter(lambda z: z.distance_to(cr) < 12 and z.type_id not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air or z.type_id in self.ai.bases_ids))
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

            # high templar
        for ht in whole_army(unit.HIGHTEMPLAR):
            # if enemy.exists:
            _enemy = enemy.closer_than(9,ht)
            if _enemy.amount > 5:
                # if low energy, go behind army, else to front
                army = whole_army.closer_than(7,ht)
                if ht.energy < 50 or ht.is_idle:
                    en = _enemy.closest_to(ht)
                    place = army.furthest_to(en).position.towards(en,-7)
                    if ht.distance_to(place) > 3:
                        self.ai.do(ht.move(place))
                # Cast spells   ---> look for group of enemy
                spell_target = _enemy.filter(
                    lambda unit_: not unit_.is_structure and unit_.type_id not in self.ai.workers and
                    unit_.type_id not in self.ai.units_to_ignore)
                target = None
                if spell_target.amount > 5:
                    abilities = await self.ai.get_available_abilities(ht)
                    # medivacs = spell_target.filter(lambda x: x.type_id == unit.MEDIVAC)
                    if ability.PSISTORM_PSISTORM in abilities and \
                            self.ai.time - self.ai.psi_storm_wait > 1.4:
                        maxNeighbours = 0
                        for en in spell_target:
                            neighbours = _enemy.filter(lambda u: u.distance_to(en) <= 1.5)
                            if neighbours.amount > maxNeighbours:
                                maxNeighbours = neighbours.amount
                                target = en
                        if target is not None and self.ai.army.closer_than(1.7,target).amount < 3:
                            print("Casting Psi Storm on " + str(maxNeighbours + 1) + " units.")
                            self.ai.do(ht(ability.PSISTORM_PSISTORM,target.position))
                            self.ai.psi_storm_wait = self.ai.time

                    elif ability.FEEDBACK_FEEDBACK in abilities:
                        spell_target = spell_target.filter(lambda z: z.energy > 100).exclude_type({unit.OVERSEER})
                        if spell_target.exists:
                            spell_target = spell_target.sorted(lambda z: z.energy,reverse=True)
                            target = spell_target[0]
                            print("Casting Feedback on " + target.name + " with " + str(target.energy) + " energy.")
                            self.ai.do(ht(ability.FEEDBACK_FEEDBACK,target))
                            break

        # Disruptor
        zealots = self.ai.army(unit.ZEALOT)
        disruptors = self.ai.army(unit.DISRUPTOR)
        for dr in disruptors:
            # Cast spells   ---> look for group of enemy
            abilities = await self.ai.get_available_abilities(dr)
            if self.ai.time - self.ai.nova_wait >= 1 and ability.EFFECT_PURIFICATIONNOVA in abilities:  #
                spell_target = enemy.filter(
                    lambda unit_: not unit_.is_structure and unit_.distance_to(dr) < 12
                                  and unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids
                                  and not unit_.is_flying)
                target = None
                if spell_target.amount > 2:
                    tanks = spell_target.filter(lambda x: x.type_id == unit.SIEGETANKSIEGED or x.type_id == unit.THOR)
                    if tanks.amount > 1:
                        spell_target = tanks

                    maxNeighbours = 0
                    for en in spell_target:
                        neighbours = enemy.filter(lambda unit_: not unit_.is_flying and not
                        unit_.is_structure and unit_.distance_to(en) <= 1.5)
                        if neighbours.amount > maxNeighbours:
                            maxNeighbours = neighbours.amount
                            target = en
                    if target is not None and self.ai.army.closer_than(2.4,target).amount < 3:
                        dist = await self.ai._client.query_pathing(dr.position,target.position)
                        if dist is not None and dist <= 13:
                            print("Casting Purification nova on " + str(maxNeighbours + 1) + " units.")
                            self.ai.nova_wait = self.ai.time
                            self.ai.do(dr(ability.EFFECT_PURIFICATIONNOVA,target.position))
            else:
                threat = enemy.closer_than(7,dr)
                if threat.exists:
                    self.ai.do(dr.move(dr.position.towards(threat.closest_to(dr), -5)))
        # Disruptor purification nova
        if self.ai.time - self.ai.nova_wait > 0.4:
            for nova in self.ai.units(unit.DISRUPTORPHASED):
                spell_target = enemy.filter(lambda unit_: not unit_.is_structure and unit_.distance_to(nova) < 9
                        and unit_.type_id not in self.ai.units_to_ignore and not unit_.is_flying and unit_.type_id
                                                          not in self.ai.workers_ids)
                target = None
                if spell_target.amount > 0:
                    tanks = spell_target.filter(lambda x: x.type_id == unit.SIEGETANKSIEGED)
                    if tanks.amount > 0:
                        spell_target = tanks
                    maxNeighbours = 0
                    for en in spell_target:
                        neighbours = enemy.filter(lambda unit_: not unit_.is_structure and unit_.distance_to(nova) <= 1.5
                            and unit_.type_id not in self.ai.units_to_ignore and not unit_.is_flying and unit_.type_id
                                                                not in self.ai.workers_ids)
                        if neighbours.amount > maxNeighbours:
                            maxNeighbours = neighbours.amount
                            target = en
                    if target is not None:
                        # if self.ai.army.closer_than(3,target).amount < 2:
                        print("Steering Purification nova to " + str(maxNeighbours + 1) + " units.")
                        self.ai.do(nova.move(target.position.towards(nova, -2)))

        for wp in self.ai.army(unit.WARPPRISM):
            threats = self.ai.enemy_units().filter(lambda x: x.can_attack_air and x.distance_to(wp) < 11)
            for t in threats:
                if t.target_in_range(wp):
                    self.ai.do(wp.move(wp.position.towards(t, -5)))
        for wp in self.ai.army(unit.WARPPRISMPHASING):
            threats = self.ai.enemy_units().filter(lambda x: x.can_attack_air and x.distance_to(wp) < 11)
            for t in threats:
                if t.target_in_range(wp):
                    abilities = await self.ai.get_available_abilities(wp)
                    if ability.MORPH_WARPPRISMTRANSPORTMODE in abilities:
                        self.ai.do(wp(ability.MORPH_WARPPRISMTRANSPORTMODE))
                        self.ai.do(wp.move(wp.position.towards(t, -5), queue=True))

        for dt in self.ai.army(unit.DARKTEMPLAR):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(dt) < 9 and not x2.is_flying and
                          x2.type_id not in self.ai.units_to_ignore).sorted(lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(dt)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(dt) > \
                    closest.distance_to(dt) + 3 or not self.ai.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                self.ai.do(dt.attack(target))

        # zealot
        for zl in zealots.filter(lambda z: not z.is_attacking):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(zl) < 7).sorted(lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(zl)
                if self.ai.enemy_race == Race.Protoss:
                    a = threats[0].shield_percentage
                else:
                    a = 1
                dist = await self.ai._client.query_pathing(zl.position,threats[0].position)
                if threats[0].health_percentage * a == 1 or dist is None or dist > closest.distance_to(zl) + 4:
                    target = closest
                else:
                    target = threats[0]
                if not zl.is_attacking:
                    if ability.EFFECT_CHARGE in await self.ai.get_available_abilities(zl):
                        self.ai.do(zl(ability.EFFECT_CHARGE, target))
                    else:
                        self.ai.do(zl.attack(target))

    async def group_with_blink(self):
        enemy = self.ai.enemy_units()
        if not enemy.exists:
            return

        def chunk(lst,n):
            for k in range(0,len(lst),n):
                yield lst[k:k + n]

        # stalkers // mixed
        whole_army = self.ai.army.exclude_type({unit.ZEALOT,unit.DARKTEMPLAR,unit.WARPPRISM,unit.WARPPRISMPHASING,
                                                unit.SENTRY})
        dist = 7
        group_size = 5
        c = int(len(whole_army) / group_size)
        chunks = c if c > 0 else 1
        part_army = chunk(whole_army,chunks)
        for army_l in part_army:
            army = Units(army_l,self.ai)
            if army.exists:
                # leader = self.ai.leader
                # if leader is None:
                if self.ai.destination is not None:
                    leader = army.closest_to(self.ai.destination)
                else:
                    leader = army.random
                threats = enemy.filter(
                    lambda unit_: (unit_.can_attack_ground or unit_.type_id in [unit.DISRUPTOR, unit.MEDIVAC])
                                  and unit_.distance_to(leader) <= dist and
                                  unit_.type_id not in self.ai.units_to_ignore)
                if self.ai.attack:
                    threats.extend(
                        self.ai.enemy_structures().filter(lambda _x: _x.can_attack_ground or _x.can_attack_air or
                                                              _x.type_id == unit.BUNKER))
                if threats.exists:
                    closest_enemy = threats.closest_to(leader)
                    priority = threats.filter(lambda x1: x1.type_id in [unit.COLOSSUS,unit.DISRUPTOR,unit.HIGHTEMPLAR,
                                                                        unit.MEDIVAC,unit.SIEGETANKSIEGED, unit.CYCLONE,
                                                                        unit.SIEGETANK,unit.THOR])
                    if priority.exists:
                        targets = priority.sorted(lambda x1: x1.health + x1.shield)
                        if self.ai.enemy_race == Race.Protoss:
                            a = targets[0].shield_percentage
                        else:
                            a = 1
                        if targets[0].health_percentage * a == 1:
                            target = priority.closest_to(leader)
                        else:
                            target = targets[0]
                    else:
                        targets = threats.sorted(lambda x1: x1.health + x1.shield)
                        if self.ai.enemy_race == Race.Protoss:
                            a = targets[0].shield_percentage
                        else:
                            a = 1
                        if targets[0].health_percentage * a == 1:
                            target = closest_enemy
                        else:
                            target = targets[0]
                    if target.distance_to(leader) > leader.distance_to(closest_enemy) + 4:
                        target = closest_enemy

                    i = 3
                    pos = leader.position.towards(closest_enemy.position,-i)
                    while not self.__in_grid(pos) and i < 12:
                        # print('func i: ' + str(i))
                        pos = leader.position.towards(closest_enemy.position,-i)
                        i += 1
                        j = 1
                        while not self.__in_grid(pos) and j < 9:
                            # print('func j: ' + str(j))
                            pos = pos.random_on_distance(j)
                            j += 1
                    for st in army:
                        # for st in army:
                        if st.shield_percentage < 0.5:
                            if st.health_percentage < 0.4:
                                if not await self.ai.blink(st,pos):
                                    self.ai.do(st.move(pos))
                                continue
                            else:
                                d = 5
                        else:
                            d = 3

                        if pos is not None and st.weapon_cooldown > 0:  # blink/move backwards
                            if not await self.ai.blink(st,pos):
                                self.ai.do(st.move(st.position.towards(pos,d)))
                        else:
                            highground = (target.position3d.z - st.position3d.z > 1.2) or\
                                         await self.ai._client.query_pathing(st,target.position) is None
                            if highground or st.distance_to(
                                    target) > 7:  # blink forwards and attack
                                print('want to blink!')
                                if highground:
                                    print('highground')
                                    position = target.position.towards(st, -3)
                                else:
                                    position = target.position.towards(st,6)
                                if not await self.ai.blink(st,position):
                                    print('no blink')
                                    self.ai.do(st.attack(target))
                                else:
                                    print('blink2')
                                    self.ai.do(st.attack(target,queue=True))
                                # else:
                                #     print('blink1')
                                #     self.ai.do(man.attack(target, queue=True))
                            else:
                                print('just attack')
                                self.ai.do(st.attack(target))

        #  Sentry region  #
        sents = self.ai.army(unit.SENTRY)
        if sents.exists:
            m = -1
            sentry = None
            for se in sents:
                close = sents.closer_than(7,se).amount
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
                lambda unit_: unit_.can_attack_ground or unit_.can_attack_air and unit_.distance_to(sentry) <= 9 and
                              unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids)
            has_energy_amount = sents.filter(lambda x2: x2.energy >= 50).amount
            points = []

            if has_energy_amount > 0 and len(
                    force_fields) < 5 and threats.amount > 4:  # and self.ai.time - self.ai.force_field_time > 1:
                enemy_army_center = threats.center.towards(sentry,-1)
                gap = 3
                points.append(enemy_army_center)
                points.append(Point2((enemy_army_center.x - gap,enemy_army_center.y)))
                points.append(Point2((enemy_army_center.x + gap,enemy_army_center.y)))
                points.append(Point2((enemy_army_center.x,enemy_army_center.y - gap)))
                points.append(Point2((enemy_army_center.x,enemy_army_center.y + gap)))
            for se in self.ai.units(unit.SENTRY):
                abilities = await self.ai.get_available_abilities(se)
                if threats.amount > 4 and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities \
                        and se.distance_to(threats.closest_to(se)) < 7:
                    self.ai.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                    guardian_shield_on = True
                if ability.FORCEFIELD_FORCEFIELD in abilities and len(points) > 0:
                    self.ai.do(se(ability.FORCEFIELD_FORCEFIELD,points.pop(0)))
                else:
                    army_nearby = self.ai.army.closer_than(9,se)
                    if army_nearby.exists:
                        if threats.exists:
                            self.ai.do(se.move(army_nearby.center.towards(threats.closest_to(se),-4)))

        # Carrier
        for cr in self.ai.army(unit.CARRIER):
            threats = self.ai.enemy_units().filter(
                lambda z: z.distance_to(cr) < 12 and z.type_id not in self.ai.units_to_ignore)
            threats.extend(
                self.ai.enemy_structures().filter(lambda z: z.can_attack_air or z.type_id in self.ai.bases_ids))
            if threats.exists:
                # target2 = None
                priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps,reverse=True)
                if priority.exists:
                    # closest = priority.closest_to(cr)
                    # if cr.distance_to(closest) < 7:
                    #     self.ai.do(cr.move(cr.position.towards(closest,-3)))
                    # else:
                    if priority.amount > 2:
                        priority = sorted(priority[:int(len(priority) / 2)],key=lambda z: z.health + z.shield)
                    target2 = priority[0]
                else:
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    self.ai.do(cr.attack(target2))

            # high templar
        for ht in whole_army(unit.HIGHTEMPLAR):
            # if enemy.exists:
            _enemy = enemy.closer_than(9,ht)
            if _enemy.amount > 5:
                # if low energy, go behind army, else to front
                army = whole_army.closer_than(7,ht)
                if ht.energy < 50 or ht.is_idle:
                    en = _enemy.closest_to(ht)
                    place = army.furthest_to(en).position.towards(en,-7)
                    if ht.distance_to(place) > 3:
                        self.ai.do(ht.move(place))
                # Cast spells   ---> look for group of enemy
                spell_target = _enemy.filter(
                    lambda unit_: not unit_.is_structure and unit_.type_id not in self.ai.workers and
                                  unit_.type_id not in self.ai.units_to_ignore)
                target = None
                if spell_target.amount > 5:
                    abilities = await self.ai.get_available_abilities(ht)
                    # medivacs = spell_target.filter(lambda x: x.type_id == unit.MEDIVAC)
                    if ability.PSISTORM_PSISTORM in abilities and \
                            self.ai.time - self.ai.psi_storm_wait > 1.4:
                        maxNeighbours = 0
                        for en in spell_target:
                            neighbours = _enemy.filter(lambda u: u.distance_to(en) <= 1.5)
                            if neighbours.amount > maxNeighbours:
                                maxNeighbours = neighbours.amount
                                target = en
                        if target is not None and self.ai.army.closer_than(1.7,target).amount < 3:
                            print("Casting Psi Storm on " + str(maxNeighbours + 1) + " units.")
                            self.ai.do(ht(ability.PSISTORM_PSISTORM,target.position))
                            self.ai.psi_storm_wait = self.ai.time

                    elif ability.FEEDBACK_FEEDBACK in abilities:
                        spell_target = spell_target.filter(lambda z: z.energy > 100).exclude_type({unit.OVERSEER})
                        if spell_target.exists:
                            spell_target = spell_target.sorted(lambda z: z.energy,reverse=True)
                            target = spell_target[0]
                            print("Casting Feedback on " + target.name + " with " + str(target.energy) + " energy.")
                            self.ai.do(ht(ability.FEEDBACK_FEEDBACK,target))
                            break

        # Disruptor
        zealots = self.ai.army(unit.ZEALOT)
        disruptors = self.ai.army(unit.DISRUPTOR)
        for dr in disruptors:
            # Cast spells   ---> look for group of enemy
            abilities = await self.ai.get_available_abilities(dr)
            if self.ai.time - self.ai.nova_wait >= 1 and ability.EFFECT_PURIFICATIONNOVA in abilities:  #
                spell_target = enemy.filter(
                    lambda unit_: not unit_.is_structure and unit_.distance_to(dr) < 12
                                  and unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids
                                  and not unit_.is_flying)
                target = None
                if spell_target.amount > 2:
                    tanks = spell_target.filter(lambda x: x.type_id == unit.SIEGETANKSIEGED or x.type_id == unit.THOR)
                    if tanks.amount > 1:
                        spell_target = tanks

                    maxNeighbours = 0
                    for en in spell_target:
                        neighbours = enemy.filter(lambda unit_: not unit_.is_flying and not
                        unit_.is_structure and unit_.distance_to(en) <= 1.5)
                        if neighbours.amount > maxNeighbours:
                            maxNeighbours = neighbours.amount
                            target = en
                    if target is not None and self.ai.army.closer_than(2.4,target).amount < 3:
                        dist = await self.ai._client.query_pathing(dr.position,target.position)
                        if dist is not None and dist <= 13:
                            print("Casting Purification nova on " + str(maxNeighbours + 1) + " units.")
                            self.ai.nova_wait = self.ai.time
                            self.ai.do(dr(ability.EFFECT_PURIFICATIONNOVA,target.position))
            else:
                threat = enemy.closer_than(7,dr)
                if threat.exists:
                    self.ai.do(dr.move(dr.position.towards(threat.closest_to(dr),-5)))
        # Disruptor purification nova
        if self.ai.time - self.ai.nova_wait > 0.4:
            for nova in self.ai.units(unit.DISRUPTORPHASED):
                spell_target = enemy.filter(lambda unit_: not unit_.is_structure and unit_.distance_to(nova) < 9
                                                          and unit_.type_id not in self.ai.units_to_ignore and not unit_.is_flying and unit_.type_id
                                                          not in self.ai.workers_ids)
                target = None
                if spell_target.amount > 0:
                    tanks = spell_target.filter(lambda x: x.type_id == unit.SIEGETANKSIEGED)
                    if tanks.amount > 0:
                        spell_target = tanks
                    maxNeighbours = 0
                    for en in spell_target:
                        neighbours = enemy.filter(
                            lambda unit_: not unit_.is_structure and unit_.distance_to(nova) <= 1.5
                                          and unit_.type_id not in self.ai.units_to_ignore and not unit_.is_flying and unit_.type_id
                                          not in self.ai.workers_ids)
                        if neighbours.amount > maxNeighbours:
                            maxNeighbours = neighbours.amount
                            target = en
                    if target is not None:
                        # if self.ai.army.closer_than(3,target).amount < 2:
                        print("Steering Purification nova to " + str(maxNeighbours + 1) + " units.")
                        self.ai.do(nova.move(target.position.towards(nova,-2)))

        for wp in self.ai.army(unit.WARPPRISM):
            threats = self.ai.enemy_units().filter(lambda x: x.can_attack_air and x.distance_to(wp) < 11)
            for t in threats:
                if t.target_in_range(wp):
                    self.ai.do(wp.move(wp.position.towards(t,-5)))
        for wp in self.ai.army(unit.WARPPRISMPHASING):
            threats = self.ai.enemy_units().filter(lambda x: x.can_attack_air and x.distance_to(wp) < 11)
            for t in threats:
                if t.target_in_range(wp):
                    abilities = await self.ai.get_available_abilities(wp)
                    if ability.MORPH_WARPPRISMTRANSPORTMODE in abilities:
                        self.ai.do(wp(ability.MORPH_WARPPRISMTRANSPORTMODE))
                        self.ai.do(wp.move(wp.position.towards(t,-5),queue=True))

        for dt in self.ai.army(unit.DARKTEMPLAR):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(dt) < 9 and not x2.is_flying and
                                                              x2.type_id not in self.ai.units_to_ignore).sorted(
                lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(dt)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(dt) > \
                        closest.distance_to(dt) + 3 or not self.ai.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                self.ai.do(dt.attack(target))

        # zealot
        for zl in zealots.filter(lambda z: not z.is_attacking):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(zl) < 7).sorted(
                lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(zl)
                if self.ai.enemy_race == Race.Protoss:
                    a = threats[0].shield_percentage
                else:
                    a = 1
                dist = await self.ai._client.query_pathing(zl.position,threats[0].position)
                if threats[0].health_percentage * a == 1 or dist is None or dist > closest.distance_to(zl) + 4:
                    target = closest
                else:
                    target = threats[0]
                if not zl.is_attacking:
                    if ability.EFFECT_CHARGE in await self.ai.get_available_abilities(zl):
                        self.ai.do(zl(ability.EFFECT_CHARGE,target))
                    else:
                        self.ai.do(zl.attack(target))

    async def personal_new(self):
        enemy = self.ai.enemy_units()
        if not enemy.exists:
            return
        whole_army = self.ai.army.exclude_type({unit.CARRIER, unit.TEMPEST, unit.VOIDRAY, unit.ZEALOT})
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
                    if self.ai.enemy_race == Race.Protoss:
                        a = targets[0].shield_percentage
                    else:
                        a = 1
                    if targets[0].health_percentage * a == 1:
                        target = priority.closest_to(man)
                    else:
                        target = targets[0]
                else:
                    targets = threats.sorted(lambda x1: x1.health + x1.shield)
                    if self.ai.enemy_race == Race.Protoss:
                        a = targets[0].shield_percentage
                    else:
                        a = 1
                    if targets[0].health_percentage * a == 1:
                        target = closest_enemy
                    else:
                        target = targets[0]
                if target.distance_to(man) > man.distance_to(closest_enemy) + 4:
                    target = closest_enemy
                i=3
                pos = man.position.towards(closest_enemy.position,-i)
                while not self.__in_grid(pos) and i < 12:
                    pos = man.position.towards(closest_enemy.position,-i)
                    i += 1
                    j=1
                    while not self.__in_grid(pos) and j < 9:
                        pos = pos.random_on_distance(j)
                        j+=1

                # for st in army:
                if man.shield_percentage < 0.4:
                    if man.health_percentage < 0.35:
                        self.ai.do(man.move(pos))
                        continue
                    else:
                        d = 4
                else:
                    d = 2

                if pos is not None and man.weapon_cooldown > 0:
                    self.ai.do(man.move(man.position.towards(pos,d)))
                else:
                    if man.distance_to(target) > 6:
                        self.ai.do(man.attack(target))

                #  Sentry region  #
            sents = self.ai.army(unit.SENTRY)
            if sents.exists:
                m = -1
                sentry = None
                for se in sents:
                    close = sents.closer_than(7,se).amount
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
                    lambda unit_: unit_.can_attack_ground or unit_.can_attack_air and unit_.distance_to(sentry) <= 9 and
                                  unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids)
                has_energy_amount = sents.filter(lambda x2: x2.energy >= 50).amount
                points = []

                if has_energy_amount > 0 and len(
                        force_fields) < 5 and threats.amount > 4:  # and self.ai.time - self.ai.force_field_time > 1:
                    enemy_army_center = threats.center.towards(sentry,-1)
                    gap = 3
                    points.append(enemy_army_center)
                    points.append(Point2((enemy_army_center.x - gap,enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x + gap,enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x,enemy_army_center.y - gap)))
                    points.append(Point2((enemy_army_center.x,enemy_army_center.y + gap)))
                for se in self.ai.units(unit.SENTRY):
                    abilities = await self.ai.get_available_abilities(se)
                    if threats.amount > 4 and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities \
                            and se.distance_to(threats.closest_to(se)) < 7:
                        self.ai.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                        guardian_shield_on = True
                    if ability.FORCEFIELD_FORCEFIELD in abilities and len(points) > 0:
                        self.ai.do(se(ability.FORCEFIELD_FORCEFIELD,points.pop(0)))
                    else:
                        army_nearby = self.ai.army.closer_than(9,se)
                        if army_nearby.exists:
                            if threats.exists:
                                self.ai.do(se.move(army_nearby.center.towards(threats.closest_to(se),-4)))
        # voidray
        for vr in self.ai.army(unit.VOIDRAY):
            threats = self.ai.enemy_units().filter(lambda z: z.distance_to(vr) < 9 and z.type_id
                not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                # target2 = None
                priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                arm = False
                if priority.exists:

                    armored = priority.filter(lambda z: z.is_armored)
                    if armored.exists:
                        arm = True
                        priority = armored
                    target2 = priority[0]
                else:
                    armored = threats.filter(lambda z: z.is_armored)
                    if armored.exists:
                        arm = True
                        threats = armored
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    if arm:
                        if ability.EFFECT_VOIDRAYPRISMATICALIGNMENT in await self.ai.get_available_abilities(vr)\
                                and target2.distance_to(vr) < 8:
                            self.ai.do(vr(ability.EFFECT_VOIDRAYPRISMATICALIGNMENT))
                    self.ai.do(vr.attack(target2))

        completion_ids = {unit.VOIDRAY, unit.BATTLECRUISER, unit.CARRIER}  # units that returns wrong air dps
        # Carrier
        for cr in self.ai.army({unit.CARRIER,unit.TEMPEST}):
            threats = self.ai.enemy_units().filter(
                lambda z: z.distance_to(cr) < 20 and z.type_id not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                completion = threats.filter(lambda z: z.type_id in completion_ids)
                if completion.exists:
                    priority = completion
                else:
                    priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                    if priority.exists:
                        id0 = priority[0].type_id
                        i = 0
                        while i < len(priority) and priority[i].type_id == id0:
                            i+=1
                        priority = priority[:i]
                if priority:
                    priority = sorted(priority,key=lambda z: z.health + z.shield)
                    target2 = priority[0]
                else:
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    self.ai.do(cr.attack(target2))

        if self.ai.attack:
            for ad in self.ai.army(unit.ADEPT):
                workers = self.ai.enemy_units().filter(lambda x: x.distance_to(ad) < 17 and x.type_id in
                                                                 self.ai.workers_ids)
                threats = self.ai.enemy_units().filter(lambda x: x.distance_to(ad) < 10 and x.type_id not in
                                                       self.ai.workers_ids)
                if workers.amount < 4 or threats.amount > 3:
                    if ability.ADEPTPHASESHIFT_ADEPTPHASESHIFT in await self.ai.get_available_abilities(ad):
                        self.ai.do(ad(ability.ADEPTPHASESHIFT_ADEPTPHASESHIFT, ad.position))
                elif workers.amount > 3:
                    self.ai.do(ad.attack(workers.closest_to(ad)))
            for shadow in self.ai.units(unit.ADEPTPHASESHIFT):
                workers = self.ai.enemy_units().filter(lambda x: x.distance_to(shadow) < 11 and x.type_id in
                                                       self.ai.workers_ids)
                if workers.amount > 3:
                    self.ai.do(shadow.move(workers.closest_to(shadow)))
                # else:
                #     bases = self.ai.enemy_structures().filter(lambda x: x.type_id in self.ai.bases_ids)
                #     if bases.exists:
                #         base = bases.closest_to(shadow).position
                #         workers = self.ai.enemy_units().filter(lambda x: x.distance_to(base) < 11 and x.type_id in
                #                                                          self.ai.workers_ids)
                #         if shadow.distance_to(base) < 4 and (workers.amount < 5 or self.ai.enemy_units().filter(lambda x:
                #             x.distance_to(shadow) < 7 and x.type_id not in self.ai.workers_ids).amount > 4):
                #             self.ai.do(shadow.move(self.ai.enemy_start_locations[0]))
                #             print('going to main base case1')
                #         else:
                #             print('going to near base')
                #             self.ai.do(shadow.move(base))
                else:
                    self.ai.do(shadow.move(self.ai.enemy_start_locations[0]))
                    # print('going to main base case2')

        # zealot
        for zl in self.ai.army(unit.ZEALOT):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(zl) < 9 and not x2.is_flying and
                          x2.type_id not in self.ai.units_to_ignore).sorted(lambda _x: _x.health + _x.shield)
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

        for dt in self.ai.army(unit.DARKTEMPLAR):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(dt) < 9 and not x2.is_flying and
                          x2.type_id not in self.ai.units_to_ignore).sorted(lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(dt)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(dt) > \
                    closest.distance_to(dt) + 3 or not self.ai.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                self.ai.do(dt.attack(target))

    async def personal_with_blink(self):
        enemy = self.ai.enemy_units()
        if not enemy.exists:
            return
        whole_army = self.ai.army.exclude_type({unit.CARRIER, unit.TEMPEST, unit.VOIDRAY, unit.ZEALOT})
        dist = 13
        for man in whole_army:
            threats = enemy.filter(
                lambda unit_: unit_.can_attack_ground and unit_.distance_to(man) <= dist and
                              unit_.type_id not in self.ai.units_to_ignore)
            if self.ai.attack:
                threats.extend(self.ai.enemy_structures().filter(lambda _x: (_x.can_attack_ground or _x.type_id == unit.BUNKER)
                               and _x.distance_to(man) <= 7))
            if threats.exists:
                closest_enemy = threats.closest_to(man)
                priority = threats.filter(lambda x1: x1.type_id in [unit.COLOSSUS, unit.DISRUPTOR, unit.HIGHTEMPLAR,
                    unit.MEDIVAC, unit.SIEGETANKSIEGED, unit.IMMORTAL, unit.SIEGETANK, unit.THOR])
                if priority.exists:
                    print('priority exists:')
                    targets = priority.sorted(lambda x1: x1.health + x1.shield)
                    if self.ai.enemy_race == Race.Protoss:
                        a = targets[0].shield_percentage
                    else:
                        a = 1
                    if targets[0].health_percentage * a == 1:
                        target = priority.closest_to(man)
                    else:
                        target = targets[0]
                    print(str(target.type_id))
                else:
                    targets = threats.sorted(lambda x1: x1.health + x1.shield)
                    if self.ai.enemy_race == Race.Protoss:
                        a = targets[0].shield_percentage
                    else:
                        a = 1
                    if targets[0].health_percentage * a == 1:
                        target = closest_enemy
                    else:
                        target = targets[0]
                if man.distance_to(target) > man.distance_to(closest_enemy) + 5:
                    target = closest_enemy
                i=4
                pos = man.position.towards(closest_enemy.position,-i)
                while not self.__in_grid(pos) and i < 12:
                    pos = man.position.towards(closest_enemy.position,-i)
                    i += 1
                    j=1
                    while not self.__in_grid(pos) and j < 9:
                        pos = pos.random_on_distance(j)
                        j+=1

                # for st in army:
                if man.shield_percentage < 0.5:
                    if man.health_percentage < 0.4:
                        if not await self.ai.blink(man, pos):
                            self.ai.do(man.move(pos))
                        continue
                    else:
                        d = 5
                else:
                    d = 3

                if pos is not None and man.weapon_cooldown > 0:      # blink/move backwards
                    if not await self.ai.blink(man,pos):
                        self.ai.do(man.move(man.position.towards(pos,d)))
                else:
                    if self.ai._client.query_pathing(man, target) is None or man.distance_to(target) > 7:  # blink forwards and attack
                        print('want to blink!')
                        if not await self.ai.blink(man,target.position.towards(man, 6)):
                            print('no blink')
                            self.ai.do(man.attack(target))
                        else:
                            print('blink2')
                            self.ai.do(man.attack(target,queue=True))
                        # else:
                        #     print('blink1')
                        #     self.ai.do(man.attack(target, queue=True))
                    else:
                        print('just attack')
                        self.ai.do(man.attack(target))

                #  Sentry region  #
            sents = self.ai.army(unit.SENTRY)
            if sents.exists:
                m = -1
                sentry = None
                for se in sents:
                    close = sents.closer_than(7,se).amount
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
                    lambda unit_: unit_.can_attack_ground or unit_.can_attack_air and unit_.distance_to(sentry) <= 9 and
                                  unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids)
                has_energy_amount = sents.filter(lambda x2: x2.energy >= 50).amount
                points = []

                if has_energy_amount > 0 and len(
                        force_fields) < 5 and threats.amount > 4:  # and self.ai.time - self.ai.force_field_time > 1:
                    enemy_army_center = threats.center.towards(sentry,-1)
                    gap = 3
                    points.append(enemy_army_center)
                    points.append(Point2((enemy_army_center.x - gap,enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x + gap,enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x,enemy_army_center.y - gap)))
                    points.append(Point2((enemy_army_center.x,enemy_army_center.y + gap)))
                for se in self.ai.units(unit.SENTRY):
                    abilities = await self.ai.get_available_abilities(se)
                    if threats.amount > 4 and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities \
                            and se.distance_to(threats.closest_to(se)) < 7:
                        self.ai.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                        guardian_shield_on = True
                    if ability.FORCEFIELD_FORCEFIELD in abilities and len(points) > 0:
                        self.ai.do(se(ability.FORCEFIELD_FORCEFIELD,points.pop(0)))
                    else:
                        army_nearby = self.ai.army.closer_than(9,se)
                        if army_nearby.exists:
                            if threats.exists:
                                self.ai.do(se.move(army_nearby.center.towards(threats.closest_to(se),-4)))
        # voidray
        for vr in self.ai.army(unit.VOIDRAY):
            threats = self.ai.enemy_units().filter(lambda z: z.distance_to(vr) < 9 and z.type_id
                not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                # target2 = None
                priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                arm = False
                if priority.exists:

                    armored = priority.filter(lambda z: z.is_armored)
                    if armored.exists:
                        arm = True
                        priority = armored
                    target2 = priority[0]
                else:
                    armored = threats.filter(lambda z: z.is_armored)
                    if armored.exists:
                        arm = True
                        threats = armored
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    if arm:
                        if ability.EFFECT_VOIDRAYPRISMATICALIGNMENT in await self.ai.get_available_abilities(vr)\
                                and target2.distance_to(vr) < 8:
                            self.ai.do(vr(ability.EFFECT_VOIDRAYPRISMATICALIGNMENT))
                    self.ai.do(vr.attack(target2))

        completion_ids = {unit.VOIDRAY, unit.BATTLECRUISER, unit.CARRIER}  # units that returns wrong air dps
        # Carrier
        for cr in self.ai.army({unit.CARRIER,unit.TEMPEST}):
            threats = self.ai.enemy_units().filter(
                lambda z: z.distance_to(cr) < 20 and z.type_id not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                completion = threats.filter(lambda z: z.type_id in completion_ids)
                if completion.exists:
                    priority = completion
                else:
                    priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                    if priority.exists:
                        id0 = priority[0].type_id
                        i = 0
                        while i < len(priority) and priority[i].type_id == id0:
                            i+=1
                        priority = priority[:i]
                if priority:
                    priority = sorted(priority,key=lambda z: z.health + z.shield)
                    target2 = priority[0]
                else:
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    self.ai.do(cr.attack(target2))

        if self.ai.attack:
            for ad in self.ai.army(unit.ADEPT):
                workers = self.ai.enemy_units().filter(lambda x: x.distance_to(ad) < 17 and x.type_id in
                                                                 self.ai.workers_ids)
                threats = self.ai.enemy_units().filter(lambda x: x.distance_to(ad) < 10 and x.type_id not in
                                                       self.ai.workers_ids)
                if workers.amount < 4 or threats.amount > 3:
                    if ability.ADEPTPHASESHIFT_ADEPTPHASESHIFT in await self.ai.get_available_abilities(ad):
                        self.ai.do(ad(ability.ADEPTPHASESHIFT_ADEPTPHASESHIFT, ad.position))
                elif workers.amount > 3:
                    self.ai.do(ad.attack(workers.closest_to(ad)))
            for shadow in self.ai.units(unit.ADEPTPHASESHIFT):
                workers = self.ai.enemy_units().filter(lambda x: x.distance_to(shadow) < 11 and x.type_id in
                                                       self.ai.workers_ids)
                if workers.amount > 3:
                    self.ai.do(shadow.move(workers.closest_to(shadow)))
                # else:
                #     bases = self.ai.enemy_structures().filter(lambda x: x.type_id in self.ai.bases_ids)
                #     if bases.exists:
                #         base = bases.closest_to(shadow).position
                #         workers = self.ai.enemy_units().filter(lambda x: x.distance_to(base) < 11 and x.type_id in
                #                                                          self.ai.workers_ids)
                #         if shadow.distance_to(base) < 4 and (workers.amount < 5 or self.ai.enemy_units().filter(lambda x:
                #             x.distance_to(shadow) < 7 and x.type_id not in self.ai.workers_ids).amount > 4):
                #             self.ai.do(shadow.move(self.ai.enemy_start_locations[0]))
                #             print('going to main base case1')
                #         else:
                #             print('going to near base')
                #             self.ai.do(shadow.move(base))
                else:
                    self.ai.do(shadow.move(self.ai.enemy_start_locations[0]))
                    # print('going to main base case2')

        # zealot
        for zl in self.ai.army(unit.ZEALOT):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(zl) < 9 and not x2.is_flying and
                          x2.type_id not in self.ai.units_to_ignore).sorted(lambda _x: _x.health + _x.shield)
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

        for dt in self.ai.army(unit.DARKTEMPLAR):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(dt) < 9 and not x2.is_flying and
                          x2.type_id not in self.ai.units_to_ignore).sorted(lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(dt)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(dt) > \
                    closest.distance_to(dt) + 3 or not self.ai.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                self.ai.do(dt.attack(target))

    async def personal_defend(self):
        enemy = self.ai.enemy_units()
        if not enemy.exists:
            return
        whole_army = self.ai.army.exclude_type({unit.CARRIER, unit.TEMPEST, unit.VOIDRAY, unit.ZEALOT})
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
                    if self.ai.enemy_race == Race.Protoss:
                        a = targets[0].shield_percentage
                    else:
                        a = 1
                    if targets[0].health_percentage * a == 1:
                        target = priority.closest_to(man)
                    else:
                        target = targets[0]
                else:
                    targets = threats.sorted(lambda x1: x1.health + x1.shield)
                    if self.ai.enemy_race == Race.Protoss:
                        a = targets[0].shield_percentage
                    else:
                        a = 1
                    if targets[0].health_percentage * a == 1:
                        target = closest_enemy
                    else:
                        target = targets[0]
                if target.distance_to(man) > man.distance_to(closest_enemy) + 4:
                    target = closest_enemy
                i=3
                pos = man.position.towards(closest_enemy.position,-i)
                while not self.__in_grid(pos) and i < 12:
                    pos = man.position.towards(closest_enemy.position,-i)
                    i += 1
                    j=1
                    while not self.__in_grid(pos) and j < 9:
                        pos = pos.random_on_distance(j)
                        j+=1

                # for st in army:
                if man.shield_percentage < 0.4:
                    if man.health_percentage < 0.35:
                        self.ai.do(man.move(pos))
                        continue
                    else:
                        d = 4
                else:
                    d = 2

                if pos is not None and man.weapon_cooldown > 0:
                    self.ai.do(man.move(man.position.towards(pos,d)))
                else:
                    if man.distance_to(target) > 6:
                        self.ai.do(man.attack(target))

                #  Sentry region  #
            sents = self.ai.army(unit.SENTRY)
            if sents.exists:
                m = -1
                sentry = None
                for se in sents:
                    close = sents.closer_than(7,se).amount
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
                    lambda unit_: unit_.can_attack_ground or unit_.can_attack_air and unit_.distance_to(sentry) <= 9 and
                                  unit_.type_id not in self.ai.units_to_ignore and unit_.type_id not in self.ai.workers_ids)
                has_energy_amount = sents.filter(lambda x2: x2.energy >= 50).amount
                points = []

                if has_energy_amount > 0 and len(
                        force_fields) < 5 and threats.amount > 4:  # and self.ai.time - self.ai.force_field_time > 1:
                    enemy_army_center = threats.center.towards(sentry,-1)
                    gap = 3
                    points.append(enemy_army_center)
                    points.append(Point2((enemy_army_center.x - gap,enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x + gap,enemy_army_center.y)))
                    points.append(Point2((enemy_army_center.x,enemy_army_center.y - gap)))
                    points.append(Point2((enemy_army_center.x,enemy_army_center.y + gap)))
                for se in self.ai.units(unit.SENTRY):
                    abilities = await self.ai.get_available_abilities(se)
                    if threats.amount > 4 and not guardian_shield_on and ability.GUARDIANSHIELD_GUARDIANSHIELD in abilities \
                            and se.distance_to(threats.closest_to(se)) < 7:
                        self.ai.do(se(ability.GUARDIANSHIELD_GUARDIANSHIELD))
                        guardian_shield_on = True
                    if ability.FORCEFIELD_FORCEFIELD in abilities and len(points) > 0:
                        self.ai.do(se(ability.FORCEFIELD_FORCEFIELD,points.pop(0)))
                    else:
                        army_nearby = self.ai.army.closer_than(9,se)
                        if army_nearby.exists:
                            if threats.exists:
                                self.ai.do(se.move(army_nearby.center.towards(threats.closest_to(se),-4)))
        # voidray
        for vr in self.ai.army(unit.VOIDRAY):
            threats = self.ai.enemy_units().filter(lambda z: z.distance_to(vr) < 9 and z.type_id
                not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                # target2 = None
                priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                arm = False
                if priority.exists:

                    armored = priority.filter(lambda z: z.is_armored)
                    if armored.exists:
                        arm = True
                        priority = armored
                    target2 = priority[0]
                else:
                    armored = threats.filter(lambda z: z.is_armored)
                    if armored.exists:
                        arm = True
                        threats = armored
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    if arm:
                        if ability.EFFECT_VOIDRAYPRISMATICALIGNMENT in await self.ai.get_available_abilities(vr)\
                                and target2.distance_to(vr) < 8:
                            self.ai.do(vr(ability.EFFECT_VOIDRAYPRISMATICALIGNMENT))
                    self.ai.do(vr.attack(target2))

        completion_ids = {unit.VOIDRAY, unit.BATTLECRUISER, unit.CARRIER}  # units that returns wrong air dps
        # Carrier
        for cr in self.ai.army({unit.CARRIER,unit.TEMPEST}):
            threats = self.ai.enemy_units().filter(
                lambda z: z.distance_to(cr) < 20 and z.type_id not in self.ai.units_to_ignore)
            threats.extend(self.ai.enemy_structures().filter(lambda z: z.can_attack_air))
            if threats.exists:
                completion = threats.filter(lambda z: z.type_id in completion_ids)
                if completion.exists:
                    priority = completion
                else:
                    priority = threats.filter(lambda z: z.can_attack_air).sorted(lambda z: z.air_dps, reverse=True)
                    if priority.exists:
                        id0 = priority[0].type_id
                        i = 0
                        while i < len(priority) and priority[i].type_id == id0:
                            i+=1
                        priority = priority[:i]
                if priority:
                    priority = sorted(priority,key=lambda z: z.health + z.shield)
                    target2 = priority[0]
                else:
                    target2 = threats.sorted(lambda z: z.health + z.shield)[0]
                if target2 is not None:
                    self.ai.do(cr.attack(target2))

        # zealot
        for zl in self.ai.army(unit.ZEALOT):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(zl) < 9 and not x2.is_flying and
                          x2.type_id not in self.ai.units_to_ignore).sorted(lambda _x: _x.health + _x.shield)
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

        for dt in self.ai.army(unit.DARKTEMPLAR):
            threats = self.ai.enemy_units().filter(lambda x2: x2.distance_to(dt) < 9 and not x2.is_flying and
                          x2.type_id not in self.ai.units_to_ignore).sorted(lambda _x: _x.health + _x.shield)
            if threats.exists:
                closest = threats.closest_to(dt)
                if threats[0].health_percentage * threats[0].shield_percentage == 1 or threats[0].distance_to(dt) > \
                    closest.distance_to(dt) + 3 or not self.ai.in_pathing_grid(threats[0]):
                    target = closest
                else:
                    target = threats[0]
                self.ai.do(dt.attack(target))
