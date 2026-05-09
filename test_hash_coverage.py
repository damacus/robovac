import pytest
from custom_components.robovac.tuyalocalapi import TuyaCipher

def test_hash_coverage():
    cipher = TuyaCipher("1234567890123456", (3, 3))
    val = cipher.hash(b"hello")
    print(val)

if __name__ == "__main__":
    test_hash_coverage()
