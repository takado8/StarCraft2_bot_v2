from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.ability_id import AbilityId as ability


class NexusTrainer:
    def __init__(self, ai):
        self.ai = ai

    def probes_standard(self):
        workers = self.ai.workers.amount
        nex = self.ai.structures(unit.NEXUS).ready.amount
        if not self.ai.structures(unit.PYLON).exists and workers == 14:
            return
        if workers < 20 * nex and workers < 55:
            for nexus in self.ai.structures(unit.NEXUS).ready:
                if nexus.is_idle and self.ai.can_afford(unit.PROBE):
                    self.ai.do(nexus.train(unit.PROBE))
        elif 54 < workers < 60:
            if self.ai.can_afford(unit.PROBE) and not self.ai.already_pending(unit.PROBE):
                if self.ai.structures(unit.NEXUS).idle.amount < nex:
                    return
                nexus = self.ai.structures(unit.NEXUS).ready.idle.random
                self.ai.do(nexus.train(unit.PROBE))


class GateTrainer:
    def __init__(self, ai):
        self.ai = ai

    def zealots(self):
        if self.ai.minerals > 250 and self.ai.supply_left > 1 and self.ai.units(unit.ZEALOT).amount < 20:
            gateway = self.ai.structures(unit.GATEWAY).ready.idle
            if gateway.exists:
                gateway = gateway.random
                self.ai.do(gateway.train(unit.ZEALOT))

    def stalkers(self):
        if self.ai.structures(unit.CYBERNETICSCORE).ready.exists:
            gateways = self.ai.structures(unit.GATEWAY).ready.idle
            for gateway in gateways:
                if self.ai.can_afford(unit.STALKER):
                    self.ai.do(gateway.train(unit.STALKER))

    def standard(self):
        gateway = self.ai.structures(unit.GATEWAY).ready
        if self.ai.minerals < 100 or not gateway.exists or not gateway.idle.exists:
            return

        if self.ai.can_afford(unit.STALKER) and self.ai.structures(unit.CYBERNETICSCORE).ready.exists:
            u = unit.STALKER
        elif self.ai.can_afford(unit.SENTRY) and self.ai.structures(unit.CYBERNETICSCORE).ready.exists and self.ai.units(
                unit.SENTRY).amount < 1:
            u = unit.SENTRY
        # elif self.can_afford(unit.ADEPT) and self.structures(unit.CYBERNETICSCORE).ready.exists and \
        #         self.army(unit.ADEPT).amount < 2:
        #     u = unit.ADEPT
        elif self.ai.supply_left > 1 and self.ai.minerals > 150 and self.ai.units(unit.ZEALOT).amount < 3:
            u = unit.ZEALOT
        else:
            return
        gateway = gateway.ready.idle.random
        self.ai.do(gateway.train(u))


class StargateTrainer:
    def __init__(self, ai):
        self.ai = ai

    def none(self):
        pass

    def carriers(self):
        if self.ai.structures(unit.STARGATE).ready.idle.exists:
            if self.ai.structures(unit.FLEETBEACON).ready.exists:
                if self.ai.can_afford(unit.CARRIER):
                    self.ai.train(unit_type=unit.CARRIER)
                elif self.ai.can_afford(unit.TEMPEST) and self.ai.army(unit.TEMPEST).amount < 4 and\
                        self.ai.army(unit.TEMPEST).amount * 2 < self.ai.army(unit.CARRIER).amount:
                    self.ai.train(unit.TEMPEST)
                elif self.ai.can_afford(unit.VOIDRAY) and self.ai.army(unit.VOIDRAY).amount < 7 and \
                        self.ai.army(unit.CARRIER).amount > 5:
                    self.ai.train(unit.VOIDRAY)
            elif self.ai.can_afford(unit.VOIDRAY):
                self.ai.train(unit.VOIDRAY)

    def voidray(self):
        if self.ai.structures(unit.STARGATE).ready.idle.exists:
            if self.ai.can_afford(unit.VOIDRAY):
                self.ai.train(unit.VOIDRAY)


class WarpgateTrainer:
    def __init__(self, ai):
        self.ai = ai

    async def stalkers(self):
        warpgates = self.ai.structures(unit.WARPGATE).ready.idle
        if warpgates.exists:
            if self.ai.attack:
                prisms = self.ai.units(unit.WARPPRISMPHASING)
                if prisms.exists:
                    pos = prisms.furthest_to(self.ai.start_location).position
                else:
                    furthest_pylon = self.ai.structures(unit.PYLON).ready.furthest_to(self.ai.start_location.position)
                    pos = furthest_pylon.position
            else:
                pos = self.ai.structures(unit.PYLON).ready.closer_than(35,self.ai.start_location).furthest_to(
                    self.ai.start_location).position
            placement = None
            i = 0
            while placement is None:
                i += 1
                placement = await self.ai.find_placement(ability.TRAINWARP_ADEPT, near=pos.random_on_distance(5),
                                                      max_distance=5, placement_step=2, random_alternative=False)
                if i > 5:
                    print("can't find position for warpin.")
                    return
            for warpgate in warpgates:
                abilities = await self.ai.get_available_abilities(warpgate)
                if ability.WARPGATETRAIN_ZEALOT in abilities:
                    if self.ai.can_afford(unit.STALKER):
                        self.ai.do(warpgate.warp_in(unit.STALKER, placement))


    async def standard(self):
        if not self.ai.attack:
            if (self.ai.structures(unit.ROBOTICSFACILITY).ready.idle.exists and
                    self.ai.army(unit.IMMORTAL).amount < 5) or self.ai.forge_upg_priority() or not self.ai.structures(unit.WARPGATE).exists:
                return

        if self.ai.attack:
            prisms = self.ai.units(unit.WARPPRISMPHASING)
            if prisms.exists:
                pos = prisms.furthest_to(self.ai.start_location).position
            else:
                furthest_pylon = self.ai.structures(unit.PYLON).ready.furthest_to(self.ai.start_location.position)
                pos = furthest_pylon.position
        else:
            pos = self.ai.structures(unit.PYLON).ready.closer_than(35,self.ai.start_location).furthest_to(
                self.ai.start_location).position
        placement = None
        i = 0
        while placement is None:
            i += 1
            placement = await self.ai.find_placement(ability.TRAINWARP_ADEPT, near=pos.random_on_distance(5),
                                                  max_distance=5, placement_step=2, random_alternative=False)
            if i > 5:
                print("can't find position for warpin.")
                return
        archons = self.ai.army(unit.ARCHON).amount
        if archons == 0:
            archons = 1
        amount = 4 * archons
        for warpgate in self.ai.structures(unit.WARPGATE).ready:
            abilities = await self.ai.get_available_abilities(warpgate)
            if ability.WARPGATETRAIN_ZEALOT in abilities:
                if self.ai.can_afford(unit.HIGHTEMPLAR) and self.ai.supply_left > 1 and self.ai.army(
                        unit.ARCHON).amount < 5 and self.ai.structures(unit.TEMPLARARCHIVE).ready.exists:
                    self.ai.do(warpgate.warp_in(unit.HIGHTEMPLAR,placement))
                elif self.ai.can_afford(unit.SENTRY) and self.ai.units(unit.STALKER).amount > 7 and \
                        self.ai.structures(unit.CYBERNETICSCORE).ready.exists and self.ai.units(unit.SENTRY).amount < 5:
                    self.ai.do(warpgate.warp_in(unit.SENTRY,placement))
                elif self.ai.can_afford(unit.STALKER) and self.ai.supply_left > 1 and self.ai.army(unit.STALKER).amount < amount:
                    self.ai.do(warpgate.warp_in(unit.STALKER, placement))
                # elif self.ai.minerals > 150 and self.ai.supply_left > 1 and \
                #         self.ai.structures(unit.CYBERNETICSCORE).ready.exists and self.ai.units(unit.ADEPT).amount < 7:
                #     self.ai.do(warpgate.warp_in(unit.ADEPT, placement))
                elif self.ai.minerals > 150 and \
                        self.ai.supply_left > 1 and self.ai.units(unit.ZEALOT).amount < 30:
                    self.ai.do(warpgate.warp_in(unit.ZEALOT, placement))

    async def stargate_priority(self):
        if self.ai.structures(unit.FLEETBEACON).ready.exists and self.ai.structures(unit.STARGATE).ready.idle.exists \
                or self.ai.forge_upg_priority() or not self.ai.structures(unit.WARPGATE).exists:
            return
        if self.ai.attack:
            prisms = self.ai.units(unit.WARPPRISMPHASING)
            if prisms.exists:
                pos = prisms.furthest_to(self.ai.start_location).position
            else:
                furthest_pylon = self.ai.structures(unit.PYLON).ready.furthest_to(self.ai.start_location.position)
                pos = furthest_pylon.position
        else:
            pos = self.ai.structures(unit.PYLON).ready.closer_than(35,self.ai.start_location).furthest_to(
                self.ai.start_location).position
        placement = None
        i = 0
        while placement is None:
            i += 1
            placement = await self.ai.find_placement(ability.TRAINWARP_ADEPT, near=pos.random_on_distance(5),
                                                  max_distance=5, placement_step=2, random_alternative=False)
            if i > 5:
                print("can't find position for warpin.")
                return
        for warpgate in self.ai.structures(unit.WARPGATE).ready:
            abilities = await self.ai.get_available_abilities(warpgate)
            if ability.WARPGATETRAIN_ZEALOT in abilities:
                if self.ai.can_afford(unit.SENTRY) and self.ai.units(unit.STALKER).amount > 7 and \
                        self.ai.structures(unit.CYBERNETICSCORE).ready.exists and self.ai.units(unit.SENTRY).amount < 3:
                    self.ai.do(warpgate.warp_in(unit.SENTRY,placement))
                elif self.ai.can_afford(unit.STALKER) and self.ai.supply_left > 1 and self.ai.army(unit.STALKER).amount < 30:
                    self.ai.do(warpgate.warp_in(unit.STALKER, placement))
                elif self.ai.minerals > 150 and self.ai.supply_left > 1 and \
                        self.ai.structures(unit.CYBERNETICSCORE).ready.exists and self.ai.units(unit.ADEPT).amount < 12:
                    self.ai.do(warpgate.warp_in(unit.ADEPT, placement))
                elif self.ai.minerals > 130 and self.ai.vespene < 50 and \
                        self.ai.supply_left > 1 and self.ai.units(unit.ZEALOT).amount < 12:
                    self.ai.do(warpgate.warp_in(unit.ZEALOT, placement))


class RoboticsTrainer:
    def __init__(self, ai):
        self.ai = ai

    def none(self):
        pass

    def standard(self):
        robotics = self.ai.structures(unit.ROBOTICSFACILITY).ready.idle
        if robotics.exists:
            if self.ai.structures(unit.ROBOTICSBAY).ready.exists \
                    and self.ai.units(unit.COLOSSUS).amount < 3:
                immortals_amm = 3
            else:
                immortals_amm = 10
            if self.ai.units(unit.OBSERVER).amount + self.ai.units(unit.OBSERVERSIEGEMODE).amount < 1 and \
                self.ai.can_afford(unit.OBSERVER):
                for factory in robotics:
                    self.ai.do(factory.train(unit.OBSERVER))
                    break
            elif self.ai.attack and self.ai.units(unit.WARPPRISMPHASING).amount + self.ai.units(unit.WARPPRISM).amount < 1 \
                    and self.ai.can_afford(unit.WARPPRISM) and not self.ai.already_pending(
                unit.WARPPRISM) and self.ai.supply_left > 2:
                for factory in self.ai.structures(unit.ROBOTICSFACILITY).ready.idle:
                    self.ai.do(factory.train(unit.WARPPRISM))
                    break
            elif self.ai.can_afford(unit.COLOSSUS) and self.ai.supply_left > 5 and self.ai.structures(
                    unit.ROBOTICSBAY).ready.exists \
                    and self.ai.units(unit.COLOSSUS).amount < 3:
                for factory in self.ai.structures(unit.ROBOTICSFACILITY).ready.idle:
                    self.ai.do(factory.train(unit.COLOSSUS))
            elif self.ai.can_afford(unit.IMMORTAL) and self.ai.supply_left > 3 and self.ai.structures(
                    unit.ROBOTICSFACILITY).ready.exists \
                    and self.ai.units(unit.IMMORTAL).amount < immortals_amm:
                for factory in self.ai.structures(unit.ROBOTICSFACILITY).ready.idle:
                    self.ai.do(factory.train(unit.IMMORTAL))