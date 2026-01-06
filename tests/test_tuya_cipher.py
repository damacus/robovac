"""Tests for TuyaCipher HMAC-SHA256 implementation."""

import pytest
from custom_components.robovac.tuyalocalapi import TuyaCipher


class TestTuyaCipherHMAC:
    """Test HMAC-SHA256 functionality for Protocol 3.4."""

    @pytest.fixture
    def cipher_v34(self) -> TuyaCipher:
        """Create a TuyaCipher instance for protocol 3.4."""
        return TuyaCipher("1234567890123456", (3, 4))

    @pytest.fixture
    def cipher_v33(self) -> TuyaCipher:
        """Create a TuyaCipher instance for protocol 3.3."""
        return TuyaCipher("1234567890123456", (3, 3))

    def test_hmac_sha256_returns_32_bytes(self, cipher_v34: TuyaCipher) -> None:
        """HMAC-SHA256 should return a 32-byte digest."""
        data = b"test data for hmac"
        result = cipher_v34.hmac_sha256(data)
        assert len(result) == 32

    def test_hmac_sha256_deterministic(self, cipher_v34: TuyaCipher) -> None:
        """Same data should produce same HMAC."""
        data = b"test data for hmac"
        result1 = cipher_v34.hmac_sha256(data)
        result2 = cipher_v34.hmac_sha256(data)
        assert result1 == result2

    def test_hmac_sha256_different_data_different_hash(
        self, cipher_v34: TuyaCipher
    ) -> None:
        """Different data should produce different HMAC."""
        result1 = cipher_v34.hmac_sha256(b"data1")
        result2 = cipher_v34.hmac_sha256(b"data2")
        assert result1 != result2

    def test_hmac_sha256_different_keys_different_hash(self) -> None:
        """Different keys should produce different HMAC for same data."""
        cipher1 = TuyaCipher("1234567890123456", (3, 4))
        cipher2 = TuyaCipher("6543210987654321", (3, 4))
        data = b"test data"
        result1 = cipher1.hmac_sha256(data)
        result2 = cipher2.hmac_sha256(data)
        assert result1 != result2

    def test_verify_hmac_valid(self, cipher_v34: TuyaCipher) -> None:
        """verify_hmac should return True for valid HMAC."""
        data = b"test data for verification"
        hmac = cipher_v34.hmac_sha256(data)
        assert cipher_v34.verify_hmac(data, hmac) is True

    def test_verify_hmac_invalid(self, cipher_v34: TuyaCipher) -> None:
        """verify_hmac should return False for invalid HMAC."""
        data = b"test data for verification"
        invalid_hmac = b"\x00" * 32
        assert cipher_v34.verify_hmac(data, invalid_hmac) is False

    def test_verify_hmac_wrong_data(self, cipher_v34: TuyaCipher) -> None:
        """verify_hmac should return False when data doesn't match HMAC."""
        original_data = b"original data"
        hmac = cipher_v34.hmac_sha256(original_data)
        modified_data = b"modified data"
        assert cipher_v34.verify_hmac(modified_data, hmac) is False

    def test_verify_hmac_empty_data(self, cipher_v34: TuyaCipher) -> None:
        """verify_hmac should work with empty data."""
        data = b""
        hmac = cipher_v34.hmac_sha256(data)
        assert cipher_v34.verify_hmac(data, hmac) is True

    def test_hmac_sha256_with_binary_data(self, cipher_v34: TuyaCipher) -> None:
        """HMAC should work with binary data containing null bytes."""
        data = b"\x00\x01\x02\xff\xfe\xfd"
        result = cipher_v34.hmac_sha256(data)
        assert len(result) == 32
        assert cipher_v34.verify_hmac(data, result) is True


class TestTuyaCipherDecrypt:
    """Test decrypt method edge cases."""

    @pytest.fixture
    def cipher(self) -> TuyaCipher:
        """Create a TuyaCipher instance."""
        return TuyaCipher("1234567890123456", (3, 3))

    def test_decrypt_unencrypted_json(self, cipher: TuyaCipher) -> None:
        """Decrypt should return unencrypted JSON data as-is."""
        json_data = b'{"dps":{"1":true}}'
        result = cipher.decrypt(0, json_data)
        assert result == json_data

    def test_decrypt_unencrypted_json_with_prefix(self, cipher: TuyaCipher) -> None:
        """Decrypt should detect JSON even with curly brace start."""
        json_data = b'{"status":"ok"}'
        result = cipher.decrypt(0, json_data)
        assert result == json_data

    def test_decrypt_valid_encrypted_data(self, cipher: TuyaCipher) -> None:
        """Decrypt should properly decrypt valid AES-encrypted data."""
        plaintext = b'{"dps":{"1":true}}'
        encrypted = cipher.encrypt(0, plaintext)
        decrypted = cipher.decrypt(0, encrypted)
        assert decrypted == plaintext

    def test_decrypt_invalid_length_raises_error(self, cipher: TuyaCipher) -> None:
        """Decrypt should raise ValueError for invalid data length."""
        invalid_data = b"\x00" * 17
        with pytest.raises(ValueError, match="Invalid encrypted data length"):
            cipher.decrypt(0, invalid_data)

    def test_decrypt_pkcs7_unpadding_failure(self, cipher: TuyaCipher) -> None:
        """Decrypt should return raw data when PKCS7 unpadding fails."""
        corrupted_data = b"\x00" * 16
        result = cipher.decrypt(0, corrupted_data)
        assert len(result) == 16
