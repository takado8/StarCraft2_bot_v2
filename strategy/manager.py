from builders import *
from bot.chronobooster import *
from bot.upgraders import *
from bot.trainers import *
from bot.conditions import *
from army.micro import *
from army.movements import *


class Strategy:
    def __init__(self, ai):
        self.ai = ai
        # type
        self.type = 'strategy type'
        self.name = 'strategy name'
        # builders
        self._gate_builder = GateBuilder(ai)
        self._stargate_builder = StargateBuilder(ai)
        self._forge_builder = ForgeBuilder(ai)
        self._twilight_builder = TwilightBuilder(ai)
        self._templar_archives_builder = TemplarArchivesBuilder(ai)
        self._dark_shrine_builder = DarkShrineBuilder(ai)
        self._pylon_builder = PylonBuilder(ai)
        self._cybernetics_builder = CyberneticsBuilder(ai)
        self._robotics_builder = RoboticsBuilder(ai)
        self._robotics_bay_builder = RoboticsBayBuilder(ai)
        self._assimilator_builder = AssimilatorBuilder(ai)
        self._cannon_builder = CannonBuilder(ai)
        self._expander = Expander(ai)
        # upgraders
        self._cybernetics_upgrader = CyberneticsUpgrader(ai)
        self._forge_upgrader = ForgeUpgrader(ai)
        self._twilight_upgrader = TwilightUpgrader(ai)
        self._templar_archives_upgrader = TemplarArchiveUpgrader(ai)
        self._fleet_beacon_upgrader = FleetBeaconUpgrader(ai)
        # trainers
        self._nexus_trainer = NexusTrainer(ai)
        self._gate_trainer = GateTrainer(ai)
        self._warpgate_trainer = WarpgateTrainer(ai)
        self._stargate_trainer = StargateTrainer(ai)
        self._robotics_trainer = RoboticsTrainer(ai)
        # army
        self._micro = Micro(ai)
        self._movements = Movements(ai)
        # Conditions
        self._condition_attack = ConditionAttack(ai)
        self._condition_retreat = ConditionRetreat(ai)
        self._condition_transform = ConditionTransform(ai)
        # chronoboost
        self._chronobooster = Chronobooster(ai)

    # =======================================================  Builders

    async def gate_build(self):
        raise NotImplementedError

    async def stargate_build(self):
        print('stargate_build not implemented')

    def assimilator_build(self):
        raise NotImplementedError

    async def forge_build(self):
        print('forge_build not implemented')

    async def twilight_build(self):
        print('twilight_build not implemented')

    async def templar_archives_build(self):
        print('templar_archives_build not implemented')

    async def dark_shrine_build(self):
        pass

    async def pylon_first_build(self):
        print('pylon_first_build not implemented')

    async def pylon_next_build(self):
        raise NotImplementedError

    async def proxy(self):
        print('proxy not implemented')

    async def cybernetics_build(self):
        print('cybernetics_build not implemented')

    async def robotics_build(self):
        print('robotics_build not implemented')

    async def robotics_bay_build(self):
        print('robotics_bay_build not implemented')

    async def cannons_build(self):
        pass

    async def expand(self):
        print('expand not implemented')

    # =======================================================  Upgraders

    def cybernetics_upgrades(self):
        print('cybernetics upg not implemented')

    def forge_upgrades(self):
        print('forge upg not implemented')

    async def twilight_upgrades(self):
        print('twilight upg not implemented')

    async def templar_archives_upgrades(self):
        print('templar arch upg not implemented')

    async def fleet_beacon_upgrades(self):
        print('fleet beacon upg not implemented')

    # =======================================================  Trainers

    def nexus_train(self):
        raise NotImplementedError

    def gate_train(self):
        raise NotImplementedError

    def stargate_train(self):
        print('stargate train not implemented')

    def robotics_train(self):
        print('robotics train not implemented')

    async def warpgate_train(self):
        raise NotImplementedError

    # =======================================================  Army

    async def micro(self):
        raise NotImplementedError

    async def movements(self):
        raise NotImplementedError

# ======================================================= Conditions

    def attack_condition(self):
        raise NotImplementedError

    def counter_attack_condition(self):
        raise NotImplementedError

    def retreat_condition(self):
        raise NotImplementedError

    async def transformation(self):
        pass

    async def chronoboost(self):
        # raise NotImplementedError
        pass