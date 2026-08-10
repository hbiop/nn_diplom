"""Signing and restricted deserialization for trusted application artifacts.

Pickle is not a data format: loading an arbitrary pickle can execute code. The
application therefore only loads artifacts that it created and signed, and
only permits the classes needed by the ML pipeline.
"""

import hashlib
import hmac
import io
import pickle
import struct

from django.conf import settings


_MAGIC = b"NNPK1"
_MAX_PAYLOAD_SIZE = 25 * 1024 * 1024

# Keep this list narrow. Add a class only when a legitimate artifact requires it.
_ALLOWED_GLOBALS = {
    ("builtins", name)
    for name in ("bool", "bytes", "complex", "dict", "float", "int", "list", "set", "slice", "str", "tuple")
} | {
    ("collections", "OrderedDict"),
    ("learning.data_preprocessor", "DataPreprocessor"),
    ("learning.neural_network", "NeuralNetwork"),
    ("numpy", "dtype"),
    ("numpy", "ndarray"),
    ("numpy", "ufunc"),
    ("numpy", "bool_"),
    ("numpy", "float16"),
    ("numpy", "float32"),
    ("numpy", "float64"),
    ("numpy", "int8"),
    ("numpy", "int16"),
    ("numpy", "int32"),
    ("numpy", "int64"),
    ("numpy", "uint8"),
    ("numpy", "uint16"),
    ("numpy", "uint32"),
    ("numpy", "uint64"),
    ("numpy.core.multiarray", "_reconstruct"),
    ("numpy._core.multiarray", "_reconstruct"),
    ("numpy.core.numeric", "_frombuffer"),
    ("numpy._core.numeric", "_frombuffer"),
    ("numpy.core.multiarray", "scalar"),
    ("numpy._core.multiarray", "scalar"),
    ("sklearn.compose._column_transformer", "ColumnTransformer"),
    ("sklearn.compose._column_transformer", "_RemainderColsList"),
    ("sklearn.pipeline", "Pipeline"),
    ("sklearn.impute._base", "SimpleImputer"),
    ("sklearn.preprocessing._data", "StandardScaler"),
    ("sklearn.preprocessing._encoders", "OneHotEncoder"),
}


def _sign(payload):
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"), payload, hashlib.sha256
    ).digest()


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) not in _ALLOWED_GLOBALS:
            raise pickle.UnpicklingError(f"Global is not allowed: {module}.{name}")
        return super().find_class(module, name)


def dumps(value):
    payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
    if len(payload) > _MAX_PAYLOAD_SIZE:
        raise ValueError("Serialized artifact is too large")
    return _MAGIC + struct.pack(">I", len(payload)) + _sign(payload) + payload


def loads(data):
    if not data or len(data) < len(_MAGIC) + 4 + 32:
        raise ValueError("Invalid serialized artifact")
    if len(data) > _MAX_PAYLOAD_SIZE + len(_MAGIC) + 4 + 32:
        raise ValueError("Serialized artifact is too large")

    stream = io.BytesIO(bytes(data))
    if stream.read(len(_MAGIC)) != _MAGIC:
        raise ValueError("Unsupported or unsigned serialized artifact")

    (payload_size,) = struct.unpack(">I", stream.read(4))
    signature = stream.read(32)
    payload = stream.read()
    if payload_size != len(payload) or not hmac.compare_digest(signature, _sign(payload)):
        raise ValueError("Serialized artifact signature is invalid")

    return RestrictedUnpickler(io.BytesIO(payload)).load()
