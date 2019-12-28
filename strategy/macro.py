from strategy.manager import Strategy


class Macro(Strategy):
    def __init__(self, ai):
        super().__init__(ai)

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
        await self._twilight_upgrader.both()

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