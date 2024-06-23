#!/usr/bin/env python3

import argparse
import sys
import logging




# fmt: off

# JPEG marker constants
M_STUF  = 0x00 # Stuffing, technically not a marker
M_MAGIC = 0xff # Padding, technically not a marker
M_TEM   = 0x01


M_SOF0  = 0xc0; M_SOF1  = 0xc1; M_SOF2  = 0xc2; M_SOF3  = 0xc3
M_DHT   = 0xc4; M_SOF5  = 0xc5; M_SOF6  = 0xc6; M_SOF7  = 0xc7
M_JPG   = 0xc8; M_SOF9  = 0xc9; M_SOF10 = 0xca; M_SOF11 = 0xcb
M_DAC   = 0xcc; M_SOF13 = 0xcd; M_SOF14 = 0xce; M_SOF15 = 0xcf

M_RST0  = 0xd0; M_RST1  = 0xd1; M_RST2  = 0xd2; M_RST3  = 0xd3
M_RST4  = 0xd4; M_RST5  = 0xd5; M_RST6  = 0xd6; M_RST7  = 0xd7
M_SOI   = 0xd8; M_EOI   = 0xd9; M_SOS   = 0xda; M_DQT   = 0xdb
M_DNL   = 0xdc; M_DRI   = 0xdd; M_DHP   = 0xde; M_EXP   = 0xdf

M_APP0  = 0xe0; M_APP1  = 0xe1; M_APP2  = 0xe2; M_APP3  = 0xe3
M_APP4  = 0xe4; M_APP5  = 0xe5; M_APP6  = 0xe6; M_APP7  = 0xe7
M_APP8  = 0xe8; M_APP9  = 0xe9; M_APP10 = 0xea; M_APP11 = 0xeb
M_APP12 = 0xec; M_APP13 = 0xed; M_APP14 = 0xee; M_APP15 = 0xef

M_JPG0  = 0xf0; M_JPG1  = 0xf1; M_JPG2  = 0xf2; M_JPG3  = 0xf3
M_JPG4  = 0xf4; M_JPG5  = 0xf5; M_JPG6  = 0xf6; M_JPG7  = 0xf7
M_JPG8  = 0xf8; M_JPG9  = 0xf9; M_JPG10 = 0xfa; M_JPG11 = 0xfb
M_JPG12 = 0xfc; M_JPG13 = 0xfd; M_COM   = 0xfe

jpeg_markers = {
    # 00-0F
                      M_TEM:   "TEM",

    # C0-CF
    M_SOF0:  "SOF0",  M_SOF1:  "SOF1",  M_SOF2:  "SOF2",  M_SOF3:  "SOF3",
    M_DHT:   "DHT",   M_SOF5:  "SOF5",  M_SOF6:  "SOF6",  M_SOF7:  "SOF7",
    M_JPG:   "JPG",   M_SOF9:  "SOF9",  M_SOF10: "SOF10", M_SOF11: "SOF11",
    M_DAC:   "DAC",   M_SOF13: "SOF13", M_SOF14: "SOF14", M_SOF15: "SOF15",

    # D0-DF
    M_RST0:  "RST0",  M_RST1:  "RST1",  M_RST2:  "RST2",  M_RST3:  "RST3",
    M_RST4:  "RST4",  M_RST5:  "RST5",  M_RST6:  "RST6",  M_RST7:  "RST7",
    M_SOI:   "SOI",   M_EOI:   "EOI",   M_SOS:   "SOS",   M_DQT:   "DQT",
    M_DNL:   "DNL",   M_DRI:   "DRI",   M_DHP:   "DHP",   M_EXP:   "EXP",

    # E0-EF
    M_APP0:  "APP0",  M_APP1:  "APP1",  M_APP2:  "APP2",  M_APP3:  "APP3",
    M_APP4:  "APP4",  M_APP5:  "APP5",  M_APP6:  "APP6",  M_APP7:  "APP7",
    M_APP8:  "APP8",  M_APP9:  "APP9",  M_APP10: "APP10", M_APP11: "APP11",
    M_APP12: "APP12", M_APP13: "APP13", M_APP14: "APP14", M_APP15: "APP15",

    # F0-FE
    M_JPG0:  "JPG0",  M_JPG1:  "JPG1",  M_JPG2:  "JPG2",  M_JPG3:  "JPG3",
    M_JPG4:  "JPG4",  M_JPG5:  "JPG5",  M_JPG6:  "JPG6",  M_JPG7:  "JPG7",
    M_JPG8:  "JPG8",  M_JPG8:  "JPG9",  M_JPG10: "JPG10", M_JPG11: "JPG11",
    M_JPG12: "JPG12", M_JPG13: "JPG13", M_COM:   "COM",
}

paramterless_jpeg_markers = [
    M_TEM,

    M_RST0,  M_RST1,  M_RST2,  M_RST3,
    M_RST4,  M_RST5,  M_RST6,  M_RST7,

    M_SOI,   M_EOI,
]


start_of_bitsream_markers = [
    M_RST0, M_RST1, M_RST2, M_RST3,
    M_RST4, M_RST5, M_RST6, M_RST7,

    M_SOS,
]

# fmt: on


def process_jpeg(input_file, output_file, remove_markers=None):
    if remove_markers is None:
        remove_markers = []

    in_ecs = False  # Indicates if we are inside an Entropy Coded Segment
    eoi_encountered = False  # Flag to indicate if EOI marker has been found

    while True:
        byte = input_file.read(1)
        if not byte:  # End of file
            break

        if byte == b'\xFF':
            file_position = input_file.tell() - 1
            # Skip any fill bytes (multiple 0xFF bytes)
            while True:
                next_byte = input_file.peek(1)[:1]  # Peek at the next byte without consuming it
                if next_byte != b'\xFF':
                    break  # Found a non-fill byte, break the fill byte skip loop
                logging.debug(f"Offset 0x{file_position:08X}: Padded byte (0xFF)")
                input_file.read(1)  # Consume the fill byte
                file_position += 1

            marker_byte = input_file.read(1)  # Read the next byte which should be the marker code
            if not marker_byte:
                break  # End of file immediately after fill bytes

            marker_code = marker_byte[0]
            marker_name = jpeg_markers.get(marker_code, "Unknown")
            if marker_code not in remove_markers and marker_name != "Unknown":
                if not eoi_encountered:  # Only print markers if EOI hasn't been encountered
                    print(f"[{marker_name}]", end='')

            # Check if this is the EOI marker
            if marker_code == M_EOI:
                eoi_encountered = True  # Set the flag
                output_file.write(b'\xFF' + marker_byte)  # Write the EOI marker to output before stopping
                logging.debug(f"Offset 0x{file_position:08X}: EOI marker encountered, stopping further output.")
                break  # Stop processing after writing EOI

            # Check if we should remove this marker
            if marker_code in remove_markers:
                logging.debug(f"Offset 0x{file_position:08X}: Removing marker {marker_name} (0xFF{marker_code:02X})")
                if marker_code not in paramterless_jpeg_markers:
                    length = int.from_bytes(input_file.read(2), 'big') - 2
                    input_file.read(length)  # Skip the segment
                continue  # Marker removed, skip further processing

            # Handle the ECS state if not removing the marker
            if in_ecs:
                # We are already in an ECS, look for end of segment markers or stuff bytes
                if marker_byte == b'\x00':  # Stuffed byte after 0xFF within ECS
                    logging.debug(f"Offset 0x{file_position:08X}: Stuffed byte (0xFF00)")
                    continue  # Just skip this byte

            # Write the marker to the output file
            if not eoi_encountered and marker_code not in paramterless_jpeg_markers:
                length_bytes = input_file.read(2)
                length = int.from_bytes(length_bytes, 'big') - 2
                segment = input_file.read(length)
                output_file.write(b'\xFF' + marker_byte + length_bytes + segment)
                logging.debug(f"Offset 0x{file_position:08X}: Marker {marker_name:<5} (0xFF{marker_code:02X}), segment length: {length + 2}")
            elif not eoi_encountered:
                output_file.write(b'\xFF' + marker_byte)
                logging.debug(f"Offset 0x{file_position:08X}: Marker {marker_name:<5} (0xFF{marker_code:02X})")

            # Mark entering ECS if this marker starts an ECS
            if marker_code == M_SOS or marker_code in range(M_RST0, M_RST7+1):
                in_ecs = True  # Marking the start of ECS after SOS or RSTn
                logging.debug(f"Offset 0x{input_file.tell():08X}: Entering ECS segment")



def valid_marker(marker):
    try:
        # Convert the marker string to its corresponding byte value
        marker_code = getattr(sys.modules[__name__], f'M_{marker}')
        if marker_code in jpeg_markers:
            return marker_code
    except AttributeError:
        raise argparse.ArgumentTypeError(f"{marker} is not a valid JPEG marker")
    return None  # Return None if the marker is not valid to filter out later.

def parse_markers(marker_list):
    """Parse and validate the comma-separated list of markers."""
    if not marker_list:
        return []
    markers = marker_list.split(',')
    marker_codes = [valid_marker(marker) for marker in markers if valid_marker(marker)]
    return marker_codes

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process a JPEG file, with options to modify markers.")
    parser.add_argument('-i', '--input', type=argparse.FileType('rb'), default=sys.stdin.buffer,
                        help="Input JPEG file path. If omitted, reads from stdin.")
    parser.add_argument('-o', '--output', type=argparse.FileType('wb'), default=sys.stdout.buffer,
                        help="Output JPEG file path. If omitted, writes to stdout.")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable debug output.")

    # Define a mutually exclusive group for markers
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-r', '--remove', type=parse_markers, default=[],
                       help="Comma-separated list of markers to remove. Specify marker names without the 'M_' prefix.")
    group.add_argument('-m', '--keep', type=parse_markers, default=[],
                       help="Comma-separated list of markers to keep. Specify marker names without the 'M_' prefix.")
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Set up logging based on the debug option
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Calculate the markers to remove based on the markers to keep
    if args.keep:
        all_markers = set(jpeg_markers.keys())
        remove_markers = list(all_markers - set(args.keep))
    else:
        remove_markers = args.remove


    # Since -r and -m are mutually exclusive, we pass only the relevant markers to process_jpeg
    # This example assumes process_jpeg handles the empty list appropriately if neither -r nor -m is specified
    process_jpeg(args.input, args.output, remove_markers)
    #print("")

if __name__ == "__main__":
    main()
