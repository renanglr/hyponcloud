"""Data models for Hypontech Cloud API."""

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig


class _HyponConfig(BaseConfig):
    """Shared mashumaro configuration for all models."""

    omit_none = True
    allow_deserialization_not_by_alias = True


@dataclass
class EarningData(DataClassDictMixin):
    """Earning data for a plant."""

    currency: str = ""
    today: float = 0.0
    total: float = 0.0

    Config = _HyponConfig


@dataclass
class GatewayData(DataClassDictMixin):
    """Gateway device data for an inverter."""

    sn: str = ""
    model: str = ""
    status: str = ""
    time: str = ""
    push_time: int = 0
    pid: str = ""

    Config = _HyponConfig


@dataclass
class PortData(DataClassDictMixin):
    """Port data for an inverter."""

    sn: str = ""
    id: str = ""
    x: int = -1
    y: int = -1
    port: int = 0

    Config = _HyponConfig


@dataclass
class BatteryData(DataClassDictMixin):
    """Battery data from the plant endpoint or an inverter snapshot."""

    time: str = ""
    sn: str = ""
    status: str = ""
    soc: float = 0.0
    ahrtg: float = 0.0
    wh: float = 0.0
    ohk: int = 0
    a_bat: float = 0.0
    a_bat_inv: float = 0.0
    achamax: float = 0.0
    adischamax: float = 0.0
    battery_model: str = ""
    gateway_model: str = ""
    gsn: str = ""
    gsn_version: str = ""
    huayu: int = 0
    inv_sn: str = ""
    manufacturer: str = ""
    model: str = ""
    mosstate: int = 0
    ncyc: int = 0
    pid: str = ""
    plant_name: str = ""
    single_hp_bat_sns: list[str] | None = None
    spn: str = ""
    st: int = 0
    software_version: str = ""
    upgrade_state: int = 0
    v_bat: float = 0.0
    v_bat_inv: float = 0.0

    class Config(_HyponConfig):
        aliases = {
            "ohk": "OHK",
            "gsn_version": "gsnversion",
            "single_hp_bat_sns": "singleHpBatSns",
            "software_version": "sversion",
        }


@dataclass
class OverviewData(DataClassDictMixin):
    """Overview data class.

    This class represents the overview data for a Hypon Cloud plant.
    It contains information about the plant's capacity, power, energy production,
    device status, and environmental impact.
    """

    capacity: float = 0.0
    capacity_company: str = "KW"
    power: float = 0.0
    company: str = "W"
    percent: int = 0
    e_today: float = 0.0
    e_total: float = 0.0
    fault_dev_num: int = 0
    normal_dev_num: int = 0
    offline_dev_num: int = 0
    wait_dev_num: int = 0
    total_co2: float = 0.0
    total_tree: float = 0.0
    earning: list[EarningData] = field(default_factory=list)

    Config = _HyponConfig


@dataclass
class PlantData(DataClassDictMixin):
    """Plant data class.

    This class represents the data for a Hypon Cloud plant.
    It contains information about the plant's location, energy production,
    identifiers, and status.
    """

    city: str = ""
    country: str = ""
    e_today: float = 0.0
    e_total: float = 0.0
    eid: int = 0
    kwhimp: int = 0
    micro: int = 0
    plant_id: str = ""
    plant_name: str = ""
    plant_type: str = ""
    power: float = 0.0
    company: str = "W"
    status: str = ""
    time: str = ""
    photo: str = ""
    owner_name: str = ""
    owner_id: str = ""
    top: int = 0
    property: int = 0

    Config = _HyponConfig


@dataclass
class InverterData(DataClassDictMixin):
    """Inverter data class.

    This class represents the data for a Hypon Cloud inverter.
    It contains information about the inverter's status, power output,
    energy production, and device details.
    """

    plant_name: str = ""
    sn: str = ""
    gateway_sn: str = ""
    status: str = ""
    model: str = ""
    software_version: str = ""
    lcd_version: str = ""
    afci_version: str = ""
    afci_version0: str = ""
    afci_version1: str = ""
    afci_version2: str = ""
    time: str = ""
    spn: str = ""
    power: float = 0.0
    eid: str = ""
    device_type: str = ""
    fault: int = 0
    warning: int = 0
    plant_id: str = ""
    modbus: int = 0
    e_total: float = 0.0
    e_today: float = 0.0
    property: int = 0
    nick_name: str = ""
    com: int = 0
    system_connect_mode: int = 0
    third_active_power: int = 0
    third_meter_energy: int = 0
    today_generation_third: int = 0
    gateway: GatewayData | None = None
    battery: BatteryData | None = None
    port: list[PortData] = field(default_factory=list)

    Config = _HyponConfig


@dataclass
class PlantMonitorData(DataClassDictMixin):
    """Plant monitor data class.

    This class represents the real-time monitoring data for a specific plant,
    as returned by the plant monitor endpoint.
    """

    monetary: str = ""
    today_earning: float = 0.0
    month_earning: float = 0.0
    total_earning: float = 0.0
    e_today: float = 0.0
    e_month: float = 0.0
    e_total: float = 0.0
    e_year: float = 0.0
    total_tree: float = 0.0
    total_co2: float = 0.0
    total_diesel: float = 0.0
    percent: float = 0.0
    meter_power: float = 0.0  # Power drawn from the grid (W)
    power_load: float = 0.0  # Home/load power consumption (W)
    w_cha: float = 0.0  # Battery discharging power (W)
    power_pv: float = 0.0  # PV (solar) generation power (W)
    soc: float = 0.0
    micro: int = 0
    warning: str = ""

    Config = _HyponConfig


@dataclass
class AdminInfo(DataClassDictMixin):
    """Administrator information data class.

    This class represents administrator account information including
    user details, roles, and permissions.
    """

    parent_name: str = ""
    role: list[str] | None = None
    parent_id: str = ""
    has_lower_level: bool = False
    last_login_time: str = ""
    created_at: str = ""
    deleted_at: str = ""
    country: str = ""
    address: str = ""
    email: str = ""
    mobile: str = ""
    mobile_prefix_code: str = ""
    login_name: str = ""
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    city: str = ""
    city_mobile_code: str = ""
    username: str = ""
    country_mobile_code: str = ""
    photo: str = ""
    address2: str = ""
    language: str = ""
    currency: str = ""
    postal_code: str = ""
    timezone: str = ""
    last_login_ip: str = ""
    id: str = ""
    eid: int = 0
    manufacturer: int = 0
    switch_warning: int = 0
    is_internal: int = 0
    status: int = 0
    first_login: bool = False
    token: str = ""

    Config = _HyponConfig
