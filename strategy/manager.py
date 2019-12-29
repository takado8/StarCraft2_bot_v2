from builders.gate_builder import GateBuilder
from builders.stargate_builder import StargateBuilder
from builders.assimilator_builder import AssimilatorBuilder
from builders.forge_builder import ForgeBuilder
from builders.twilight_builder import TwilightBuilder
from builders.pylon_builder import PylonBuilder
from builders.cybernetics_builder import CyberneticsBuilder
from builders.robotics_builder import RoboticsBuilder
from builders.expander import Expander
from upgraders import *
from trainers import *
from army.micro import *
from army.movements import *


class Strategy:
    def __init__(self, ai):
        self.ai = ai
        # builders
        self._gate_builder = GateBuilder(ai)
        self._stargate_builder = StargateBuilder(ai)
        self._forge_builder = ForgeBuilder(ai)
        self._twilight_builder = TwilightBuilder(ai)
        self._pylon_builder = PylonBuilder(ai)
        self._cybernetics_builder = CyberneticsBuilder(ai)
        self._robotics_builder = RoboticsBuilder(ai)
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
        pass

    async def stargate_build(self):
        pass

    def assimilator_build(self):
        pass

    async def forge_build(self):
        pass

    async def twilight_build(self):
        pass

    async def pylon_first_build(self):
        pass

    async def pylon_next_build(self):
        pass

    async def proxy(self):
        pass

    async def cybernetics_build(self):
        pass

    async def robotics_build(self):
        pass

    async def expand(self):
        pass

    # =======================================================  Upgraders

    def cybernetics_upgrades(self):
        pass

    def forge_upgrades(self):
        pass

    async def twilight_upgrades(self):
        pass

    # =======================================================  Trainers

    def nexus_train(self):
        pass

    def gate_train(self):
        pass

    def stargate_train(self):
        pass

    def robotics_train(self):
        pass

    async def warpgate_train(self):
        pass

    # =======================================================  Army

    async def micro(self):
        pass

    async def movements(self):
        pass