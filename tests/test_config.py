"""
Unit tests for configuration module.
Tests expiry options and configuration validation.
"""

import pytest
from datetime import timedelta
import config


@pytest.mark.unit
class TestExpiryConfiguration:
    """Test expiry time configurations."""
    
    def test_all_expiry_options_valid(self):
        """Test that all expiry options return valid timedeltas."""
        for key in config.EXPIRY_OPTIONS.keys():
            delta = config.get_expiry_timedelta(key)
            assert isinstance(delta, timedelta)
            assert delta.total_seconds() > 0
    
    def test_is_valid_expiry(self):
        """Test expiry key validation."""
        assert config.is_valid_expiry('1hour') is True
        assert config.is_valid_expiry('1day') is True
        assert config.is_valid_expiry('invalid') is False
        assert config.is_valid_expiry('') is False
    
    def test_get_expiry_timedelta(self):
        """Test getting timedelta for expiry keys."""
        # Test specific values
        assert config.get_expiry_timedelta('10min') == timedelta(minutes=10)
        assert config.get_expiry_timedelta('1hour') == timedelta(hours=1)
        assert config.get_expiry_timedelta('1day') == timedelta(days=1)
        assert config.get_expiry_timedelta('1week') == timedelta(weeks=1)
    
    def test_invalid_expiry_returns_default(self):
        """Test that invalid expiry returns default."""
        delta = config.get_expiry_timedelta('invalid_key')
        default_delta = config.EXPIRY_OPTIONS[config.DEFAULT_EXPIRY]
        assert delta == default_delta
    
    def test_get_expiry_choices(self):
        """Test getting expiry choices for frontend."""
        choices = config.get_expiry_choices()
        
        assert isinstance(choices, list)
        assert len(choices) > 0
        
        for choice in choices:
            assert 'key' in choice
            assert 'label' in choice
            assert config.is_valid_expiry(choice['key'])


@pytest.mark.unit
class TestConfigurationValues:
    """Test configuration values are sensible."""
    
    def test_paste_id_length(self):
        """Test paste ID length is reasonable."""
        assert config.PASTE_ID_LENGTH >= 6
        assert config.PASTE_ID_LENGTH <= 32
    
    def test_max_paste_size(self):
        """Test max paste size is reasonable."""
        assert config.MAX_PASTE_SIZE > 0
        assert config.MAX_PASTE_SIZE <= 10 * 1024 * 1024  # 10MB max
    
    def test_cleanup_interval(self):
        """Test cleanup interval is reasonable."""
        assert config.CLEANUP_INTERVAL > 0
        assert config.CLEANUP_INTERVAL <= 3600  # At most 1 hour
    
    def test_default_expiry_exists(self):
        """Test that default expiry is valid."""
        assert config.DEFAULT_EXPIRY in config.EXPIRY_OPTIONS