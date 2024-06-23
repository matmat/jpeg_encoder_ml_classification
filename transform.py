#!/usr/bin/env python3
import sys
import json

def process_scan_components(value, prefix, top_level_data):
    # order cs, td, ta is per the standard and not how they appear in the json structure
    return {f"{prefix}scan_components": "; ".join([f"{sc['cs']}:{sc['td']}:{sc['ta']}" for sc in value])}

def process_qs(value, prefix, top_level_data):
    qs_data = {}
    for i, qs in enumerate(value):
        pq, tq = qs['pq'], qs['tq']
        q_values = qs['q']
        q_values_hex = ''.join([f"{q:02x}" if pq == 0 else f"{q:04x}" for q in q_values])
        qs_key_prefix = f"{prefix}qs_{i}_"
        qs_data[f"{qs_key_prefix}pq"] = pq
        qs_data[f"{qs_key_prefix}tq"] = tq
        top_level_data[f"qtable_tq{tq}"] = q_values_hex
    return qs_data

def process_version(value, prefix, top_level_data):
    return {f"{prefix}version": f"{value['major']}.{value['minor']}"}

def process_frame_components(value, prefix, top_level_data):
    # order c, h, v, tq is per the standard and not how they appear in the json structure
    return {f"{prefix}frame_components": "; ".join([f"{fc['c']}:{fc['h']}:{fc['v']}:{fc['tq']}" for fc in value])}

def process_dht_hs(value, prefix, top_level_data):
    result = {}
    for m, hs in enumerate(value):
        tc = hs['tc']
        th = hs['th']
        lv = ''.join([f"{x:02x}" for x in hs['l']]) + ':' + ''.join([f"{x:02x}" for x in hs['v']])
        result[f"{prefix}hs_{m}_tc"] = tc
        result[f"{prefix}hs_{m}_th"] = th
        result[f"{prefix}hs_{m}_lv"] = lv
    return result

def process_json(input_json):
    frequencies = {}
    marker_data = {}
    top_level_data = {}
    sequence_markers = []

    special_processing = {
        'sos': {'scan_components': process_scan_components},
        'dqt': {'qs': process_qs},
        'app0': {'version': process_version},
        'sof0': {'frame_components': process_frame_components},
        'sof1': {'frame_components': process_frame_components},
        'sof2': {'frame_components': process_frame_components},
        'dht': {'hs': process_dht_hs}
    }

    for seg in input_json['segments']:
        if not isinstance(seg, dict):  # Skip non-dict items
            continue

        code = seg.get('code', 'unknown')
        sequence_markers.append(code)  # Track the sequence of markers
        frequencies[code] = frequencies.get(code, 0) + 1

        index = frequencies[code] - 1
        prefix = f"marker_{code}_{index}_"

        for key, value in seg.items():
            if key in ['code', 'prefix']:  # Skip 'code' and 'prefix' keys
                continue

            if key in special_processing.get(code, {}):
                processed_data = special_processing[code][key](value, prefix, top_level_data)
                marker_data.update(processed_data)
            else:
                marker_data[f"{prefix}{key}"] = value

    # Format sequence of markers as a string and place it at the beginning
    final_data = {'sequence_markers': "; ".join(sequence_markers)}

    # Include frequency data correctly labeled and right after sequence_markers
    for code, count in frequencies.items():
        final_data[f"frequency_{code}"] = count

    # Add remaining marker data and top-level data
    final_data.update(marker_data)
    final_data.update(top_level_data)

    return final_data

def main():
    input_json = json.load(sys.stdin)
    marker_data = process_json(input_json)

    all_keys = list(marker_data.keys())
    all_values = list(marker_data.values())

    sys.stdout.write("\t".join(all_keys) + "\n")
    sys.stdout.write("\t".join(str(v) for v in all_values) + "\n")

if __name__ == "__main__":
    main()
