from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.upgrade_id import UpgradeId as upgrade


class ForgeBuilder:
    @staticmethod
    async def none(ai):
        pass

    @staticmethod
    async def macro(ai):
        if ai.time > 160:
            if ai.structures(unit.FORGE).amount < 1 and not ai.already_pending(unit.FORGE) and ai.can_afford(
                    unit.FORGE):
                if ai.structures(unit.PYLON).ready.exists:
                    placement = ai.get_proper_pylon()
                    if placement:
                        await ai.build(unit.FORGE,near=placement,placement_step=2)
            elif ai.structures(unit.FORGE).ready.exists:
                if ai.time > 480 and ai.structures(unit.FORGE).amount < 2 and not ai.already_pending(
                        unit.FORGE) and ai.can_afford(unit.FORGE):
                    placement = ai.get_proper_pylon()
                    if placement:
                        await ai.build(unit.FORGE,near=placement,placement_step=2)
                for forge in ai.structures(unit.FORGE).ready.idle:
                    if upgrade.PROTOSSGROUNDARMORSLEVEL1 not in ai.state.upgrades and not ai.already_pending_upgrade(
                            upgrade.PROTOSSGROUNDARMORSLEVEL1) and ai.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL1):
                        ai.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL1))
                    elif upgrade.PROTOSSGROUNDWEAPONSLEVEL1 not in ai.state.upgrades and not ai.already_pending_upgrade(
                            upgrade.PROTOSSGROUNDWEAPONSLEVEL1) and ai.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL1):
                        ai.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL1))
                    elif upgrade.PROTOSSSHIELDSLEVEL1 not in ai.state.upgrades and not ai.already_pending_upgrade(
                            upgrade.PROTOSSSHIELDSLEVEL1) and ai.can_afford(upgrade.PROTOSSSHIELDSLEVEL1):
                        ai.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL1))
                    elif upgrade.PROTOSSGROUNDARMORSLEVEL2 not in ai.state.upgrades and not ai.already_pending_upgrade(
                            upgrade.PROTOSSGROUNDARMORSLEVEL2) and ai.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL2):
                        ai.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL2))
                    elif upgrade.PROTOSSGROUNDWEAPONSLEVEL2 not in ai.state.upgrades and not ai.already_pending_upgrade(
                            upgrade.PROTOSSGROUNDWEAPONSLEVEL2) and ai.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL2):
                        ai.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL2))
                    elif upgrade.PROTOSSGROUNDWEAPONSLEVEL2 in \
                            ai.state.upgrades and not ai.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDWEAPONSLEVEL3) and ai.can_afford(upgrade.PROTOSSGROUNDWEAPONSLEVEL3):
                        ai.do(forge.research(upgrade.PROTOSSGROUNDWEAPONSLEVEL3))
                    elif upgrade.PROTOSSGROUNDARMORSLEVEL2 in \
                            ai.state.upgrades and not ai.already_pending_upgrade(
                        upgrade.PROTOSSGROUNDARMORSLEVEL3) and ai.can_afford(upgrade.PROTOSSGROUNDARMORSLEVEL3):
                        ai.do(forge.research(upgrade.PROTOSSGROUNDARMORSLEVEL3))
                    elif upgrade.PROTOSSSHIELDSLEVEL2 not in ai.state.upgrades and not ai.already_pending_upgrade(
                            upgrade.PROTOSSSHIELDSLEVEL2) and ai.can_afford(upgrade.PROTOSSSHIELDSLEVEL2) and \
                            upgrade.PROTOSSSHIELDSLEVEL1 in ai.state.upgrades and ai.structures(
                        unit.TWILIGHTCOUNCIL).ready.exists:
                        ai.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL2))
                    elif upgrade.PROTOSSSHIELDSLEVEL3 not in ai.state.upgrades and not ai.already_pending_upgrade(
                            upgrade.PROTOSSSHIELDSLEVEL3) and ai.can_afford(upgrade.PROTOSSSHIELDSLEVEL3) and \
                            upgrade.PROTOSSSHIELDSLEVEL2 in ai.state.upgrades:
                        ai.do(forge.research(upgrade.PROTOSSSHIELDSLEVEL3))