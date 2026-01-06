"""Tests for Protocol 3.5 GCM cipher implementation."""

import pytest
from custom_components.robovac.tuyalocalapi import TuyaCipher


class TestProtocol35Cipher:
    """Test Protocol 3.5 AES-GCM cipher functionality."""

    @pytest.fixture
    def cipher_v35(self) -> TuyaCipher:
        """Create a Protocol 3.5 cipher instance."""
        return TuyaCipher("abcdefghijklmnop", (3, 5))

    @pytest.fixture
    def cipher_v34(self) -> TuyaCipher:
        """Create a Protocol 3.4 cipher instance for comparison."""
        return TuyaCipher("abcdefghijklmnop", (3, 4))

    def test_cipher_version_is_stored(self, cipher_v35: TuyaCipher) -> None:
        """Cipher stores the protocol version correctly."""
        assert cipher_v35.version == (3, 5)

    def test_v35_uses_gcm_mode(self, cipher_v35: TuyaCipher) -> None:
        """Protocol 3.5 should use GCM mode, not ECB."""
        assert hasattr(cipher_v35, 'is_gcm_mode')
        assert cipher_v35.is_gcm_mode is True

    def test_v34_uses_ecb_mode(self, cipher_v34: TuyaCipher) -> None:
        """Protocol 3.4 should use ECB mode."""
        assert hasattr(cipher_v34, 'is_gcm_mode')
        assert cipher_v34.is_gcm_mode is False

    def test_v35_encrypt_returns_iv_ciphertext_tag(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Protocol 3.5 encrypt should return (iv, ciphertext, tag) tuple."""
        plaintext = b'{"dps":{"1":true}}'
        result = cipher_v35.encrypt_gcm(plaintext)

        assert isinstance(result, tuple)
        assert len(result) == 3

        iv, ciphertext, tag = result
        assert len(iv) == 12  # 96-bit IV/nonce
        assert len(tag) == 16  # 128-bit GCM tag
        assert len(ciphertext) > 0

    def test_v35_encrypt_no_padding_required(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Protocol 3.5 GCM mode does not require padding."""
        # 17 bytes - not a multiple of 16
        plaintext = b'12345678901234567'
        iv, ciphertext, tag = cipher_v35.encrypt_gcm(plaintext)

        # GCM ciphertext length equals plaintext length (no padding)
        assert len(ciphertext) == len(plaintext)

    def test_v35_decrypt_with_valid_data(self, cipher_v35: TuyaCipher) -> None:
        """Protocol 3.5 decrypt should work with valid iv, ciphertext, tag."""
        plaintext = b'{"dps":{"1":true}}'
        iv, ciphertext, tag = cipher_v35.encrypt_gcm(plaintext)

        decrypted = cipher_v35.decrypt_gcm(iv, ciphertext, tag)
        assert decrypted == plaintext

    def test_v35_decrypt_with_invalid_tag_raises(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Protocol 3.5 decrypt should raise on invalid GCM tag."""
        plaintext = b'{"dps":{"1":true}}'
        iv, ciphertext, tag = cipher_v35.encrypt_gcm(plaintext)

        # Corrupt the tag
        bad_tag = bytes([tag[0] ^ 0xFF]) + tag[1:]

        with pytest.raises(Exception):  # GCM authentication failure
            cipher_v35.decrypt_gcm(iv, ciphertext, bad_tag)

    def test_v35_decrypt_with_tampered_ciphertext_raises(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Protocol 3.5 decrypt should raise if ciphertext is tampered."""
        plaintext = b'{"dps":{"1":true}}'
        iv, ciphertext, tag = cipher_v35.encrypt_gcm(plaintext)

        # Corrupt the ciphertext
        bad_ciphertext = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]

        with pytest.raises(Exception):  # GCM authentication failure
            cipher_v35.decrypt_gcm(iv, bad_ciphertext, tag)

    def test_v35_encrypt_with_aad(self, cipher_v35: TuyaCipher) -> None:
        """Protocol 3.5 encrypt should support additional authenticated data."""
        plaintext = b'{"dps":{"1":true}}'
        aad = b'\x00\x00\x66\x99\x00\x00\x00\x00\x00\x01'  # Header bytes

        iv, ciphertext, tag = cipher_v35.encrypt_gcm(plaintext, aad=aad)

        # Decrypt with same AAD should work
        decrypted = cipher_v35.decrypt_gcm(iv, ciphertext, tag, aad=aad)
        assert decrypted == plaintext

    def test_v35_decrypt_with_wrong_aad_raises(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Protocol 3.5 decrypt should fail if AAD doesn't match."""
        plaintext = b'{"dps":{"1":true}}'
        aad = b'\x00\x00\x66\x99\x00\x00\x00\x00\x00\x01'

        iv, ciphertext, tag = cipher_v35.encrypt_gcm(plaintext, aad=aad)

        # Decrypt with different AAD should fail
        wrong_aad = b'\x00\x00\x66\x99\x00\x00\x00\x00\x00\x02'
        with pytest.raises(Exception):
            cipher_v35.decrypt_gcm(iv, ciphertext, tag, aad=wrong_aad)

    def test_v35_generate_iv_returns_12_bytes(
        self, cipher_v35: TuyaCipher
    ) -> None:
        """Protocol 3.5 IV generator should return 12 random bytes."""
        iv = cipher_v35.generate_iv()
        assert len(iv) == 12
        assert isinstance(iv, bytes)

    def test_v35_generate_iv_is_random(self, cipher_v35: TuyaCipher) -> None:
        """Protocol 3.5 IV generator should produce unique values."""
        ivs = [cipher_v35.generate_iv() for _ in range(100)]
        # All IVs should be unique
        assert len(set(ivs)) == 100
