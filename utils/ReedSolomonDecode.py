# Initialization
from reedsolo import RSCodec, ReedSolomonError

rsc = RSCodec(2)  # 2 ecc symbols

# Encoding
encodedMsg = rsc.encode( bytearray( [ 0xFF, 0xF3 ] ) )

# Decoding (repairing)
rsc.decode( encodedMsg )[0]  # original
