from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.upgrade_id import UpgradeId as upgrade
from sc2.ids.ability_id import AbilityId as ability


class ForgeUpgrader:
    def __init__(self, ai):
        self.ai = ai

    def none(self):
        pass

    def standard(self):
        for forge in self.ai.structures(unit.FORGE).ready.idle:

            if upgrade.PROTOSSGROUNDWEAPONSLEVEL1 not in self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                    upgrade.PROTOSSGROUNDWEAPONSLEVEL1) and self.ai.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL1):
                self.ai.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL1))
            elif upgrade.PROTOSSGROUNDWEAPONSLEVEL2 not in self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                    upgrade.PROTOSSGROUNDWEAPONSLEVEL2) and self.ai.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL2):
                self.ai.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL2))
            elif self.ai.already_pending_upgrade(upgrade.PROTOSSGROUNDWEAPONSLEVEL2) or\
                upgrade.PROTOSSGROUNDWEAPONSLEVEL2 in self.ai.state.upgrades:
                if upgrade.PROTOSSGROUNDWEAPONSLEVEL2 in \
                        self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDWEAPONSLEVEL3) and self.ai.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL3):
                    self.ai.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL3))
                elif upgrade.PROTOSSGROUNDARMORSLEVEL1 not in self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDARMORSLEVEL1) and self.ai.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL1):
                    self.ai.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL1))
                elif upgrade.PROTOSSSHIELDSLEVEL1 not in self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                        upgrade.PROTOSSSHIELDSLEVEL1) and self.ai.can_afford(upgrade.PROTOSSSHIELDSLEVEL1):
                    self.ai.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL1))
                elif upgrade.PROTOSSGROUNDARMORSLEVEL2 not in self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDARMORSLEVEL2) and self.ai.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL2):
                    self.ai.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL2))
                elif upgrade.PROTOSSGROUNDARMORSLEVEL2 in \
                        self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDARMORSLEVEL3) and self.ai.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL3):
                    self.ai.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL3))
                elif upgrade.PROTOSSSHIELDSLEVEL2 not in self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                        upgrade.PROTOSSSHIELDSLEVEL2) and self.ai.can_afford(upgrade.PROTOSSSHIELDSLEVEL2) and \
                        upgrade.PROTOSSSHIELDSLEVEL1 in self.ai.state.upgrades and self.ai.structures(
                        unit.TWILIGHTCOUNCIL).ready.exists:
                    self.ai.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL2))
                elif upgrade.PROTOSSSHIELDSLEVEL3 not in self.ai.state.upgrades and not self.ai.already_pending_upgrade(
                        upgrade.PROTOSSSHIELDSLEVEL3) and self.ai.can_afford(upgrade.PROTOSSSHIELDSLEVEL3) and \
                        upgrade.PROTOSSSHIELDSLEVEL2 in self.ai.state.upgrades:
                    self.ai.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL3))


class CyberneticsUpgrader:
    def __init__(self, ai):
        self.ai = ai

    def standard(self):
        cyber = self.ai.structures(unit.CYBERNETICSCORE).ready.idle
        if cyber.exists:
            if upgrade.WARPGATERESEARCH not in self.ai.state.upgrades and\
                    not self.ai.already_pending_upgrade(upgrade.WARPGATERESEARCH) and\
                    self.ai.can_afford(upgrade.WARPGATERESEARCH):
                self.ai.do(cyber.random.research(upgrade.WARPGATERESEARCH))

    def air_dmg(self):
        cyber = self.ai.structures(unit.CYBERNETICSCORE).ready.idle
        if cyber.exists:
            if upgrade.PROTOSSAIRWEAPONSLEVEL1 not in self.ai.state.upgrades and self.ai.can_afford(
                    upgrade.PROTOSSAIRWEAPONSLEVEL1) and \
                    not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL1):
                self.ai.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL1))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL2 not in self.ai.state.upgrades and self.ai.can_afford(
                    upgrade.PROTOSSAIRWEAPONSLEVEL2) and \
                    not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL2):
                self.ai.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL2))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL3 not in self.ai.state.upgrades and self.ai.can_afford(
                    upgrade.PROTOSSAIRWEAPONSLEVEL3) and \
                    not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRWEAPONSLEVEL3):
                self.ai.do(cyber.random.research(upgrade.PROTOSSAIRWEAPONSLEVEL3))
            elif upgrade.PROTOSSAIRWEAPONSLEVEL3 in self.ai.state.upgrades:
                if upgrade.PROTOSSAIRARMORSLEVEL1 not in self.ai.state.upgrades and self.ai.can_afford(
                        upgrade.PROTOSSAIRARMORSLEVEL1) and \
                        not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRARMORSLEVEL1):
                    self.ai.do(cyber.random.research(upgrade.PROTOSSAIRARMORSLEVEL1))
                elif upgrade.PROTOSSAIRARMORSLEVEL2 not in self.ai.state.upgrades and self.ai.can_afford(
                        upgrade.PROTOSSAIRARMORSLEVEL2) and \
                        not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRARMORSLEVEL2):
                    self.ai.do(cyber.random.research(upgrade.PROTOSSAIRARMORSLEVEL2))
                elif upgrade.PROTOSSAIRARMORSLEVEL3 not in self.ai.state.upgrades and self.ai.can_afford(
                        upgrade.PROTOSSAIRARMORSLEVEL3) and \
                        not self.ai.already_pending_upgrade(upgrade.PROTOSSAIRARMORSLEVEL3):
                    self.ai.do(cyber.random.research(upgrade.PROTOSSAIRARMORSLEVEL3))


class TwilightUpgrader:
    def __init__(self, ai):
        self.ai = ai

    async def none(self):
        pass

    async def charge(self):
        if upgrade.CHARGE not in self.ai.state.upgrades and self.ai.structures(unit.TWILIGHTCOUNCIL).ready.exists:
            tc = self.ai.structures(unit.TWILIGHTCOUNCIL).ready.idle
            if tc.exists:
                tc = tc.random
                abilities = await self.ai.get_available_abilities(tc)
                if ability.RESEARCH_CHARGE in abilities:
                    self.ai.do(tc(ability.RESEARCH_CHARGE))

    async def blink(self):
        if upgrade.BLINKTECH not in self.ai.state.upgrades and self.ai.structures(unit.TWILIGHTCOUNCIL).ready.exists:
            tc = self.ai.structures(unit.TWILIGHTCOUNCIL).ready.idle
            if tc.exists:
                tc = tc.random
                abilities = await self.ai.get_available_abilities(tc)
                if ability.RESEARCH_BLINK in abilities:
                    self.ai.do(tc(ability.RESEARCH_BLINK))

    async def both(self):
        if self.ai.structures(unit.TWILIGHTCOUNCIL).ready.exists:
            if upgrade.CHARGE not in self.ai.state.upgrades:
                tc = self.ai.structures(unit.TWILIGHTCOUNCIL).ready.idle
                if tc.exists:
                    tc = tc.random
                    abilities = await self.ai.get_available_abilities(tc)
                    if ability.RESEARCH_CHARGE in abilities:
                        self.ai.do(tc(ability.RESEARCH_CHARGE))
            elif upgrade.BLINKTECH not in self.ai.state.upgrades:
                tc = self.ai.structures(unit.TWILIGHTCOUNCIL).ready.idle
                if tc.exists:
                    tc = tc.random
                    abilities = await self.ai.get_available_abilities(tc)
                    if ability.RESEARCH_BLINK in abilities:
                        self.ai.do(tc(ability.RESEARCH_BLINK))


class TemplarArchiveUpgrader:
    def __init__(self, ai):
        self.ai = ai

    async def none(self):
        pass

    async def storm(self):
        if upgrade.PSISTORMTECH not in self.ai.state.upgrades:
            tc = self.ai.structures(unit.TEMPLARARCHIVE).ready.idle
            if tc.exists:
                tc = tc.random
                abilities = await self.ai.get_available_abilities(tc)
                if ability.RESEARCH_PSISTORM in abilities:
                    self.ai.do(tc(ability.RESEARCH_PSISTORM))



class FleetBeaconUpgrader:
    def __init__(self, ai):
        self.ai = ai

    async def voidrays(self):
        fleet = self.ai.structures(unit.FLEETBEACON).ready
        if fleet.exists:
            fleet = fleet.random
            if ability.FLEETBEACONRESEARCH_RESEARCHVOIDRAYSPEEDUPGRADE in await self.ai.get_available_abilities(fleet):
                self.ai.do(fleet(ability.FLEETBEACONRESEARCH_RESEARCHVOIDRAYSPEEDUPGRADE))