# This is cobbled together to parse Trimble (TSIP) serial data from GPS Datum 9390-55165 receiver.
# Had to fudge the 0x41 to add 2048 to the GPS week because of the missing epoch rollover
# This software was developed with assistance from Perplexity AI (https://www.perplexity.ai), accessed on March 13, 2025.

import serial
import struct
from datetime import datetime, timedelta

# Constants for TSIP framing
DLE = 0x10  # Data Link Escape
ETX = 0x03  # End of Text

def read_tsip_packet(serial_port):
    """Reads a single TSIP packet from the serial port."""
    buffer = bytearray()
    state = 0  # 0: waiting for DLE, 1: waiting for ID, 2: reading data

    while True:
        byte = serial_port.read(1)
        if not byte:
            print("Timeout or no data received")
            return None  # Timeout or no data

        b = byte[0]

        if state == 0:  # Waiting for DLE
            if b == 0x10:  # Start of packet
                state = 1
        elif state == 1:  # Waiting for ID
            if b == 0x10:  # Escaped DLE, stay in this state
                continue
            buffer.append(b)  # Packet ID
            state = 2
        elif state == 2:  # Reading data
            if b == 0x10:  # Possible end of packet
                next_byte = serial_port.read(1)
                if not next_byte:
                    print("Unexpected end of packet")
                    return None
                next_byte = next_byte[0]
                if next_byte == 0x03:  # End of packet
                    return bytes(buffer)  # Return parsed packet
                elif next_byte == 0x10:  # Escaped DLE
                    buffer.append(0x10)
                else:
                    buffer.append(0x10)
                    buffer.append(next_byte)
            else:
                buffer.append(b)
 

def parse_tsip_packet(packet):
    """Parses a TSIP packet based on its ID."""
    if len(packet) < 1:
        print("Invalid packet: too short")
        return

    packet_id = packet[0]
    data = packet[1:]

    parsers = {
        0x40: parse_packet_40,
        0x41: parse_gps_time,
        0x43: parse_packet_43,
        0x44: parse_satellite_selection,
        0x45: parse_firmware_info,
        0x46: parse_health,
        0x47: parse_signal_levels,
        0x48: parse_packet_48, 
        0x49: parse_almanac_health, 
        0x4A: parse_packet_4A,
        0x4B: parse_additional_status,
        0x54: parse_packet_54,
        0x55: parse_packet_55,
        0x5B: parse_sat_health_status,
        0x70: parse_POS_Filter,  
        0x82: parse_packet_82,
    }

    parser_function = parsers.get(packet_id)
    if parser_function:
        parser_function(packet_id, data)
    else:
        print(f"Report Packet: 0x{packet_id:02X}: Unknown packet, Data: {data.hex()}")

def parse_packet_40(packet_id, data):
    """Parses TSIP Report Packet 0x40: Almanac Data for Single Satellite."""
    
    # Check if the data length is sufficient
    if len(data) < 39:  # Minimum required length based on Table 3-5
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for Almanac Data")
        return

    try:
        # Unpack the almanac data according to Table 3-5
        satellite, t_zc, week_number, eccentricity, t_oa, i_o, omega_dot, sqrt_a, omega_o, omega, mo = struct.unpack('>BfHfffffff', data[:39])
        
        # Print parsed information
        print(f"Report Packet: 0x{packet_id:02X}: Almanac Data for Single Satellite")
        print(f"  Satellite PRN: {satellite} (1-32)")
        print(f"  T_zc (Z-count time): {t_zc:.2f} seconds")
        print(f"  Week Number: {week_number} weeks")
        print(f"  Eccentricity: {eccentricity:.6f} (dimensionless)")
        print(f"  T_oa (Time of Almanac): {t_oa:.2f} seconds")
        print(f"  i_o (Inclination Angle): {i_o:.6f} radians")
        print(f"  OMEGA_dot (Rate of Right Ascension): {omega_dot:.6f} radians/sec")
        print(f"  Square Root of Semi-Major Axis (sqrt(A)): {sqrt_a:.6f} meters^(1/2)")
        print(f"  OMEGA_o (Longitude of Ascending Node): {omega_o:.6f} radians")
        print(f"  Omega (Argument of Perigee): {omega:.6f} radians")
        print(f"  Mo (Mean Anomaly): {mo:.6f} radians")

        # Return parsed data as a dictionary
        return {
            "packet_id": packet_id,
            "satellite_prn": satellite,
            "t_zc": t_zc,
            "week_number": week_number,
            "eccentricity": eccentricity,
            "t_oa": t_oa,
            "i_o": i_o,
            "omega_dot": omega_dot,
            "sqrt_a": sqrt_a,
            "omega_o": omega_o,
            "omega": omega,
            "mo": mo
        }

    except struct.error as e:
        print(f"Error parsing Almanac Data packet 0x40: {e}")


def parse_gps_time(packet_id, data):
    """Parses GPS Time (Packet ID 0x41) and handles week rollovers."""
    if len(data) < 10:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for GPS Time")
        return
    
    try:
        # Unpack GPS time fields
        time_of_week, extended_gps_week, utc_offset = struct.unpack('>fHf', data[:10])
        
        # Handle GPS week rollovers
        gps_week = extended_gps_week
        current_gps_week = 2357  # Approximate current GPS week as of March 2025
        if gps_week < (current_gps_week - 1024):  # Adjust for rollover
            gps_week += 2048 #Adjust for two missing epochs since GPS epoch (January 6, 1980) 
        
        # Display parsed information
        print(f"Report Packet: 0x{packet_id:02X}: GPS Time")
        print(f"  Time of Week: {time_of_week:.3f} seconds")
        print(f"  Extended GPS Week: {gps_week}")
        print(f"  UTC Offset: {utc_offset} seconds")  # Display UTC offset as an integer
        
        # Calculate current UTC time
        gps_epoch = datetime(1980, 1, 6)  # GPS epoch start date
        current_gps_time = gps_epoch + timedelta(weeks=gps_week, seconds=time_of_week)
        current_utc_time = current_gps_time - timedelta(seconds=int(utc_offset))
        
        # Display calculated UTC time
        print(f"  Current UTC Time: {current_utc_time}")
    except struct.error as e:
        print(f"Error parsing GPS Time packet: {e}")


def parse_packet_43(packet_id, data):
    """Parses TSIP Report Packet 0x43: Velocity Fix (XYZ ECEF)."""
    if len(data) < 12:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for Velocity Fix")
        return

    try:
        # Unpack the X, Y, Z velocities
        x_velocity, y_velocity, z_velocity = struct.unpack('>fff', data[:12])

        # Print parsed information
        print(f"Report Packet: 0x{packet_id:02X}: Velocity Fix (XYZ ECEF)")
        print(f"  X Velocity: {x_velocity:.3f} m/s")
        print(f"  Y Velocity: {y_velocity:.3f} m/s")
        print(f"  Z Velocity: {z_velocity:.3f} m/s")
    except struct.error as e:
        print(f"Error parsing Velocity Fix packet: {e}")


def parse_satellite_selection(packet_id, data):
    """Parses Non-Overdetermined Satellite Selection Report (Packet ID 0x44)."""
    
    # Check data length
    if len(data) < 21:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for Satellite Selection Report")
        return
    
    # Define mode meanings
    MODE_MEANINGS = {
        1: "Auto, 1-satellite, 0D",
        3: "Auto, 3-satellite, 2D",
        4: "Auto, 4-satellite, 3D",
        11: "Manual, 1-satellite, 0D",
        13: "Manual, 3-satellite, 2D",
        14: "Manual, 4-satellite, 3D"
    }

    try:
        # Unpack data
        mode = data[0]
        sv1, sv2, sv3, sv4 = data[1:5]
        pdop, hdop, vdop, tdop = struct.unpack('>ffff', data[5:21])

        # Interpret mode
        mode_description = MODE_MEANINGS.get(mode, "Unknown mode")

        # Print parsed information
        print(f"Report Packet: 0x{packet_id:02X}: Satellite Selection Report")
        print(f"  Mode: {mode_description} ({mode:#02X})")
        print(f"  Satellites: SV1={sv1}, SV2={sv2}, SV3={sv3}, SV4={sv4}")
        print(f"  PDOP: {pdop:.2f}")
        print(f"  HDOP: {hdop:.2f}")
        print(f"  VDOP: {vdop:.2f}")
        print(f"  TDOP: {tdop:.2f}")

        # Return parsed data as dictionary
        return {
            "packet_id": packet_id,
            "mode": mode_description,
            "satellites": [sv1, sv2, sv3, sv4],
            "pdop": pdop,
            "hdop": hdop,
            "vdop": vdop,
            "tdop": tdop
        }

    except struct.error as e:
        print(f"Error parsing Satellite Selection packet: {e}")



def parse_firmware_info(packet_id, data):
    """Parses Receiver Firmware Information (Packet ID 0x45)."""
    if len(data) < 10:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for Firmware Information")
        return
    
    major_version = data[0]
    minor_version = data[1]
    month = data[2]
    day = data[3]
    year = struct.unpack('>H', data[4:6])[0]
    product_id = struct.unpack('>I', data[6:10])[0]
    
    print(f"Report Packet: 0x{packet_id:02X}: Receiver Firmware Information")
    print(f"  Firmware Version: {major_version}.{minor_version}")
    print(f"  Date: {year}-{month:02d}-{day:02d}")
    print(f"  Product ID: {product_id}")

def parse_health(packet_id, data):
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
        print(f"Report Packet: 0x{packet_id:02X}: Health Packet: Status Code={status_code:#02x}, Description={desc}")
    except IndexError as e:
        print(f"Error parsing Health packet: {e}")

def parse_signal_levels(packet_id, data):
    """Parses Signal Levels (Packet ID 0x47)."""
    try:
        count = data[0]
        print(f"Report Packet: 0x{packet_id:02X}: Signal Levels Packet: Number of Satellites={count}")
        index = 1
        for i in range(count):
            if index + 5 > len(data):
                print("Incomplete signal level data")
                break
            prn, signal_level = struct.unpack(">Bf", data[index:index + 5])
            print(f"  SV PRN={prn}, Signal Level={signal_level:.2f}")
            index += 5
    except struct.error as e:
        print(f"Error parsing Signal Levels packet: {e}")

def parse_packet_48(packet_id, data):
    """Parses TSIP Report Packet 0x48: GPS System Message Report."""
    
    # Check if the data length is sufficient
    if len(data) < 22:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for GPS System Message Report")
        return

    try:
        # Extract the 22-byte ASCII message
        message = data[:22].decode('ascii', errors='replace')  # Decode as ASCII, replacing invalid characters
        
        # Print the parsed information
        print(f"Report Packet: 0x{packet_id:02X}: GPS System Message Report")
        print(f"  Message: {message.strip()}")  # Strip any trailing whitespace or null characters
        
        # Return the parsed message as a dictionary
        return {
            "packet_id": packet_id,
            "message": message.strip()
        }

    except Exception as e:
        print(f"Error parsing GPS System Message packet: {e}")


def parse_almanac_health(packet_id, data):
    """Parses TSIP Report Packet 0x49: Almanac Health Page Report."""
    if len(data) < 32:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for Almanac Health Report")
        return

    try:
        health_status = {}
        healthy_count = 0
        unhealthy_count = 0
        
        print(f"Report Packet: 0x{packet_id:02X}: Almanac Health Page Report")
        print(" Satellite | Status")
        print("-------------------")
        
        for sat_num in range(32):
            status_byte = data[sat_num]
            is_healthy = status_byte == 0
            health_status[sat_num + 1] = "Healthy" if is_healthy else "Unhealthy"
            
            if is_healthy:
                healthy_count += 1
            else:
                unhealthy_count += 1
                
            print(f" SV{sat_num + 1:3}     | {'✅ Healthy' if is_healthy else '❌ Unhealthy (0x' + format(status_byte, '02X') + ')'}")

        print("\nSummary:")
        print(f" Healthy Satellites: {healthy_count}")
        print(f" Unhealthy Satellites: {unhealthy_count}")
        
        return {
            "packet_id": packet_id,
            "health_status": health_status,
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count
        }
        
    except IndexError as e:
        print(f"Error parsing Almanac Health Report: {e}")



def parse_packet_4A(packet_id, data):
    """Parses TSIP Report Packet 0x4A."""
    data_length = len(data)

    if data_length == 20 or data_length == 24:
        # Single Precision LLA Position Fix Report
        try:
            latitude, longitude, altitude, clock_bias, time_of_fix = struct.unpack('>fffff', data[:20])
            print(f"Report Packet: 0x{packet_id:02X}: Single Precision LLA Position Fix Report")
            print(f"  Latitude: {latitude:.6f} radians ({latitude * (180 / 3.141592653589793):.6f} degrees)")
            print(f"  Longitude: {longitude:.6f} radians ({longitude * (180 / 3.141592653589793):.6f} degrees)")
            print(f"  Altitude: {altitude:.2f} meters")
            print(f"  Clock Bias: {clock_bias:.2f} meters")
            print(f"  Time of Fix: {time_of_fix:.3f} seconds")
        except struct.error as e:
            print(f"Error parsing Single Precision LLA Position Fix Report: {e}")


def parse_additional_status(packet_id, data):
    """Parses Machine/Code ID and Additional Status Report (Packet ID 0x4B)."""
    if len(data) < 3:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for Additional Status Report")
        return

    # Extract fields
    machine_id = data[0]
    status_flags_1 = data[1]
    status_flags_2 = data[2]

    # Interpret Status Flags 1
    battery_fault = (status_flags_1 >> 1) & 0x01
    acknowledged_status = (status_flags_1 >> 3) & 0x01

    # Interpret Status Flags 2
    tsip_superpackets_fault = status_flags_2 & 0x01
    receiver_reset_fault = (status_flags_2 >> 1) & 0x01
    almanac_fault = (status_flags_2 >> 2) & 0x01
    adc_fault = (status_flags_2 >> 3) & 0x01

    # Print parsed information
    print(f"Report Packet: 0x{packet_id:02X}: Machine/Code ID and Additional Status Report")
    print(f"  Machine ID: {machine_id:#02X}")
    print(f"  Status Flags:")
    print(f"    Battery-powered time clock fault: {'Yes' if battery_fault else 'No'}")
    print(f"    Acknowledged status: {'Yes' if acknowledged_status else 'No'}")
    print(f"    TSIP Superpackets fault: {'Yes' if tsip_superpackets_fault else 'No'}")
    print(f"    Receiver reset fault: {'Yes' if receiver_reset_fault else 'No'}")
    print(f"    Almanac fault: {'Yes' if almanac_fault else 'No'}")
    print(f"    A-to-D converter fault: {'Yes' if adc_fault else 'No'}")

def parse_packet_54(packet_id, data):
    """Parses Report Packet 0x54: One Satellite Bias and Bias Rate Report."""
    
    if len(data) < 3:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for One Satellite Bias and Bias Rate Report")
        return
    
    try:
        bias = data[0]
        bias_rate = data[1]
        time_of_fix = data[2]

        print(f"Report Packet: 0x{packet_id:02X}: One Satellite Bias and Bias Rate Report")
        print(f"  Bias: {bias} (units unknown)")
        print(f"  Bias Rate: {bias_rate} (units unknown)")
        print(f"  Time of Fix: {time_of_fix} (possibly cyclic counter)")

        return {
            "packet_id": packet_id,
            "bias": bias,
            "bias_rate": bias_rate,
            "time_of_fix": time_of_fix
        }

    except IndexError as e:
        print(f"Error parsing One Satellite Bias and Bias Rate Report 0x54: {e}")

def parse_packet_55(packet_id, data):
    """Parses TSIP Report Packet 0x55: I/O Options Report."""
    if len(data) < 4:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for I/O Options Report")
        return

    position_flags = data[0]
    velocity_flags = data[1]
    timing_flags = data[2]
    auxiliary_flags = data[3]

    print(f"Report Packet: 0x{packet_id:02X}: I/O Options Report")
    
    # Parse Position Flags
    print("Position Flags:")
    print(f"  XYZ ECEF Position Report: {'ON' if position_flags & 0x01 else 'OFF'}")
    print(f"  LLA Position Report: {'ON' if position_flags & 0x02 else 'OFF'}")
    print(f"  LLA Altitude Output: {'WGS-84 MSL' if position_flags & 0x04 else 'WGS-84 HAE'}")
    print(f"  Altitude Input: {'WGS-84 MSL' if position_flags & 0x08 else 'WGS-84 HAE'}")
    print(f"  Position Data Precision: {'Double' if position_flags & 0x10 else 'Single'}")
    print(f"  Super Packet Output: {'ON' if position_flags & 0x20 else 'OFF'}")

    # Parse Velocity Flags
    print("Velocity Flags:")
    print(f"  XYZ ECEF Velocity Report: {'ON' if velocity_flags & 0x01 else 'OFF'}")
    print(f"  ENU Velocity Report: {'ON' if velocity_flags & 0x02 else 'OFF'}")

    # Parse Timing Flags
    print("Timing Flags:")
    print(f"  Time Type: {'UTC' if timing_flags & 0x01 else 'GPS Time'}")
    print(f"  Fix Computation Time: {'At Integer Second' if timing_flags & 0x02 else 'ASAP'}")
    print(f"  Fix Time Output: {'On Request' if timing_flags & 0x04 else 'When Computed'}")
    print(f"  Simultaneous Measurements: {'ON' if timing_flags & 0x08 else 'OFF'}")
    print(f"  Minimum Projection: {'ON' if timing_flags & 0x10 else 'OFF'}")

    # Parse Auxiliary Flags
    print("Auxiliary Flags:")
    print(f"  Measurement Output: {'ON' if auxiliary_flags & 0x01 else 'OFF'}")
    print(f"  Codephase Measurement Data Source: {'ON' if auxiliary_flags & 0x02 else 'OFF'}")
    print(f"  Additional Fix Status Report: {'ON' if auxiliary_flags & 0x04 else 'OFF'}")
    print(f"  Signal Level Output Units: {'dBHz' if auxiliary_flags & 0x08 else 'AMUs'}")


def parse_sat_health_status(packet_id, data):
    """Report Packet 0x5B Satellite Ephemeris Status Report"""
    if len(data) < 16:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for Satellite Ephemeris Status Report")
        return

    SV_PRN = data[0]  # Pseudorandom number of satellite
    Collection_time = struct.unpack('>f', data[1:5])[0]  # GPS time when Ephemeris data is collected
    Health = data[5]  # The 6-bit ephemeris health
    IODE = data[6]  # Issue of Data Ephemeris
    tSec = struct.unpack('>f', data[7:11])[0]  # Time of Ephemeris (seconds)
    Fit_Interval = data[11]  # Fit Interval Flag
    URA = struct.unpack('>f', data[12:16])[0]  # User Range Accuracy (meters)

    print(f"Report Packet: 0x{packet_id:02X}: Satellite Ephemeris Status Report")
    print(f"  SV PRN: {SV_PRN}")
    print(f"  Collection Time: {Collection_time:.3f} seconds")
    print(f"  Health: 0x{Health:02X}")
    print(f"  IODE: 0x{IODE:02X}")
    print(f"  Time of Ephemeris: {tSec:.3f} seconds")
    print(f"  Fit Interval Flag: 0x{Fit_Interval:02X}")
    print(f"  URA: {URA:.2f} meters")

def parse_POS_Filter(packet_id, data):
    """Parses Position/Velocity Filter Operation Report (Packet ID 0x70)."""
    if len(data) < 4:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for Position/Velocity Filter Operation Report")
        return

    try:
        dynamic_filter = data[0]
        static_filter = data[1]
        altitude_filter = data[2]
        reserved = data[3]

        print(f"Report Packet: 0x{packet_id:02X}: Position/Velocity Filter Operation Report")
        print(f"  Dynamic Filter Switch: 0x{dynamic_filter:02X}")
        print(f"  Static Filter Switch: 0x{static_filter:02X}")
        print(f"  Altitude Filter Switch: 0x{altitude_filter:02X}")
        print(f"  Reserved: 0x{reserved:02X}")

        return {
            "packet_id": packet_id,
            "dynamic_filter": dynamic_filter,
            "static_filter": static_filter,
            "altitude_filter": altitude_filter,
            "reserved": reserved
        }

    except IndexError as e:
        print(f"Error parsing Position/Velocity Filter Operation Report: {e}")


def parse_packet_82(packet_id, data):
    """Parses TSIP Report Packet 0x82: SBAS Correction Status."""
    if len(data) < 1:
        print(f"Report Packet: 0x{packet_id:02X}: Insufficient data for SBAS Correction Status")
        return

    sbas_status_bits = data[0]
    print(f"Report Packet: 0x{packet_id:02X}: SBAS Correction Status")
    print(f"  SBAS Status Bits: {sbas_status_bits:#08b}")

def main():
    # Open the serial port (adjust settings as needed)
    serial_port = serial.Serial(
    port="/dev/ttyUSB0",         # Replace with your serial port
    baudrate=19200,              # Set baud rate
    parity=serial.PARITY_NONE,   # No parity
    stopbits=serial.STOPBITS_ONE, # One stop bit
    bytesize=serial.EIGHTBITS,   # 8 data bits
    timeout=10.0,                # Timeout in seconds
    rtscts=True                  # Enable RTS/CTS hardware handshaking
    )
    print("Listening for TSIP packets...")
    
    try:
        while True:
            packet = read_tsip_packet(serial_port)
            if packet is not None:
                parse_tsip_packet(packet)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        serial_port.close()

if __name__ == "__main__":
    main()

