from strategy.manager import Strategy


class Dt(Strategy):
    def __init__(self, ai):
        super().__init__(ai)
        self.type = 'rush'
        self.name = 'dt'


    # =======================================================  Builders

    async def gate_build(self):
        await self._gate_builder.three_rush()

    async def stargate_build(self):
        pass

    def assimilator_build(self):
        self._assimilator_builder.more_vespene()

    async def forge_build(self):
        await self._forge_builder.none()

    async def twilight_build(self):
        await self._twilight_builder.early()

    async def pylon_first_build(self):
        await self._pylon_builder.none()

    async def pylon_next_build(self):
        await self._pylon_builder.first_and_next_standard()

    async def proxy(self):
        await self._pylon_builder.proxy()
        await self._gate_builder.proxy()

    async def templar_archives_build(self):
        await self._templar_archives_builder.none()

    async def dark_shrine_build(self):
        await self._dark_shrine_builder.standard()

    async def cybernetics_build(self):
        await self._cybernetics_builder.standard()

    async def robotics_bay_build(self):
        await self._robotics_bay_builder.none()

    async def robotics_build(self):
        await self._robotics_builder.none()

    async def expand(self):
        await self._expander.two_bases()

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
        self._gate_trainer.zealots()

    def stargate_train(self):
        self._stargate_trainer.none()

    def robotics_train(self):
        self._robotics_trainer.none()

    async def warpgate_train(self):
        await self._warpgate_trainer.dt()

    async def templar_archives_upgrades(self):
        pass

    async def fleet_beacon_upgrades(self):
        pass

    # =======================================================  Army

    async def micro(self):
        await self._micro.personal_new()

    async def movements(self):
        await self._movements.attack_formation_brand_new_newest_thee_most_new_shit_in_whole_wide_world()

    # ======================================================= Conditions

    def attack_condition(self):
        return self._condition_attack.dt()

    def counter_attack_condition(self):
        return self._condition_attack.counter_attack()

    def retreat_condition(self):
        return self._condition_retreat.dt()

    async def transformation(self):
        await self._condition_transform.adept_proxy()

    # ======================================================== Buffs

    async def chronoboost(self):
        await self._chronobooster.standard()