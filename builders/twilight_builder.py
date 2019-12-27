from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.ability_id import AbilityId as ability


class TwilightBuilder:
    @staticmethod
    async def stalkers(ai):
        pass

    @staticmethod
    async def zealots(ai):
        if ai.structures(unit.CYBERNETICSCORE).ready.exists and ai.time > 360:
            if not ai.structures(unit.TWILIGHTCOUNCIL).exists \
                    and not ai.already_pending(unit.TWILIGHTCOUNCIL) and ai.can_afford(unit.TWILIGHTCOUNCIL):
                pylon = ai.get_proper_pylon()
                await ai.build(unit.TWILIGHTCOUNCIL,near=pylon.position,
                                 random_alternative=True,placement_step=2)
            if ai.structures(unit.TWILIGHTCOUNCIL).ready.exists:
                tc = ai.structures(unit.TWILIGHTCOUNCIL).ready.idle
                if tc.exists:
                    tc = tc.random
                else:
                    return
                abilities = await ai.get_available_abilities(tc)
                if ability.RESEARCH_CHARGE in abilities:
                    ai.do(tc(ability.RESEARCH_CHARGE))