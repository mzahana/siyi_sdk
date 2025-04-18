import struct

# Sample data from the response (hex string)
data_hex = "01010005d002b80b1e"

# Convert hex string to bytes
data_bytes = bytes.fromhex(data_hex)

# Unpack the binary data (using little-endian format '<')
# '<' = little-endian, B = uint8_t, H = uint16_t
stream_type, video_enc_type, res_l, res_h, bitrate, frame_rate = struct.unpack('<BBHHHB', data_bytes)

# Define codec string
codec_map = {1: "H264", 2: "H265"}
stream_type_map = {0: "Recording stream", 1: "Main stream", 2: "Sub stream (ZT30/ZT6 only)"}

# Output
print(f"Stream Type     : {stream_type} ({stream_type_map.get(stream_type, 'Unknown')})")
print(f"Video Enc Type  : {video_enc_type} ({codec_map.get(video_enc_type, 'Unknown')})")
print(f"Resolution      : {res_l} x {res_h}")
print(f"Video Bitrate   : {bitrate} Kbps")
print(f"Frame Rate      : {frame_rate} fps")