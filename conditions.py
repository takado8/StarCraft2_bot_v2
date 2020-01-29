from sc2.ids.unit_typeid import UnitTypeId as unit
from sc2.ids.upgrade_id import UpgradeId as upgrade


class ConditionAttack:
    def __init__(self, ai):
        self.ai = ai

    def none(self):
        pass

    def rush(self):
        return (not self.ai.first_attack) and upgrade.WARPGATERESEARCH in self.ai.state.upgrades

    def dt(self):
        return (not self.ai.first_attack) and self.ai.structures(unit.DARKSHRINE).ready.amount > 0

    def rush_voidray(self):
        return (not self.ai.first_attack) and self.ai.army(unit.VOIDRAY).amount > 1

    def colossus(self):
        return (not self.ai.first_attack) and self.ai.army(unit.COLOSSUS).amount > 1

    def archons(self):
        return (not self.ai.first_attack) and self.ai.army(unit.ARCHON).amount > 2

    def counter_attack(self):
        en = self.ai.enemy_units()
        return en.exists and en.closer_than(40,self.ai.defend_position).amount > 5


class ConditionRetreat:
    def __init__(self,ai):
        self.ai = ai

    def none(self):
        pass

    def rush(self):
        return self.ai.attack and self.ai.army.amount < 2

    def macro(self):
        return self.ai.attack and self.ai.army.amount < 13