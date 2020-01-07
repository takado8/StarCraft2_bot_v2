from strategy.manager import Strategy


class CarrierMadness(Strategy):
    def __init__(self, ai):
        self.type = 'macro'
        super().__init__(ai)

    # =======================================================  Builders

    async def gate_build(self):
        await self._gate_builder.one_standard()

    async def stargate_build(self):
        await self._stargate_builder.carrier_madness()

    def assimilator_build(self):
        self._assimilator_builder.max_vespene()

    async def forge_build(self):
        await self._forge_builder.none()

    async def twilight_build(self):
        await self._twilight_builder.none()

    async def pylon_first_build(self):
        await self._pylon_builder.none()

    async def pylon_next_build(self):
        await self._pylon_builder.first_and_next_standard()

    async def proxy(self):
        pass

    async def cybernetics_build(self):
        await self._cybernetics_builder.standard()

    async def robotics_build(self):
        await self._robotics_builder.none()

    async def robotics_bay_build(self):
        await self._robotics_bay_builder.none()

    async def expand(self):
        await self._expander.standard()

    # =======================================================  Upgraders

    def cybernetics_upgrades(self):
        self._cybernetics_upgrader.air_dmg()

    def forge_upgrades(self):
        self._forge_upgrader.none()

    async def twilight_upgrades(self):
        await self._twilight_upgrader.none()

    # =======================================================  Trainers

    def nexus_train(self):
        self._nexus_trainer.probes_standard()

    def gate_train(self):
        self._gate_trainer.zealots()

    def stargate_train(self):
        self._stargate_trainer.carriers()

    def robotics_train(self):
        self._robotics_trainer.none()

    async def warpgate_train(self):
        await self._warpgate_trainer.stargate_priority()

    # =======================================================  Army

    async def micro(self):
        await self._micro.personal()

    async def movements(self):
        await self._movements.attack_formation()
