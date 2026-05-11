import random
from time import sleep
import dash
from dash import html, dcc, Input, Output, State, callback
from flask import session
from flask_login import current_user
from server import db
import dash_bootstrap_components as dbc
from components.device_card import device_card
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
    
    def get_location(s):
        return s.replace("""%s""", str(device.code))
    
    cards = []
    for device in devices:
        # Lookup values and alarms for this device from the database.
        if not device.device_ref:
            continue
        
        device_tags : list = device.device_ref.get_tag_defs() 
        
        values : list[tuple[str,str,bool]]= []
        alarms : list[str] = []
        messages : list[str] = []
        
        currently_pumping = None # None = unknown, True = pumping, False = not pumping
        active_kim = None # None = unknown, True = this KIM is active, False = this KIM is not active.
        
        # HACK: Set both of the above to True for now
        currently_pumping = True
        active_kim = True
        # HACK: End
        
        last_updated = None
         
        for device_tag in device_tags:
            # Check if the tag is enabled
            iniRef = device_tag.get("IniRef", None)
            if iniRef:     
                tag_enabled = device.get_tag_override(iniRef)
                if tag_enabled is None:
                    # Find default enabled state for this tag
                    tag_enabled = device_tag.get("Default", True)
                if not tag_enabled:
                    continue # Skip disabled tags
                           
            
            # Go through and lookup values
            errored : bool = False
            
            locations : list[str] = [get_location(s) for s in device_tag.get("DBRef", [])] # DBRef is a JSON array.
            conversion = ConversionType(device_tag.get("Conversion", 0))
            raw_values : list[str] = []
            
            location : str | None = None
            for location in locations:
                raw = tagdb.get(location, 'Value', fallback=None)
                if raw is None: 
                    if conversion not in [ConversionType.FLOW_COUNTS, ConversionType.DPL_HOUR_COUNT, ConversionType.DPL_LAST_RUN]: # These conversions can work without a raw value, so we allow missing values for them
                        errored = True
                    break
                raw_values.append(raw)
            if errored: # TODO: Error handling for missing values
                print(f"Error: Missing value for device {device.device_ref.name} code {device.code} at location {location if location is not None else 'Unknown'}") # Debugging output
                continue
            
            if len(raw_values) > 0:
                raw_value = "".join(raw_values)
                if raw_value == "": # TODO: Error handling for empty values
                    print(f"Error: Empty value for device {device.device_ref.name} code {device.code} at location {location if location is not None else 'Unknown'}") # Debugging output
                    continue
            else:
                raw_value = "" # Some conversions can work with an empty string, so we allow this case.
            # Be aware: some conversions use historical files and won't have any raw_value to convert, so we pass None in that case and handle it in the conversion function.
            
            # TODO: Timeouts
            update = None
            if len(locations) > 0:
                update = tagdb.get(locations[0], 'LastUpdate', fallback=None)
                if update is not None:
                    update_time = datetime.strptime(update, "%d/%m/%Y %H:%M:%S")
                    if last_updated is None or update_time > last_updated:
                        last_updated = update_time
                    
            
            def convert_value(conversion_type : ConversionType) -> tuple[str, bool] | None:
                # Convert raw values using the appropriate conversion function
                match conversion_type:
                    case ConversionType.NONE:
                        return raw_value, False
                        
                    case ConversionType.HEX_TO_INT:
                        return hex_to_int(raw_value), False
                        
                    case ConversionType.BIT_IN_BYTE:
                        converted_value = None
                        for x in range(len(device_tag["Args"]) // 2):
                            bit_pos = int(device_tag["Args"][x * 2])
                            if bit_in_byte(raw_value, bit_pos):
                                converted_value = device_tag["Args"][x * 2 + 1]
                                break

                        if converted_value is None:
                            converted_value = device_tag["Args"][-1]
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
                        flow_factor = tagdb.get(get_location(device_tag["Args"][0]), 'Value', fallback='1')
                        lps = bit_in_byte(tagdb.get(get_location(device_tag["Args"][1]), 'Value', fallback='0'), device_tag["Args"][2])
                        return two_byte_flow_rate(raw_value, flow_factor, lps), False 
                    
                    case ConversionType.TWO_BYTE_DS18B20_TEMP:
                        return two_byte_ds18b20_temp(raw_value), False
                    
                    case ConversionType.TWO_BYTE_DS18B20_HUMIDITY:
                        air_value = ''
                        for i in range(len(device_tag["Args"])):
                            air_value += tagdb.get(get_location(device_tag["Args"][i]), 'Value', fallback='0')
                        return two_byte_ds18b20_humidity(raw_value, air_value), False
                    
                    case ConversionType.TWO_BYTE_SHT1X_TEMP:
                        return two_byte_sht1x_temp(raw_value), False
                    
                    case ConversionType.TWO_BYTE_SHT1X_HUMIDITY:
                        air_value = ''
                        for i in range(len(device_tag["Args"])):
                            air_value += tagdb.get(get_location(device_tag["Args"][i]), 'Value', fallback='0')
                        return two_byte_ds18b20_humidity(raw_value, air_value), False
                    
                    case ConversionType.BATTERY:
                        offset = 0
                        if len(device_tag.get("Args", [])) > 0:
                            offset = int(device_tag["Args"][0])
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
                        return pump_status_msg(raw_value, device_tag["Args"]), False
                    
                    case ConversionType.PUMP_STOPPED_MSG:
                        return pump_stopped_msg(raw_value, device_tag["Args"]), False
                    
                    case ConversionType.LAT_LONG:
                        return lat_long(raw_value), False
                    
                    case ConversionType.RIVER_COUNT:
                        return river_counts(raw_value), False
                    
                    case ConversionType.DPL_LAST_RUN:
                        ...# TODO: This requires historical values
                    
                    case _:
                        return None
                return None
                    
            
            converted_value = convert_value(conversion)
            if converted_value is None:
                continue # TODO: error handling for failed conversions
            converted_value_str, value_is_bool = converted_value
            
            if device_tag.get("Alarm", False) == True:
                if converted_value_str != '':
                    alarms.append(converted_value_str)
            else:
                if converted_value_str != '': # Don't show values that convert to an empty string
                    if device_tag.get("Message", False) == True:
                        messages.append(converted_value_str)
                    else:
                        values.append((device_tag["Name"], f"{converted_value_str} {device_tag.get('Units', '')}", value_is_bool))
        
        cards.append(device_card(
            name=f"{device.device_ref.name} {device.code}",
            alias=device.alias,
            last_updated=last_updated,
            values=values,
            alarms=alarms,
            messages=messages,
            show_bar=device.device_ref.has_bar,
            show_line=device.device_ref.has_line,
            show_gps=device.device_ref.has_gps,
            # show_edit=True
        ))
    return [dbc.Col(card, width=12, lg=6, xxl=4, className="pb-3") for card in cards]

def update_dashboard_children():
    return dbc.Row(update_dashboard(), id="dashboard-row")

def dashboard_layout():
    return dbc.Container([
        dcc.Loading(
            dbc.Container(update_dashboard_children(), id="dashboard-wrapper", fluid=True, className="p-0"),
            id = "loading-dashboard",
            type = "circle",
            delay_hide = 700,
            show_initially=False,
            target_components={"dashboard-wrapper": "children"}, # type: ignore # This is a valid TargetComponents dict, but the type checker doesn't like it for some reason
            style={"position": "absolute", "top": 0, "left": 0, "width": "100%", "height": "100%", "zIndex": 1050},
            color="#ffffff",
        ),
        dcc.Interval(id="refresh-interval", interval=60*1000, n_intervals=0)
    ], fluid=True, className="px-3 pb-2")
    
dash.register_page("dashboard", path="/", layout=dashboard_layout)

@callback(
    Output("dashboard-row", "children"),
    Input("refresh-interval", "n_intervals"),
    prevent_initial_call=True
)
def refresh_dashboard_silent(n_intervals):
    return update_dashboard()

@callback(
    Output("dashboard-wrapper", "children"),
    Output("refresh-interval", "interval"),
    Input("refresh-btn", "n_clicks"),
    prevent_initial_call=True
)
def refresh_dashboard_manual(n_clicks):
    return update_dashboard_children(), 60*1000 # Reset interval to 60 seconds on manual refresh