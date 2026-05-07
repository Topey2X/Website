import random
import dash
from dash import html, dcc, Input, Output, State, callback
from flask import session
from flask_login import current_user
from server import db
import dash_bootstrap_components as dbc
from components.device_card import device_card_example, device_card
from models import DevicesModel, UserModel
import configparser
from components.conversions import *


def update_dashboard():
    # Query database for relevent devices
    esp = db.session.execute(db.select(UserModel.esp).where(UserModel.username == current_user.id)).scalar_one_or_none()
    if esp is None:
        return html.Div("Error: User not found.") # TODO: error handling
    selection = db.select(DevicesModel) \
        .where(DevicesModel.esp == esp) \
        .options(db.joinedload(DevicesModel.device_ref)) # eager load device_ref relationship
        
    devices = db.session.execute(selection).scalars().all()
    if not devices or len(devices) == 0:
        return html.Div("Error: No devices found for this user.") # TODO: error handling
    
    # Get tag DB path for this user to lookup values and alarms
    tagdb_ini = current_user.tagdb_path + "/TagDB.ini"
    
    tagdb = configparser.ConfigParser()
    files_read = tagdb.read(tagdb_ini)
    if not files_read:
        print(f"Warning: Could not read TagDB.ini at {tagdb_ini}") # Debugging output # TODO: error handling
    
    cards = []
    for device in devices:
        # Lookup values and alarms for this device from the database.
        if not device.device_ref:
            continue
        
        device_defs : list = device.device_ref.get_tag_defs() 
        
        values : list[tuple[str,str,bool]]= []
        alarms : list[str] = []
        
        currently_pumping = None # None = unknown, True = pumping, False = not pumping
        active_kim = None # None = unknown, True = this KIM is active, False = this KIM is not active.
        
        # HACK: Set both of the above to True for now
        currently_pumping = True
        active_kim = True
        # HACK: End
         
        for device_def in device_defs:
            # Go through and lookup values
            errored : bool = False
            
            def get_location(s):
                return s.replace("""%s""", str(device.code))
            locations : list[str] = [get_location(s) for s in device_def.get("DBRef", [])] # DBRef is a JSON array.
            
            raw_values : list[str] = []
            for location in locations:
                raw = tagdb.get(location, 'Value', fallback=None)
                if raw is None:
                    errored = True
                    break
                raw_values.append(raw)
            if errored: # TODO: Error handling for missing values
                continue
            
            raw_value = "".join(raw_values)
            if raw_value == "": # TODO: Error handling for empty values
                continue
            
            # TODO: Timeouts
            
            def convert_value(conversion_type : ConversionType) -> tuple[str, bool] | None:
                # Convert raw values using the appropriate conversion function
                match conversion_type:
                    case ConversionType.NONE:
                        return raw_value, False
                        
                    case ConversionType.HEX_TO_INT:
                        return hex_to_int(raw_value), False
                        
                    case ConversionType.BIT_IN_BYTE:
                        value_is_bool = True
                        converted_value = None
                        for x in range(len(device_def["Args"]) // 2):
                            bit_pos = int(device_def["Args"][x * 2])
                            if bit_in_byte(raw_value, bit_pos):
                                converted_value = device_def["Args"][x * 2 + 1]
                                break

                        if converted_value is None:
                            converted_value = device_def["Args"][-1]
                        return converted_value, True
                    
                    case ConversionType.BIT_IN_BYTE_IRRUNN:
                        if currently_pumping is None:
                            ...# TODO: figure out if the pump is active here
                        if not currently_pumping:
                            return None
                        return convert_value(ConversionType.BIT_IN_BYTE)
                    
                    case ConversionType.BIT_IN_BYTE_ACTIVE_KIM:
                        if active_kim is None:
                            ... # TODO: figure out if this KIM is active here
                        if active_kim is False:
                            return None
                        return convert_value(ConversionType.BIT_IN_BYTE)
                    
                    case ConversionType.FLOW_COUNTS:
                        ...# TODO: This requires going into historical values :P
                    
                    case ConversionType.TWO_BYTE_FLOW_RATE:
                        flow_factor = tagdb.get(get_location(device_def["Args"][0]), 'Value', fallback='1')
                        lps = bit_in_byte(tagdb.get(get_location(device_def["Args"][1]), 'Value', fallback='0'), device_def["Args"][2])
                        return two_byte_flow_rate(raw_value, flow_factor, lps), False 
                    
                    case ConversionType.TWO_BYTE_DS18B20_TEMP:
                        return two_byte_ds18b20_temp(raw_value), False
                    
                    case ConversionType.TWO_BYTE_DS18B20_HUMIDITY:
                        air_value = ''
                        for i in range(len(device_def["Args"])):
                            air_value += tagdb.get(get_location(device_def["Args"][i]), 'Value', fallback='0')
                        return two_byte_ds18b20_humidity(raw_value, air_value), False
                    
                    case ConversionType.TWO_BYTE_SHT1X_TEMP:
                        return two_byte_sht1x_temp(raw_value), False
                    
                    case ConversionType.TWO_BYTE_SHT1X_HUMIDITY:
                        air_value = ''
                        for i in range(len(device_def["Args"])):
                            air_value += tagdb.get(get_location(device_def["Args"][i]), 'Value', fallback='0')
                        return two_byte_ds18b20_humidity(raw_value, air_value), False
                    
                    case ConversionType.BATTERY:
                        offset = 0
                        if len(device_def.get("Args", [])) > 0:
                            offset = int(device_def["Args"][0])
                        return battery(raw_value, offset), False
                    
                    case ConversionType.SIGNAL:
                        return rx_signal(raw_value), False
                    
                    case ConversionType.WIND_DIR:
                        return wind_dir(raw_value), True
                    
                    case ConversionType.SOIL_TEMP:
                        if raw_value == "00":
                            return None
                        return soil_temp(raw_value), False
                    
                    case ConversionType.SOIL_MOISTURE:
                        ...# TODO: This requires porosity, a setting
                    
                    case ConversionType.DPL_HOUR_COUNT:
                        ...# TODO: This requires historical values
                        
                    case ConversionType.PUMP_STATUS_MSG:
                        return pump_status_msg(raw_value, device_def["Args"]), False
                    
                    case ConversionType.PUMP_STOPPED_MSG:
                        return pump_stopped_msg(raw_value, device_def["Args"]), False
                    
                    case ConversionType.LAT_LONG:
                        return lat_long(raw_value), False
                    
                    case ConversionType.RIVER_COUNT:
                        return river_counts(raw_value), False
                    
                    case ConversionType.DPL_LAST_RUN:
                        ...# TODO: This requires historical values
                    
                    case _:
                        return None
                return None
                    
            
            converted_value = convert_value(ConversionType(device_def["Conversion"]))
            if converted_value is None:
                continue # TODO: error handling for failed conversions
            converted_value_str, value_is_bool = converted_value
            
            if device_def.get("Alarm", False) == True:
                if converted_value_str != '':
                    alarms.append(converted_value_str)
            else:
                values.append((device_def["Name"], f"{converted_value_str} {device_def.get('Units', '')}", value_is_bool))
        
        cards.append(device_card(
            name=f"{device.device_ref.name} {device.code}", # TODO: Alias
            last_updated="2024-06-01T12:00:00Z", # TODO: device.last_updated
            values=values,
            alarms=alarms,
            show_bar=device.device_ref.has_bar,
            show_line=device.device_ref.has_line,
            show_gps=device.device_ref.has_gps,
            # show_edit=True
        ))
    return [dbc.Col(card, width=12) for card in cards]

def dashboard_layout():
    return dbc.Container(dcc.Loading(dbc.Row([
    ], id="dashboard-row")), fluid=True, className="pb-2")
    
dash.register_page("dashboard", path="/", layout=dashboard_layout)

@callback(
    Output("dashboard-row", "children"),
    Input("dashboard-row", "id"), # Fires once on mount
)
def load_dashboard(_):
    return update_dashboard()