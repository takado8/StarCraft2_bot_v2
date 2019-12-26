from builders.gate_builder import GateBuilder
from builders.stargate_builder import StargateBuilder
from builders.assimilator_builder import AssimilatorBuilder

from sc2.ids.ability_id import AbilityId as ability
from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.upgrade_id import UpgradeId as upgrade



class CarrierMadness:
    def __init__(self, ai):
        self.ai = ai

    async def gate_build(self):
        await GateBuilder.carrier_madness(self.ai)

    async def stargate_build(self):
        await StargateBuilder.carrier_madness(self.ai)

    async def assimilators_build(self):
        await AssimilatorBuilder.max_vespene(self.ai)


    def cybernetics_core_upgrades(self):
        cyber = self.ai.structures(unit.CYBERNETICSCORE).ready.idle
        if cyber.amount > 0:
            if upgrade.WARPGATERESEARCH not in self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                    upgrade.WARPGATERESEARCH) and self.ai.can_afford(upgrade.WARPGATERESEARCH):
                self.ai.do(cyber.random.research(upgrade.WARPGATERESEARCH))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL1 not in self.ai.state.upgrades and self.ai.can_afford(upgrade.PROTOSSAIRWEAPONSLEVEL1) and\
                not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL1):
                self.ai.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL1))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL2 not in self.ai.state.upgrades and self.ai.can_afford(upgrade.PROTOSSAIRWEAPONSLEVEL2) and\
                not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL2):
                self.ai.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL2))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL3 not in self.ai.state.upgrades and self.ai.can_afford(upgrade.PROTOSSAIRWEAPONSLEVEL3) and\
                not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL3):
                self.ai.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL3))

    async def twilight_council_build(self):
        # 220
        if self.ai.structures(unit.CYBERNETICSCORE).ready.exists and self.ai.time > 360 and self.ai.build_type == 'macro':
            if not self.ai.structures(unit.TWILIGHTCOUNCIL).exists \
                    and not self.ai.already_pending(unit.TWILIGHTCOUNCIL) and self.ai.can_afford(unit.TWILIGHTCOUNCIL):
                pylon = self.ai.get_proper_pylon()
                await self.ai.build(unit.TWILIGHTCOUNCIL,near=pylon.position,
                                 random_alternative=True,placement_step=2)
            # elif self.units(unit.TWILIGHTCOUNCIL).ready.exists and not self.units(unit.TEMPLARARCHIVE).exists and \
            #         self.can_afford(unit.TEMPLARARCHIVE) and not self.already_pending(unit.TEMPLARARCHIVE):
            #     await self.build(unit.TEMPLARARCHIVE,near=self.get_proper_pylon())
            # elif self.units(unit.TEMPLARARCHIVE).ready.exists:
            #     temparch = self.units(unit.TEMPLARARCHIVE).ready.random
            #     abilities = await self.get_available_abilities(temparch)
            #     if ability.RESEARCH_PSISTORM in abilities:
            #         await self.do(temparch(ability.RESEARCH_PSISTORM))
            if self.ai.structures(unit.TWILIGHTCOUNCIL).ready.exists:
                tc = self.ai.structures(unit.TWILIGHTCOUNCIL).ready.idle
                if tc.exists:
                    tc = tc.random
                else:
                    return
                abilities = await self.ai.get_available_abilities(tc)
                # if ability.RESEARCH_ADEPTRESONATINGGLAIVES in abilities:
                #     await self.do(tc(ability.RESEARCH_ADEPTRESONATINGGLAIVES))
                if ability.RESEARCH_CHARGE in abilities:
                    self.ai.do(tc(ability.RESEARCH_CHARGE))
                # if ability.RESEARCH_BLINK in abilities:
                #     self.do(tc(ability.RESEARCH_BLINK))
