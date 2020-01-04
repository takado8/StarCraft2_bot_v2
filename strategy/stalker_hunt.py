from strategy.manager import Strategy


class StalkerHunt(Strategy):
    def __init__(self, ai):
        super().__init__(ai)
        self.type = 'rush'

    # =======================================================  Builders

    async def gate_build(self):
        await self._gate_builder.three_standard()

    async def stargate_build(self):
        await self._stargate_builder.none()

    def assimilator_build(self):
        self._assimilator_builder.standard()

    async def forge_build(self):
        await self._forge_builder.none()

    async def twilight_build(self):
        await self._twilight_builder.none()

    async def pylon_first_build(self):
        await self._pylon_builder.none()

    async def pylon_next_build(self):
        await self._pylon_builder.first_and_next_standard()

    async def proxy(self):
        await self._pylon_builder.proxy()

    async def cybernetics_build(self):
        await self._cybernetics_builder.standard()

    async def robotics_build(self):
        await self._robotics_builder.none()

    async def expand(self):
        await self._expander.none()

    # =======================================================  Upgraders

    def cybernetics_upgrades(self):
        self._cybernetics_upgrader.standard()

    def forge_upgrades(self):
        self._forge_upgrader.none()

    async def twilight_upgrades(self):
        await self._twilight_upgrader.none()

    # =======================================================  Trainers

    def nexus_train(self):
        self._nexus_trainer.probes_standard()

    def gate_train(self):
        self._gate_trainer.stalkers()

    def stargate_train(self):
        self._stargate_trainer.none()

    def robotics_train(self):
        self._robotics_trainer.none()

    async def warpgate_train(self):
        await self._warpgate_trainer.stalkers()

    # =======================================================  Army

    async def micro(self):
        await self._micro.standard()

    async def movements(self):
        await self._movements.attack_formation()