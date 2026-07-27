"""Tests for countries module."""

import pytest
from custom_components.robovac.countries import (
    get_region_by_country_code,
    get_region_by_phone_code,
    get_phone_code_by_region,
    get_phone_code_by_country_code,
)


class TestCountriesRegion:
    """Tests for country region lookups."""

    def test_get_region_by_country_code_valid_us(self) -> None:
        """Test getting region for valid US country code."""
        region = get_region_by_country_code("US")
        assert region == "AZ"

    def test_get_region_by_country_code_valid_gb(self) -> None:
        """Test getting region for valid GB country code."""
        region = get_region_by_country_code("GB")
        assert region == "EU"

    def test_get_region_by_country_code_invalid(self) -> None:
        """Test getting region for invalid country code returns default EU."""
        region = get_region_by_country_code("XX")
        assert region == "EU"

    def test_get_region_by_phone_code_valid_us(self) -> None:
        """Test getting region for valid US phone code."""
        region = get_region_by_phone_code("1")
        assert region == "AZ"

    def test_get_region_by_phone_code_valid_uk(self) -> None:
        """Test getting region for valid UK phone code."""
        region = get_region_by_phone_code("44")
        assert region == "EU"

    def test_get_region_by_phone_code_invalid(self) -> None:
        """Test getting region for invalid phone code returns default EU."""
        region = get_region_by_phone_code("999999")
        assert region == "EU"

    def test_get_phone_code_by_region_eu(self) -> None:
        """Test getting phone code for EU region."""
        phone_code = get_phone_code_by_region("EU")
        # First matching country for EU region
        assert phone_code in ["93", "355", "213", "244"]  # Multiple countries with EU region

    def test_get_phone_code_by_region_az(self) -> None:
        """Test getting phone code for AZ region."""
        phone_code = get_phone_code_by_region("AZ")
        assert phone_code in ["54", "61", "1"]  # Multiple countries in AZ

    def test_get_phone_code_by_region_invalid(self) -> None:
        """Test getting phone code for invalid region returns default 44."""
        phone_code = get_phone_code_by_region("XX")
        assert phone_code == "44"

    def test_get_phone_code_by_country_code_valid_us(self) -> None:
        """Test getting phone code for valid US country code."""
        phone_code = get_phone_code_by_country_code("US")
        assert phone_code == "1"

    def test_get_phone_code_by_country_code_valid_gb(self) -> None:
        """Test getting phone code for valid GB country code."""
        phone_code = get_phone_code_by_country_code("GB")
        assert phone_code == "44"

    def test_get_phone_code_by_country_code_invalid(self) -> None:
        """Test getting phone code for invalid country code returns default 44."""
        phone_code = get_phone_code_by_country_code("XX")
        assert phone_code == "44"
