# This software is used for Datum 9390 GPS receiver and developed with assistance from Perplexity version pplx-70b-online
# - Many of the parse functions were written with the assistance of Perplexity AI version pplx-70b-online, including:
#   - Packet parsing logic
#   - Struct unpacking
#   - Error handling
#   - Comment Documentation assistance

import serial
import struct
from datetime import datetime, timedelta
import argparse
import sys

# Color codes for console output
WHITE = "\033[97m"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Constants for TSIP framing
DLE = 0x10  # Data Link Escape
ETX = 0x03  # End of Text

# Global debug flag
DEBUG = False

def send_tsip_packet(output, packet_id, data=b''):
    """Sends a TSIP command packet with proper DLE stuffing (serial only)."""
    if not isinstance(output, serial.Serial):
        print(f"{YELLOW}Warning: Sending packets is only supported for serial ports, not files{RESET}")
        return
    packet = bytearray([packet_id]) + bytearray(data)
    framed_packet = bytearray([DLE])
    for byte in packet:
        framed_packet.append(byte)
        if byte == DLE:
            framed_packet.append(DLE)  # Stuff an extra DLE
    framed_packet.extend([DLE, ETX])
    if DEBUG:
        print(f"{WHITE}Debug: Sending packet, ID=0x{packet_id:02X}, data={data.hex()}, framed={framed_packet.hex()}{RESET}")
    output.write(framed_packet)

def read_tsip_packet(input_source, buffer_queue=None):
    """Reads a single TSIP packet, ignoring bytes until a valid <DLE>...<DLE><ETX> pair is found."""
    if buffer_queue is None:
        buffer_queue = bytearray()
    packet_buffer = bytearray()
    raw_buffer = bytearray()
    state = 0  # 0: Looking for DLE, 1: Reading ID, 2: Reading data until DLE ETX

    while True:
        if buffer_queue:  # Process buffered data first
            byte = bytes([buffer_queue.pop(0)])
        else:
            if isinstance(input_source, serial.Serial):
                byte = input_source.read(1)
            else:  # File input
                byte = input_source.read(1)
                if not byte:  # End of file
                    if packet_buffer:
                        print(f"{YELLOW}Reached EOF with incomplete packet{RESET}")
                    return None
            if not byte:
                print(f"{YELLOW}Timeout or no data received{RESET}")
                return None

        b = byte[0]
        raw_buffer.append(b)

        if state == 0:  # Looking for start of packet (DLE)
            if b == DLE:
                state = 1  # Found potential start
            else:
                if DEBUG:
                    print(f"{WHITE}Debug: Skipping non-DLE byte: 0x{b:02X}{RESET}")
                continue  # Skip until DLE
        elif state == 1:  # Expecting packet ID after DLE
            if b == DLE:  # Double DLE, stay in state 1
                continue
            packet_buffer.append(b)  # Packet ID
            state = 2  # Move to reading data
        elif state == 2:  # Reading packet data
            if b == DLE:
                next_byte = input_source.read(1) if not buffer_queue else bytes([buffer_queue.pop(0)])
                if not next_byte:
                    print(f"{RED}Unexpected end of packet{RESET}")
                    return None
                next_byte = next_byte[0]
                raw_buffer.append(next_byte)
                if next_byte == ETX:  # End of packet
                    excess = raw_buffer[len(raw_buffer) - raw_buffer[::-1].index(DLE) - 1:]
                    if len(excess) > 2:
                        buffer_queue.extend(excess[2:])
                    if DEBUG:
                        print(f"{WHITE}Debug: Packet read, length={len(packet_buffer)}, data={packet_buffer.hex()}, raw={raw_buffer.hex()}, buffered={buffer_queue.hex()}{RESET}")
                    return bytes(packet_buffer)
                elif next_byte == DLE:  # DLE stuffing
                    packet_buffer.append(DLE)
                else:  # Treat as data
                    packet_buffer.append(DLE)
                    packet_buffer.append(next_byte)
            else:
                packet_buffer.append(b)

def parse_packet_40(packet_id, data):
    """Parses Almanac Data Packet (Packet ID: 0x40)."""
    try:
        if len(data) < 35:
            print(f"{RED}{datetime.now()} - Error: Insufficient data for Packet ID: 0x{packet_id:X}{RESET}")
            return
        print(f"{datetime.now()} - Report Packet: {BLUE}0x{packet_id:X}{RESET} - Almanac Data")
        offset = 0
        while offset + 35 <= len(data):
            prn = data[offset]
            gps_week = struct.unpack('>H', data[offset + 1:offset + 3])[0]
            sv_health = data[offset + 3]
            eccentricity = struct.unpack('>H', data[offset + 4:offset + 6])[0]
            ref_time = struct.unpack('>H', data[offset + 6:offset + 8])[0]
            inclination = struct.unpack('>H', data[offset + 8:offset + 10])[0]
            rate_of_ra = struct.unpack('>f', data[offset + 10:offset + 14])[0]
            semi_major_axis_root = struct.unpack('>f', data[offset + 14:offset + 18])[0]
            omega = struct.unpack('>f', data[offset + 18:offset + 22])[0]
            asc_node_longitude = struct.unpack('>f', data[offset + 22:offset + 26])[0]
            mean_anomaly = struct.unpack('>f', data[offset + 26:offset + 30])[0]
            af0 = struct.unpack('>f', data[offset + 30:offset + 34])[0]
            print(f" Satellite PRN={GREEN}{prn}{RESET}, GPS Week={GREEN}{gps_week}{RESET}, SV Health={GREEN}{sv_health}{RESET}")
            print(f" Eccentricity={GREEN}{eccentricity}{RESET}, Reference Time={GREEN}{ref_time}{RESET}, Inclination={GREEN}{inclination}{RESET}")
            print(f" Rate of Right Ascension={GREEN}{rate_of_ra:.6f}{RESET}, Semi-Major Axis Root={GREEN}{semi_major_axis_root:.6f}{RESET}")
            print(f" Omega={GREEN}{omega:.6f}{RESET}, Longitude of Ascension Node={GREEN}{asc_node_longitude:.6f}{RESET}")
            print(f" Mean Anomaly={GREEN}{mean_anomaly:.6f}{RESET}, Clock Parameter af0={GREEN}{af0:.6f}{RESET}")
            offset += 35
    except Exception as e:
        print(f"{RED}Error parsing Almanac Data packet 0x{packet_id:X}: {e}, data={data.hex()}{RESET}")

def parse_packet_41(packet_id, data):
    """Parses GPS Time (Packet ID 0x41)."""
    if len(data) < 10:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for GPS Time{RESET}")
        return
    try:
        time_of_week, extended_gps_week, utc_offset = struct.unpack('>fHf', data[:10])
        gps_week = extended_gps_week
        current_gps_week = 2357  # Approximate as of March 2025
        if gps_week < (current_gps_week - 1024):
            gps_week += 2048  # Adjust for rollovers
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: GPS Time{RESET}")
        print(f"{WHITE} Time of Week:{RESET} {GREEN}{time_of_week:.3f} seconds{RESET}")
        print(f"{WHITE} Extended GPS Week:{RESET} {GREEN}{gps_week}{RESET}")
        print(f"{WHITE} UTC Offset:{RESET} {GREEN}{utc_offset} seconds{RESET}")
        gps_epoch = datetime(1980, 1, 6)
        current_gps_time = gps_epoch + timedelta(weeks=gps_week, seconds=time_of_week)
        current_utc_time = current_gps_time - timedelta(seconds=int(utc_offset))
        print(f"{WHITE} Current UTC Time:{RESET} {GREEN}{current_utc_time}{RESET}")
    except struct.error as e:
        print(f"{RED}Error parsing GPS Time packet: {e}{RESET}")

def parse_packet_43(packet_id, data):
    """Parses Velocity Fix (XYZ ECEF) (Packet ID 0x43)."""
    if len(data) < 12:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for Velocity Fix{RESET}")
        return
    try:
        x_velocity, y_velocity, z_velocity = struct.unpack('>fff', data[:12])
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Velocity Fix (XYZ ECEF){RESET}")
        print(f"{WHITE} X Velocity:{RESET} {GREEN}{x_velocity:.3f} m/s{RESET}")
        print(f"{WHITE} Y Velocity:{RESET} {GREEN}{y_velocity:.3f} m/s{RESET}")
        print(f"{WHITE} Z Velocity:{RESET} {GREEN}{z_velocity:.3f} m/s{RESET}")
    except struct.error as e:
        print(f"{RED}Error parsing Velocity Fix packet: {e}{RESET}")

def parse_packet_44(packet_id, data):
    """Parses Non-Overdetermined Satellite Selection Report (Packet ID 0x44)."""
    expected_length = 21
    if len(data) < expected_length:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data, got {len(data)} bytes{RESET}")
        return
    if len(data) > expected_length:
        print(f"{YELLOW}Warning: Packet 0x44 length {len(data)} exceeds expected {expected_length} bytes, trimming excess{RESET}")
        data = data[:expected_length]
    if DEBUG:
        print(f"{WHITE}Debug: Raw data length={len(data)}, data={data.hex()}{RESET}")
        print(f"{WHITE}Debug: DOP bytes={data[5:21].hex()}{RESET}")
    MODE_MEANINGS = {
        1: "Auto, 1-satellite, 0D",
        3: "Auto, 3-satellite, 2D",
        4: "Auto, 4-satellite, 3D",
        11: "Manual, 1-satellite, 0D",
        13: "Manual, 3-satellite, 2D",
        14: "Manual, 4-satellite, 3D"
    }
    try:
        mode = data[0]
        sv1, sv2, sv3, sv4 = data[1:5]
        pdop, hdop, vdop, tdop = struct.unpack('>ffff', data[5:21])
        dop_display = lambda x: f"{x:.2e}" if abs(x) > 1000 or abs(x) < 0.01 else f"{x:.2f}"
        pdop_str = dop_display(pdop)
        hdop_str = dop_display(hdop)
        vdop_str = dop_display(vdop)
        tdop_str = dop_display(tdop)
        if any(abs(dop) > 1000 for dop in [pdop, hdop, vdop, tdop]):
            print(f"{YELLOW}Warning: Invalid DOP value detected: PDOP={pdop}, HDOP={hdop}, VDOP={vdop}, TDOP={tdop}{RESET}")
        active_sats = sum(1 for sv in [sv1, sv2, sv3, sv4] if sv != 0)
        if mode == 4 and active_sats < 4:
            print(f"{YELLOW}Warning: Mode indicates 4-satellite fix, but only {active_sats} satellites reported{RESET}")
        mode_description = MODE_MEANINGS.get(mode, "Unknown mode")
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Satellite Selection Report{RESET}")
        print(f"{WHITE} Mode:{RESET} {GREEN}{mode_description} ({mode:#02X}){RESET}")
        print(f"{WHITE} Satellites:{RESET} {GREEN}SV1={sv1}, SV2={sv2}, SV3={sv3}, SV4={sv4}{RESET}")
        print(f"{WHITE} PDOP:{RESET} {GREEN}{pdop_str}{RESET}")
        print(f"{WHITE} HDOP:{RESET} {GREEN}{hdop_str}{RESET}")
        print(f"{WHITE} VDOP:{RESET} {GREEN}{vdop_str}{RESET}")
        print(f"{WHITE} TDOP:{RESET} {GREEN}{tdop_str}{RESET}")
    except struct.error as e:
        print(f"{RED}Error parsing Satellite Selection packet: {e}, data={data.hex()}{RESET}")

def parse_packet_45(packet_id, data):
    """Parses Receiver Firmware Information (Packet ID 0x45)."""
    if len(data) < 10:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for Firmware Information{RESET}")
        return
    major_version = data[0]
    minor_version = data[1]
    month = data[2]
    day = data[3]
    year = struct.unpack('>H', data[4:6])[0]
    product_id = struct.unpack('>I', data[6:10])[0]
    print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Receiver Firmware Information{RESET}")
    print(f"{WHITE} Firmware Version:{RESET} {GREEN}{major_version}.{minor_version}{RESET}")
    print(f"{WHITE} Date:{RESET} {GREEN}{year}-{month:02d}-{day:02d}{RESET}")
    print(f"{WHITE} Product ID:{RESET} {GREEN}{product_id}{RESET}")

def parse_packet_46(packet_id, data):
    """Parses Health (Packet ID 0x46)."""
    try:
        status_code = data[0]
        codes = {
            0x00: 'Doing position fixes',
            0x01: 'Do not have GPS time yet',
            0x03: 'PDOP is too high',
            0x08: 'No usable satellites',
            0x09: 'Only 1 usable satellite',
            0x0A: 'Only 2 usable satellites',
            0x0B: 'Only 3 usable satellites',
            0x0C: 'The chosen satellite is unusable'
        }
        desc = codes.get(status_code, "Unknown status code")
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Health Packet: Status Code={status_code:#02x}, Description={desc}{RESET}")
    except IndexError as e:
        print(f"{RED}Error parsing Health packet: {e}{RESET}")

def parse_packet_47(packet_id, data):
    """Parses Signal Levels (Packet ID 0x47)."""
    if DEBUG:
        print(f"{WHITE}Debug: Raw data length={len(data)}, data={data.hex()}{RESET}")
    try:
        count = data[0]
        expected_length = 1 + count * 5
        if len(data) < expected_length:
            print(f"{RED}Incomplete signal level data, expected {expected_length} bytes, got {len(data)}{RESET}")
            return
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Signal Levels Packet: Number of Satellites={count}{RESET}")
        index = 1
        for i in range(count):
            prn, signal_level = struct.unpack(">Bf", data[index:index + 5])
            print(f"{WHITE} SV PRN={GREEN}{prn}{RESET}, Signal Level={GREEN}{signal_level:.2f}{RESET}")
            index += 5
    except struct.error as e:
        print(f"{RED}Error parsing Signal Levels packet: {e}{RESET}")

def parse_packet_48(packet_id, data):
    """Parses GPS System Message Report (Packet ID 0x48)."""
    if len(data) < 22:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for GPS System Message Report{RESET}")
        return
    try:
        message = data[:22].decode('ascii', errors='replace')
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: GPS System Message Report{RESET}")
        print(f"{WHITE} Message:{RESET} {GREEN}{message.strip()}{RESET}")
    except Exception as e:
        print(f"{RED}Error parsing GPS System Message packet: {e}{RESET}")

def parse_packet_49(packet_id, data):
    """Parses Almanac Health Page Report (Packet ID 0x49)."""
    if len(data) < 32:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for Almanac Health Report{RESET}")
        return
    try:
        health_status = {}
        healthy_count = 0
        unhealthy_count = 0
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Almanac Health Page Report{RESET}")
        print(f"{WHITE} Satellite | Status{RESET}")
        print(f"{WHITE}-------------------{RESET}")
        for sat_num in range(32):
            status_byte = data[sat_num]
            is_healthy = status_byte == 0
            health_status[sat_num + 1] = "Healthy" if is_healthy else "Unhealthy"
            if is_healthy:
                healthy_count += 1
            else:
                unhealthy_count += 1
            health_str = f"{GREEN}✅ Healthy{RESET}" if is_healthy else f"{RED}❌ Unhealthy (0x{status_byte:02X}){RESET}"
            print(f"{WHITE} SV{sat_num + 1:3} |{RESET} {health_str}")
        print(f"\n{WHITE}Summary:{RESET}")
        print(f"{WHITE} Healthy Satellites:{RESET} {GREEN}{healthy_count}{RESET}")
        print(f"{WHITE} Unhealthy Satellites:{RESET} {RED}{unhealthy_count}{RESET}")
    except IndexError as e:
        print(f"{RED}Error parsing Almanac Health Report: {e}{RESET}")

def parse_packet_4A(packet_id, data):
    """Parses Single Precision LLA Position Fix Report (Packet ID 0x4A)."""
    data_length = len(data)
    if data_length == 20 or data_length == 24:
        try:
            latitude, longitude, altitude, clock_bias, time_of_fix = struct.unpack('>fffff', data[:20])
            print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Single Precision LLA Position Fix Report{RESET}")
            print(f"{WHITE} Latitude:{RESET} {GREEN}{latitude:.6f} radians ({latitude * (180 / 3.141592653589793):.6f} degrees){RESET}")
            print(f"{WHITE} Longitude:{RESET} {GREEN}{longitude:.6f} radians ({longitude * (180 / 3.141592653589793):.6f} degrees){RESET}")
            print(f"{WHITE} Altitude:{RESET} {GREEN}{altitude:.2f} meters{RESET}")
            print(f"{WHITE} Clock Bias:{RESET} {GREEN}{clock_bias:.2f} meters{RESET}")
            print(f"{WHITE} Time of Fix:{RESET} {GREEN}{time_of_fix:.3f} seconds{RESET}")
        except struct.error as e:
            print(f"{RED}Error parsing Single Precision LLA Position Fix Report: {e}{RESET}")

def parse_packet_4B(packet_id, data):
    """Parses Machine/Code ID and Additional Status Report (Packet ID 0x4B)."""
    if len(data) < 3:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for Additional Status Report{RESET}")
        return
    machine_id = data[0]
    status_flags_1 = data[1]
    status_flags_2 = data[2]
    battery_fault = (status_flags_1 >> 1) & 0x01
    acknowledged_status = (status_flags_1 >> 3) & 0x01
    tsip_superpackets_fault = status_flags_2 & 0x01
    receiver_reset_fault = (status_flags_2 >> 1) & 0x01
    almanac_fault = (status_flags_2 >> 2) & 0x01
    adc_fault = (status_flags_2 >> 3) & 0x01
    print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Machine/Code ID and Additional Status Report{RESET}")
    print(f"{WHITE} Machine ID:{RESET} {GREEN}{machine_id:#02X}{RESET}")
    print(f"{WHITE} Status Flags:{RESET}")
    battery_fault_str = f"{RED}Yes{RESET}" if battery_fault else f"{GREEN}No{RESET}"
    print(f"{WHITE} Battery-powered time clock fault:{RESET} {battery_fault_str}")
    acknowledged_status_str = f"{GREEN}Yes{RESET}" if acknowledged_status else f"{RED}No{RESET}"
    print(f"{WHITE} Acknowledged status:{RESET} {acknowledged_status_str}")
    tsip_superpackets_fault_str = f"{RED}Yes{RESET}" if tsip_superpackets_fault else f"{GREEN}No{RESET}"
    print(f"{WHITE} TSIP superpackets fault:{RESET} {tsip_superpackets_fault_str}")
    receiver_reset_fault_str = f"{RED}Yes{RESET}" if receiver_reset_fault else f"{GREEN}No{RESET}"
    print(f"{WHITE} Receiver reset fault:{RESET} {receiver_reset_fault_str}")
    almanac_fault_str = f"{RED}Yes{RESET}" if almanac_fault else f"{GREEN}No{RESET}"
    print(f"{WHITE} Almanac fault:{RESET} {almanac_fault_str}")
    adc_fault_str = f"{RED}Yes{RESET}" if adc_fault else f"{GREEN}No{RESET}"
    print(f"{WHITE} ADC fault:{RESET} {adc_fault_str}")

def parse_packet_54(packet_id, data):
    """Parses Altitude Hold Enable (Packet ID 0x54)."""
    if len(data) < 1:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for Altitude Hold Enable{RESET}")
        return
    try:
        altitude_hold = data[0]
        status = "Enabled" if altitude_hold else "Disabled"
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Altitude Hold Enable{RESET}")
        print(f"{WHITE} Altitude Hold:{RESET} {GREEN}{status}{RESET}")
    except IndexError as e:
        print(f"{RED}Error parsing Altitude Hold Enable packet: {e}{RESET}")

def parse_packet_55(packet_id, data):
    """Parses Throttle Percentage (Packet ID 0x55)."""
    if len(data) < 1:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for Throttle Percentage{RESET}")
        return
    try:
        throttle = data[0]
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Throttle Percentage{RESET}")
        print(f"{WHITE} Throttle Percentage:{RESET} {GREEN}{throttle}%{RESET}")
    except IndexError as e:
        print(f"{RED}Error parsing Throttle Percentage packet: {e}{RESET}")

def parse_packet_5B(packet_id, data):
    """Parses Satellite Ephemeris Status Report (Packet ID 0x5B)."""
    try:
        if len(data) < 16:
            print(f"{RED}Insufficient data for Satellite Ephemeris Status Report (Packet ID: 0x{packet_id:X}){RESET}")
            return
        sv_prn = data[0]
        collection_time = struct.unpack('>f', data[1:5])[0]
        health = data[5]
        iode = data[6]
        toe = struct.unpack('>f', data[7:11])[0]
        fit_interval_flag = data[11]
        ura = struct.unpack('>f', data[12:16])[0]
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Satellite Ephemeris Status Report{RESET}")
        print(f" SV PRN #: {GREEN}{sv_prn}{RESET}")
        print(f" Collection Time: {GREEN}{collection_time:.2f}{RESET} seconds")
        print(f" Health: {GREEN}{health}{RESET}")
        print(f" IODE: {GREEN}{iode}{RESET}")
        print(f" toe: {GREEN}{toe:.2f}{RESET} seconds")
        print(f" Fit Interval Flag: {GREEN}{fit_interval_flag}{RESET}")
        print(f" URA: {GREEN}{ura:.2f}{RESET} meters")
    except Exception as e:
        print(f"{RED}Error parsing Satellite Ephemeris Status packet: {e}{RESET}")

def parse_packet_70(packet_id, data):
    """Parses Navigation Filter Configuration (Packet ID 0x70)."""
    if len(data) < 4:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for Navigation Filter Configuration{RESET}")
        return
    try:
        nav1, nav2 = struct.unpack(">HH", data[:4])
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Navigation Filter Configuration{RESET}")
        print(f"{WHITE} Nav 1:{RESET} {GREEN}{nav1}{RESET}")
        print(f"{WHITE} Nav 2:{RESET} {GREEN}{nav2}{RESET}")
    except struct.error as e:
        print(f"{RED}Error parsing Navigation Filter Configuration packet: {e}{RESET}")

def parse_packet_82(packet_id, data):
    """Parses Output Rate Control (Packet ID 0x82)."""
    if len(data) < 2:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Insufficient data for Output Rate Control{RESET}")
        return
    try:
        rate_control1, rate_control2 = struct.unpack(">BB", data[:2])
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Output Rate Control{RESET}")
        print(f"{WHITE} Rate Control 1:{RESET} {GREEN}{rate_control1}{RESET}")
        print(f"{WHITE} Rate Control 2:{RESET} {GREEN}{rate_control2}{RESET}")
    except struct.error as e:
        print(f"{RED}Error parsing Output Rate Control packet: {e}{RESET}")

def parse_tsip_packet(packet):
    """Parses a TSIP packet based on its ID."""
    if len(packet) < 1:
        print(f"{RED}Invalid packet: too short{RESET}")
        return

    packet_id = packet[0]
    data = packet[1:]

    parsers = {
        0x40: parse_packet_40,
        0x41: parse_packet_41,
        0x43: parse_packet_43,
        0x44: parse_packet_44,
        0x45: parse_packet_45,
        0x46: parse_packet_46,
        0x47: parse_packet_47,
        0x48: parse_packet_48,
        0x49: parse_packet_49,
        0x4A: parse_packet_4A,
        0x4B: parse_packet_4B,
        0x54: parse_packet_54,
        0x55: parse_packet_55,
        0x5B: parse_packet_5B,
        0x70: parse_packet_70,
        0x82: parse_packet_82,
    }

    parser_function = parsers.get(packet_id)
    if parser_function:
        parser_function(packet_id, data)
    else:
        print(f"{WHITE}Report Packet: {BLUE}0x{packet_id:02X}{RESET}: Unknown packet, Data: {data.hex()}{RESET}")

def main():
    """Main function to read and parse TSIP packets from either serial port or file."""
    parser = argparse.ArgumentParser(description="Read and parse TSIP packets from a serial port or binary file.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", "--port", help="Serial port to connect to (e.g., COM3 or /dev/ttyUSB0)")
    group.add_argument("-f", "--file", help="Binary file containing TSIP packets (use '-' for stdin)")
    parser.add_argument("-b", "--baudrate", type=int, default=9600, help="Baud rate for serial communication (default: 9600, ignored for file input)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    global DEBUG
    DEBUG = args.debug

    input_source = None
    buffer_queue = bytearray()

    try:
        if args.port:
            input_source = serial.Serial(args.port, args.baudrate, timeout=5)
            print(f"{WHITE}Connected to serial port {args.port} at {args.baudrate} baud{RESET}")
        elif args.file:
            if args.file == '-':
                input_source = sys.stdin.buffer  # Read binary from stdin
                print(f"{WHITE}Reading TSIP packets from stdin{RESET}")
            else:
                input_source = open(args.file, 'rb')
                print(f"{WHITE}Reading TSIP packets from file {args.file}{RESET}")

        while True:
            packet = read_tsip_packet(input_source, buffer_queue)
            if packet:
                parse_tsip_packet(packet)
            elif args.file and not args.port:  # EOF for file input
                break

    except serial.SerialException as e:
        print(f"{RED}Error: Could not open serial port: {e}{RESET}")
    except FileNotFoundError as e:
        print(f"{RED}Error: Could not open file: {e}{RESET}")
    except KeyboardInterrupt:
        print(f"{WHITE}Exiting program{RESET}")
    finally:
        if args.port and input_source and isinstance(input_source, serial.Serial):
            input_source.close()
        elif args.file and args.file != '-' and input_source and hasattr(input_source, 'close'):
            input_source.close()

if __name__ == "__main__":
    main()
