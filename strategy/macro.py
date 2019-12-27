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


class Macro:
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

    # =======================================================  Builders

    async def gate_build(self):
        await self._gate_builder.macro()

    def assimilator_build(self):
        self._assimilator_builder.standard()

    async def stargate_build(self):
        await self._stargate_builder.none()

    async def forge_build(self):
        await self._forge_builder.double()

    async def twilight_build(self):
        await self._twilight_builder.standard()

    async def pylon_first_build(self):
        await self._pylon_builder.first_in_lower_wall()

    async def pylon_next_build(self):
        await self._pylon_builder.next_standard()

    async def cybernetics_build(self):
        await self._cybernetics_builder.lower_wall()

    async def robotics_build(self):
        await self._robotics_builder.macro()

    async def expand(self):
        await self._expander.standard()

    # =======================================================  Upgraders

    def cybernetics_upgrades(self):
        self._cybernetics_upgrader.standard()

    def forge_upgrades(self):
        self._forge_upgrader.standard()

    async def twilight_upgrades(self):
        await self._twilight_upgrader.blink()

    # =======================================================  Trainers

    def nexus_train(self):
        self._nexus_trainer.probes_standard()

    def gate_train(self):
        self._gate_trainer.standard()

    def stargate_train(self):
        self._stargate_trainer.none()

    def robotics_train(self):
        self._robotics_trainer.standard()

    async def warpgate_train(self):
        await self._warpgate_trainer.standard()