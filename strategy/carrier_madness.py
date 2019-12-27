from builders.gate_builder import GateBuilder
from builders.stargate_builder import StargateBuilder
from builders.assimilator_builder import AssimilatorBuilder
from builders.forge_builder import ForgeBuilder
from builders.twilight_builder import TwilightBuilder
from builders.pylon_builder import PylonBuilder
from builders.cybernetics_builder import CyberneticsBuilder
from builders.expanding import Expanding


class CarrierMadness:
    def __init__(self, ai):
        self.ai = ai

    async def gate_build(self):
        await GateBuilder.carrier_madness(self.ai)

    async def stargate_build(self):
        await StargateBuilder.carrier_madness(self.ai)

    def assimilator_build(self):
        AssimilatorBuilder.max_vespene(self.ai)

    async def forge_build(self):
        await ForgeBuilder.none(self.ai)

    async def twilight_build(self):
        await TwilightBuilder.zealots(self.ai)

    async def pylon_first_build(self):
        await PylonBuilder.first_wall(self.ai)

    async def pylon_next_build(self):
        await PylonBuilder.next_standard(self.ai)

    async def cybernetics_build(self):
        await CyberneticsBuilder.standard(self.ai)

    async def expand(self):
        await Expanding.standard(self.ai)