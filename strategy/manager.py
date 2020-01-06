from builders.gate_builder import GateBuilder
from builders.stargate_builder import StargateBuilder
from builders.assimilator_builder import AssimilatorBuilder
from builders.forge_builder import ForgeBuilder
from builders.twilight_builder import TwilightBuilder
from builders.pylon_builder import PylonBuilder
from builders.cybernetics_builder import CyberneticsBuilder
from builders.robotics_builder import RoboticsBuilder
from builders.robotics_bay_builder import RoboticsBayBuilder
from builders.expander import Expander
from upgraders import *
from trainers import *
from army.micro import *
from army.movements import *


class Strategy:
    def __init__(self, ai):
        self.ai = ai
        # type
        self.type = 'strategy type'
        # builders
        self._gate_builder = GateBuilder(ai)
        self._stargate_builder = StargateBuilder(ai)
        self._forge_builder = ForgeBuilder(ai)
        self._twilight_builder = TwilightBuilder(ai)
        self._pylon_builder = PylonBuilder(ai)
        self._cybernetics_builder = CyberneticsBuilder(ai)
        self._robotics_builder = RoboticsBuilder(ai)
        self._robotics_bay_builder = RoboticsBayBuilder(ai)
        self._assimilator_builder = AssimilatorBuilder(ai)
        self._expander = Expander(ai)
        # upgraders
        self._cybernetics_upgrader = CyberneticsUpgrader(ai)
        self._forge_upgrader = ForgeUpgrader(ai)
        self._twilight_upgrader = TwilightUpgrader(ai)
        # trainers
        self._nexus_trainer = NexusTrainer(ai)
        self._gate_trainer = GateTrainer(ai)
        self._warpgate_trainer = WarpgateTrainer(ai)
        self._stargate_trainer = StargateTrainer(ai)
        self._robotics_trainer = RoboticsTrainer(ai)
        # army
        self._micro = Micro(ai)
        self._movements = Movements(ai)

    # =======================================================  Builders

    async def gate_build(self):
        print('gate_build not implemented')

    async def stargate_build(self):
        print('stargate_build not implemented')

    def assimilator_build(self):
        print('assimilator_build not implemented')

    async def forge_build(self):
        print('forge_build not implemented')

    async def twilight_build(self):
        print('twilight_build not implemented')

    async def pylon_first_build(self):
        print('pylon_first_build not implemented')

    async def pylon_next_build(self):
        print('pylon_next_build not implemented')

    async def proxy(self):
        print('proxy not implemented')

    async def cybernetics_build(self):
        print('cybernetics_build not implemented')

    async def robotics_build(self):
        print('robotics_build not implemented')

    async def robotics_bay_build(self):
        print('robotics_bay_build not implemented')

    async def expand(self):
        print('expand not implemented')

    # =======================================================  Upgraders

    def cybernetics_upgrades(self):
        print('cybernetics upg not implemented')

    def forge_upgrades(self):
        print('forge upg not implemented')

    async def twilight_upgrades(self):
        print('twilight upg not implemented')

    # =======================================================  Trainers

    def nexus_train(self):
        print('nexus train not implemented')

    def gate_train(self):
        print('gate train not implemented')

    def stargate_train(self):
        print('stargate train not implemented')

    def robotics_train(self):
        print('robotics train not implemented')

    async def warpgate_train(self):
        print('warp train not implemented')

    # =======================================================  Army

    async def micro(self):
        print('micro not implemented')

    async def movements(self):
        print('movements not implemented')