

from types import FunctionType
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import csv

MAX_LAST_RUN_SEARCH = 7  # days

class Conversion(Enum):
    """Method definitions to convert raw values into human-readable formats."""
    HEX_TO_INT = 1
    BIT_IN_BYTE = 2
    TWO_BYTE_FLOW_RATE = 3
    TWO_BYTE_DS18B20_TEMP = 4
    TWO_BYTE_SHT1X_TEMP = 5
    TWO_BYTE_SHT1X_HUMIDITY = 6
    TWO_BYTE_DS18B20_HUMIDITY = 7
    RIVER_MAX_TAKE = 8
    BATTERY = 9
    RX_SIGNAL = 10
    FLOW_COUNTS = 11
    WIND_DIR = 12
    SOIL_TEMP = 13
    SOIL_MOISTURE = 14
    DPL_HOUR_COUNT = 15
    PUMP_STOPPED_MSG = 16
    PUMP_STATUS_MSG = 17
    LAT_LONG = 18
    DPL_LAST_RUN = 19
    RIVER_COUNTS = 20

def hex_to_int(hex_str: str) -> str:
    if hex_str.upper() == 'FF':
        return '---'
    return str(int(hex_str, 16))

def bit_in_byte(hex_str: str, bit: int) -> bool:
    return (int(hex_str, 16) & (1 << bit)) != 0

def two_byte_flow_rate(hex_str: str, flow_factor: str, lps: bool) -> str:
    val = int(hex_str, 16) * (10 ** (int(flow_factor) - 1))
    if lps:
        val /= 10
        return f"{val} L/s"
    return f"{val} L/min"

def two_byte_ds18b20_temp(hex_str: str) -> str:
    val = int(hex_str, 16)
    if val > 2000:
        val = ((val ^ 0xffff) + 1) * -1
    return f"{val * 0.0625:.1f}"

def two_byte_sht1x_temp(hex_str: str) -> str:
    if hex_str.upper() == 'FFFF':
        raise ValueError('Invalid Temperature Reading')
    return f"{-40.1 + (0.01 * int(hex_str, 16)):.1f}"

def two_byte_sht1x_humidity(hex_str: str, air_hex: str) -> str:
    if hex_str.upper() == 'FFFF':
        raise ValueError('Invalid Humidity Reading')
    air_temp = -40.1 + (0.01 * int(air_hex, 16))
    val = int(hex_str, 16)
    result = (-2.0468 + (0.0367 * val) + (-0.0000015955 * val**2) + 
                ((air_temp - 25) * (0.01 + 0.00008 * val)))
    return str(round(result))

def two_byte_ds18b20_humidity(hex_str: str, air_hex: str) -> str:
    int_val = int(air_hex, 16)
    if int_val > 2000:
        int_val = ((int_val ^ 0xffff) + 1) * -1
    air_temp = int_val * 0.0625
    
    val = int(hex_str, 16)
    result = (-2.0468 + (0.0367 * val) + (-0.0000015955 * val**2) + 
                ((air_temp - 25) * (0.01 + 0.00008 * val)))
    return str(round(result))

def river_max_take(hex_str: str, river_min: int, river_med: int, river_max: int) -> str:
    val = int(hex_str, 16)
    if val & (1 << 0) != 0:
        return_val = river_min
    elif val & (1 << 1) != 0:
        return_val = river_med
    elif val & (1 << 2) != 0:
        return_val = river_max
    else:
        return_val = 0
    return str(return_val)

def battery(hex_str: str, modifier: int = 0) -> str:
    return str((int(hex_str, 16) + modifier) / 10)

def rx_signal(hex_str: str) -> str:
    return str(max(1, round(((int(hex_str, 16) - 100) / 155) * 100)))

def wind_dir(hex_str: str) -> str:
    dir_deg = int(hex_str, 16) * (360 / 255)
    fuzzy_dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    fuzzy_dir = fuzzy_dirs[round(dir_deg / 45) % 8]
    return f"{round(dir_deg)}° ({fuzzy_dir})"

def soil_temp(hex_str: str) -> str:
    return f"{3.75 * (int(hex_str, 16) * 0.08658) - 25:.1f}"

def soil_moisture(hex_str: str, soil_porosity: float) -> str:
    SANDY_THRESHOLD = 0.5
    CLAY_THRESHOLD = 0.6
    
    def sand(ma: float) -> float:
        return (3.75 * ma) - 15
    
    def clay(ma: float) -> float:
        return -14 + (2.87 * ma) + (0.214 * ma**2) - (0.0086 * ma**3)
    
    adc = int(hex_str, 16)
    ma = adc * 0.08823529411764705
    
    if soil_porosity <= SANDY_THRESHOLD:
        wfp = sand(ma)
    elif soil_porosity >= CLAY_THRESHOLD:
        wfp = clay(ma)
    else:
        t = (soil_porosity - SANDY_THRESHOLD) / (CLAY_THRESHOLD - SANDY_THRESHOLD)
        wfp = ((1 - t) * sand(ma)) + (t * clay(ma))
    
    wfp /= soil_porosity
    return f"{wfp:.0f}"

def dpl_hour_count(cls, path: str, device_id: int, days_ago: int) -> str:
    IR_RUNN = 0
    G_WASH = 3
    
    run = False
    total_seconds = 0
    old_time = None
    
    # Previous day file
    prev_date = datetime.now() - timedelta(days=days_ago + 1)
    fname = Path(path) / prev_date.strftime('%Y/%B') / f'DPlink-Hub {device_id}' / \
            f'DPlink-Hub {device_id} {prev_date.strftime("%d-%m-%y")}.csv'
    
    if fname.exists():
        try:
            with open(fname, 'r') as f:
                lines = list(csv.reader(f))
                if lines:
                    line = lines[-1]
                    if (int(line[24], 16) & (1 << G_WASH) == 0) and \
                        (int(line[6], 16) & (1 << IR_RUNN) != 0):
                        old_time = datetime.strptime(f"{line[0]} {line[1]}", "%d/%m/%Y %H:%M:%S")
                        run = True
        except:
            return 'Error'
    
    # Current day file
    curr_date = datetime.now() - timedelta(days=days_ago)
    fname = Path(path) / curr_date.strftime('%Y/%B') / f'DPlink-Hub {device_id}' / \
            f'DPlink-Hub {device_id} {curr_date.strftime("%d-%m-%y")}.csv'
    
    if fname.exists():
        try:
            with open(fname, 'r') as f:
                lines = list(csv.reader(f))
                
            for line in lines[1:]:
                pump_on = (int(line[24], 16) & (1 << G_WASH) == 0) and \
                            (int(line[6], 16) & (1 << IR_RUNN) != 0)
                new_time = datetime.strptime(f"{line[0]} {line[1]}", "%d/%m/%Y %H:%M:%S")
                
                if run and old_time:
                    total_seconds += int((new_time - old_time).total_seconds())
                
                run = pump_on
                old_time = new_time
        except:
            return 'Error'
    
    if run and old_time:
        time_diff = (datetime.now() - old_time).total_seconds() / 60
        if time_diff < 10:
            total_seconds += int((datetime.now() - old_time).total_seconds())
    
    result = ''
    if total_seconds >= 3600:
        result += f'{total_seconds // 3600}hr '
        total_seconds %= 3600
    if total_seconds >= 60:
        result += f'{total_seconds // 60}min '
        total_seconds %= 60
    result += f'{total_seconds}sec'
    
    return result


def dpl_last_run(cls, path: str, device_id: int) -> str:
    IR_RUNN = 0
    G_WASH = 3
    
    last_time = datetime.now()
    end_time = datetime.now()
    run = False
    
    for i in range(cls.MAX_LAST_RUN_SEARCH + 1):
        check_date = datetime.now() - timedelta(days=i)
        fname = Path(path) / check_date.strftime('%Y/%B') / f'DPlink-Hub {device_id}' / \
                f'DPlink-Hub {device_id} {check_date.strftime("%d-%m-%y")}.csv'
        
        if not fname.exists():
            continue
        
        try:
            with open(fname, 'r') as f:
                lines = list(csv.reader(f))
        except:
            return 'Error'
        
        for line in reversed(lines[1:]):
            running = (int(line[24], 16) & (1 << G_WASH) == 0) and \
                        (int(line[6], 16) & (1 << IR_RUNN) != 0)
            
            if running != run:
                if running:
                    end_time = last_time
                    run = True
                else:
                    total_seconds = int((last_time - end_time).total_seconds())
                    result = ''
                    if total_seconds >= 3600:
                        result += f'{total_seconds // 3600}hr '
                        total_seconds %= 3600
                    if total_seconds >= 60:
                        result += f'{total_seconds // 60}min '
                        total_seconds %= 60
                    result += f'{total_seconds}sec'
                    return result
            
            last_time = datetime.strptime(f"{line[0]} {line[1]}", "%d/%m/%Y %H:%M:%S")
    
    return 'N/A'

def pump_stopped_msg(hex_val: str, args: list[str]) -> str:
    int_val = int(hex_val, 16)
    if int_val & (1 << 8):
        return args[0]
    elif int_val & (1 << 5):
        return args[1]
    else:
        return args[2]

def pump_status_msg(status_mes: str, args: list[str]) -> str:
    status_dict: dict[int, tuple[str, bool]] = {
        0: (" N/A", True),
        1: (" Stopped By Operator", False),
        2: (" Stopped Moving", False),
        3: (" End Of Travel", False),
        4: (" Lost Irrigator Signal", False),
        5: (" Flat Irrigator Battery", False),
        6: (" Pond Too Low", False),
        7: (" High Pressure At Pods", False),
        8: (" Moving Too Slow", False),
        9: (" Remote Control Stop", False),
        10: (" No Start Speed", False),
        11: (" Irrigator Pump Fail", False),
        12: (" Finished Irrigating", False),
        13: (" No Pressure At Pods", False),
        14: (" Low Pressure At Pods", False),
        15: (" Stopped From Pods", False),
        16: (" No Start Pressure", False),
        17: (" Above High Pressure SP", False),
        18: (" Below Low Pressure SP", False),
        19: (" Keep Out Area", False),
        20: (" Stopped For Milking", False),
        21: (" Stopped By Ext Timer", False),
        22: (" Pmp Protection ShtDn", False),
        23: (" No Pressure At Pivot", False),
        24: (" Stopped From Pivot", False),
        25: (" High Pressure At Pivot", False),
        26: (" Low Pressure At Pivot", False),
        27: (" Lost Pod Signal", False),
        28: (" Lost Pivot Signal", False),
        29: (" Moving Too Fast", False),
        30: (" Pivot Stopped moving", False),
        31: (" High Pump Pressure", False),
        32: (" Low Pump Pressure", False),
        33: (" Irrigate Suspended", False),
        34: (" Pond Rising", True),
        35: (" Pond Falling", True),
        36: (" Pond Full", True),
        37: (" No Valves Open", False),
        38: (" High Pond Lvl Alarm", True),
        39: (" Doing KIM Off Time", False),
        40: (" Opening IR Valve", True),
        41: (" Finished GnWash", False),
        42: (" Opening GW Valve", True),
        43: (" Link Failed", False),
        44: (" No Pivot Stop Signal", False),
        45: (" Calibration Failed", False),
        46: (" Stopped From Larall", False),
        47: (" No GIM Pressure", False),
        48: (" GIM Pressure Failed", False),
        49: (" Link Restored", True),
        50: (" Starting Irrigator", True),
        51: (" Memory Fail-Safe", False),
        52: (" Below TR Low Lvl SP", False),
        53: (" Below IR Low Lvl SP", False),
        54: (" DPL Interrupt R/Stop", True),
        55: (" Seperate Transferring", True),
        56: (" Auto Transferring", True),
        57: (" * Frost Mode On *", False),
        58: (" Start From Irrigator", True),
        59: (" Manual Transferring", True),
        60: (" Finished Transferring", False),
        61: (" Opening TR Valve", True),
        62: (" Larall Irrigating", True),
        63: (" Kim Irrigating", True),
        64: (" Tim Irrigating", True),
        65: (" Pim Irrigating", True),
        66: (" Pre-Agitating", True),
        67: (" Finished Agitating", True),
        68: (" Starting Agitating", True),
        69: (" Agitating", True),
        70: (" Agitator Failed", True),
        71: (" Starting Transfer", True),
        72: (" Transfer Failed", True),
        73: (" Green Wash Running", False),
        74: (" Auto Transfer Mode", True),
        75: (" Multi Kim System", True),
        76: (" FarmTrenz", True),
        77: (" Kim Irrigating Ln: 1", True),
        78: (" Kim Irrigating Ln: 2", True),
        79: (" Kim Irrigating Ln: 3", True),
        80: (" Kim Irrigating Ln: 4", True),
        81: (" Tim IR + Sep.TR", True),
        82: (" Kim IR + Sep.TR", True),
        83: (" Larall IR + Sep.TR", True),
        84: (" Pim IR + Sep.TR", True),
        85: (" Changing to New Line", True),
        86: (" No Mode Selected", True),
        87: (" Larall Hi Bit Alarm", True),
        88: (" System Locked", True),
    }
    
    try:
        code = int(status_mes, 16)
        message, blacklisted = status_dict.get(code, (' N/A', False))
        return message if not blacklisted else ' N/A'
    except:
        return ' N/A'

def lat_long(raw: str) -> str:
    pos = raw.find('.') - 1
    if pos > 0:
        result = list(raw)
        result.insert(pos, '° ')
        return ''.join(result) + "'"
    return ' N/A'

def river_counts(raw: str) -> str:
    return raw


def get_conversion(id : int) -> FunctionType | None:
    conversions : dict[int, FunctionType] = {
        Conversion.HEX_TO_INT.value: hex_to_int,
        Conversion.BIT_IN_BYTE.value: bit_in_byte,
        Conversion.TWO_BYTE_FLOW_RATE.value: two_byte_flow_rate,
        Conversion.TWO_BYTE_DS18B20_TEMP.value: two_byte_ds18b20_temp,
        Conversion.TWO_BYTE_SHT1X_TEMP.value: two_byte_sht1x_temp,
        Conversion.TWO_BYTE_SHT1X_HUMIDITY.value: two_byte_sht1x_humidity,
        Conversion.TWO_BYTE_DS18B20_HUMIDITY.value: two_byte_ds18b20_humidity,
        Conversion.RIVER_MAX_TAKE.value: river_max_take,
        Conversion.BATTERY.value: battery,
        Conversion.RX_SIGNAL.value: rx_signal,
        Conversion.WIND_DIR.value: wind_dir,
        Conversion.SOIL_TEMP.value: soil_temp,
        Conversion.SOIL_MOISTURE.value: soil_moisture,
        Conversion.DPL_HOUR_COUNT.value: dpl_hour_count,
        Conversion.PUMP_STOPPED_MSG.value: pump_stopped_msg,
        Conversion.PUMP_STATUS_MSG.value: pump_status_msg,
        Conversion.LAT_LONG.value: lat_long,
        Conversion.DPL_LAST_RUN.value: dpl_last_run,
        Conversion.RIVER_COUNTS.value: river_counts
    }
    return conversions.get(id, None)