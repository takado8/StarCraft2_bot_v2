# THIS FILE WAS AUTOMATICALLY GENERATED BY "generate_dicts_from_data_json.py" DO NOT CHANGE MANUALLY!
# ANY CHANGE WILL BE OVERWRITTEN

from ..ids.unit_typeid import UnitTypeId
from ..ids.ability_id import AbilityId
from ..ids.upgrade_id import UpgradeId

# from ..ids.buff_id import BuffId
# from ..ids.effect_id import EffectId

from typing import Dict, Set, Union

UNIT_TRAINED_FROM: Dict[UnitTypeId, Set[UnitTypeId]] = {
    UnitTypeId.ADEPT: {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE},
    UnitTypeId.ARMORY: {UnitTypeId.SCV},
    UnitTypeId.ASSIMILATOR: {UnitTypeId.PROBE},
    UnitTypeId.AUTOTURRET: {UnitTypeId.RAVEN},
    UnitTypeId.BANELING: {UnitTypeId.ZERGLING},
    UnitTypeId.BANELINGNEST: {UnitTypeId.DRONE},
    UnitTypeId.BANSHEE: {UnitTypeId.STARPORT},
    UnitTypeId.BARRACKS: {UnitTypeId.SCV},
    UnitTypeId.BATTLECRUISER: {UnitTypeId.STARPORT},
    UnitTypeId.BROODLORD: {UnitTypeId.CORRUPTOR},
    UnitTypeId.BUNKER: {UnitTypeId.SCV},
    UnitTypeId.CARRIER: {UnitTypeId.STARGATE},
    UnitTypeId.CHANGELING: {UnitTypeId.OVERSEER, UnitTypeId.OVERSEERSIEGEMODE},
    UnitTypeId.COLOSSUS: {UnitTypeId.ROBOTICSFACILITY},
    UnitTypeId.COMMANDCENTER: {UnitTypeId.SCV},
    UnitTypeId.CORRUPTOR: {UnitTypeId.LARVA},
    UnitTypeId.CREEPTUMOR: {
        UnitTypeId.CREEPTUMOR,
        UnitTypeId.CREEPTUMORBURROWED,
        UnitTypeId.CREEPTUMORQUEEN,
        UnitTypeId.QUEEN,
    },
    UnitTypeId.CREEPTUMORQUEEN: {UnitTypeId.QUEEN},
    UnitTypeId.CYBERNETICSCORE: {UnitTypeId.PROBE},
    UnitTypeId.CYCLONE: {UnitTypeId.FACTORY},
    UnitTypeId.DARKSHRINE: {UnitTypeId.PROBE},
    UnitTypeId.DARKTEMPLAR: {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE},
    UnitTypeId.DISRUPTOR: {UnitTypeId.ROBOTICSFACILITY},
    UnitTypeId.DRONE: {UnitTypeId.LARVA},
    UnitTypeId.ENGINEERINGBAY: {UnitTypeId.SCV},
    UnitTypeId.EVOLUTIONCHAMBER: {UnitTypeId.DRONE},
    UnitTypeId.EXTRACTOR: {UnitTypeId.DRONE},
    UnitTypeId.FACTORY: {UnitTypeId.SCV},
    UnitTypeId.FLEETBEACON: {UnitTypeId.PROBE},
    UnitTypeId.FORGE: {UnitTypeId.PROBE},
    UnitTypeId.FUSIONCORE: {UnitTypeId.SCV},
    UnitTypeId.GATEWAY: {UnitTypeId.PROBE},
    UnitTypeId.GHOST: {UnitTypeId.BARRACKS},
    UnitTypeId.GHOSTACADEMY: {UnitTypeId.SCV},
    UnitTypeId.GREATERSPIRE: {UnitTypeId.SPIRE},
    UnitTypeId.HATCHERY: {UnitTypeId.DRONE},
    UnitTypeId.HELLION: {UnitTypeId.FACTORY},
    UnitTypeId.HELLIONTANK: {UnitTypeId.FACTORY},
    UnitTypeId.HIGHTEMPLAR: {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE},
    UnitTypeId.HIVE: {UnitTypeId.LAIR},
    UnitTypeId.HYDRALISK: {UnitTypeId.LARVA},
    UnitTypeId.HYDRALISKDEN: {UnitTypeId.DRONE},
    UnitTypeId.IMMORTAL: {UnitTypeId.ROBOTICSFACILITY},
    UnitTypeId.INFESTATIONPIT: {UnitTypeId.DRONE},
    UnitTypeId.INFESTOR: {UnitTypeId.LARVA},
    UnitTypeId.LAIR: {UnitTypeId.HATCHERY},
    UnitTypeId.LIBERATOR: {UnitTypeId.STARPORT},
    UnitTypeId.LOCUSTMPFLYING: {UnitTypeId.SWARMHOSTBURROWEDMP, UnitTypeId.SWARMHOSTMP},
    UnitTypeId.LURKERDENMP: {UnitTypeId.DRONE},
    UnitTypeId.LURKERMP: {UnitTypeId.HYDRALISK},
    UnitTypeId.MARAUDER: {UnitTypeId.BARRACKS},
    UnitTypeId.MARINE: {UnitTypeId.BARRACKS},
    UnitTypeId.MEDIVAC: {UnitTypeId.STARPORT},
    UnitTypeId.MISSILETURRET: {UnitTypeId.SCV},
    UnitTypeId.MOTHERSHIP: {UnitTypeId.NEXUS},
    UnitTypeId.MUTALISK: {UnitTypeId.LARVA},
    UnitTypeId.NEXUS: {UnitTypeId.PROBE},
    UnitTypeId.NYDUSCANAL: {UnitTypeId.NYDUSNETWORK},
    UnitTypeId.NYDUSNETWORK: {UnitTypeId.DRONE},
    UnitTypeId.OBSERVER: {UnitTypeId.ROBOTICSFACILITY},
    UnitTypeId.ORACLE: {UnitTypeId.STARGATE},
    UnitTypeId.ORACLESTASISTRAP: {UnitTypeId.ORACLE},
    UnitTypeId.OVERLORD: {UnitTypeId.LARVA},
    UnitTypeId.OVERLORDTRANSPORT: {UnitTypeId.OVERLORD},
    UnitTypeId.OVERSEER: {UnitTypeId.OVERLORD, UnitTypeId.OVERLORDTRANSPORT},
    UnitTypeId.PHOENIX: {UnitTypeId.STARGATE},
    UnitTypeId.PHOTONCANNON: {UnitTypeId.PROBE},
    UnitTypeId.PROBE: {UnitTypeId.NEXUS},
    UnitTypeId.PYLON: {UnitTypeId.PROBE},
    UnitTypeId.QUEEN: {UnitTypeId.HATCHERY, UnitTypeId.HIVE, UnitTypeId.LAIR},
    UnitTypeId.RAVAGER: {UnitTypeId.ROACH},
    UnitTypeId.RAVEN: {UnitTypeId.STARPORT},
    UnitTypeId.REAPER: {UnitTypeId.BARRACKS},
    UnitTypeId.REFINERY: {UnitTypeId.SCV},
    UnitTypeId.ROACH: {UnitTypeId.LARVA},
    UnitTypeId.ROACHWARREN: {UnitTypeId.DRONE},
    UnitTypeId.ROBOTICSBAY: {UnitTypeId.PROBE},
    UnitTypeId.ROBOTICSFACILITY: {UnitTypeId.PROBE},
    UnitTypeId.SCV: {
        UnitTypeId.COMMANDCENTER,
        UnitTypeId.ORBITALCOMMAND,
        UnitTypeId.PLANETARYFORTRESS,
    },
    UnitTypeId.SENSORTOWER: {UnitTypeId.SCV},
    UnitTypeId.SENTRY: {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE},
    UnitTypeId.SHIELDBATTERY: {UnitTypeId.PROBE},
    UnitTypeId.SIEGETANK: {UnitTypeId.FACTORY},
    UnitTypeId.SPAWNINGPOOL: {UnitTypeId.DRONE},
    UnitTypeId.SPINECRAWLER: {UnitTypeId.DRONE},
    UnitTypeId.SPIRE: {UnitTypeId.DRONE},
    UnitTypeId.SPORECRAWLER: {UnitTypeId.DRONE},
    UnitTypeId.STALKER: {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE},
    UnitTypeId.STARGATE: {UnitTypeId.PROBE},
    UnitTypeId.STARPORT: {UnitTypeId.SCV},
    UnitTypeId.SUPPLYDEPOT: {UnitTypeId.SCV},
    UnitTypeId.SWARMHOSTMP: {UnitTypeId.LARVA},
    UnitTypeId.TEMPEST: {UnitTypeId.STARGATE},
    UnitTypeId.TEMPLARARCHIVE: {UnitTypeId.PROBE},
    UnitTypeId.THOR: {UnitTypeId.FACTORY},
    UnitTypeId.TWILIGHTCOUNCIL: {UnitTypeId.PROBE},
    UnitTypeId.ULTRALISK: {UnitTypeId.LARVA},
    UnitTypeId.ULTRALISKCAVERN: {UnitTypeId.DRONE},
    UnitTypeId.VIKINGFIGHTER: {UnitTypeId.STARPORT},
    UnitTypeId.VIPER: {UnitTypeId.LARVA},
    UnitTypeId.VOIDRAY: {UnitTypeId.STARGATE},
    UnitTypeId.WARPPRISM: {UnitTypeId.ROBOTICSFACILITY},
    UnitTypeId.WIDOWMINE: {UnitTypeId.FACTORY},
    UnitTypeId.ZEALOT: {UnitTypeId.GATEWAY, UnitTypeId.WARPGATE},
    UnitTypeId.ZERGLING: {UnitTypeId.LARVA},
}
