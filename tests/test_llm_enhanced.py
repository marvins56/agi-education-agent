"""Tests for enhanced LLM factory and multi-provider support."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.llm_config import ProviderConfigRequest
from src.llm.factory_enhanced import EnhancedLLMFactory
from src.models.llm_settings import UserLLMSettings
from src.models.user import User
from src.utils.encryption import APIKeyEncryption


class TestAPIKeyEncryption:
    """Test the API key encryption utilities."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        encryption = APIKeyEncryption()
        original_key = "sk-test-api-key-12345"
        
        # Encrypt
        encrypted = encryption.encrypt(original_key)
        assert encrypted != original_key
        assert len(encrypted) > 0
        
        # Decrypt
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original_key
    
    def test_encrypt_empty_string(self):
        """Test encryption of empty strings."""
        encryption = APIKeyEncryption()
        
        encrypted = encryption.encrypt("")
        assert encrypted == ""
        
        decrypted = encryption.decrypt("")
        assert decrypted is None
    
    def test_decrypt_invalid_data(self):
        """Test decryption with invalid data."""
        encryption = APIKeyEncryption()
        
        # Invalid base64
        result = encryption.decrypt("invalid-data")
        assert result is None


class TestEnhancedLLMFactory:
    """Test the enhanced LLM factory."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock(spec=AsyncSession)
        return db
    
    @pytest.fixture
    def mock_user(self):
        """Mock user."""
        user = User()
        user.id = uuid4()
        user.email = "test@example.com"
        user.name = "Test User"
        return user
    
    @pytest.fixture
    def mock_user_settings(self, mock_user):
        """Mock user LLM settings."""
        from src.utils.encryption import api_key_encryption
        
        settings = UserLLMSettings()
        settings.user_id = mock_user.id
        settings.preferred_provider = "anthropic"
        settings.preferred_model = "claude-3-5-sonnet-20241022"
        settings.anthropic_api_key_encrypted = api_key_encryption.encrypt("test-anthropic-key")
        return settings
    
    @pytest.mark.asyncio
    async def test_get_user_settings_exists(self, mock_db, mock_user, mock_user_settings):
        """Test getting user settings when they exist."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user_settings
        mock_db.execute.return_value = mock_result
        
        settings = await EnhancedLLMFactory._get_user_settings(str(mock_user.id), mock_db)
        
        assert settings == mock_user_settings
        assert settings.preferred_provider == "anthropic"
    
    @pytest.mark.asyncio
    async def test_get_user_settings_none(self, mock_db, mock_user):
        """Test getting user settings when none exist."""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        settings = await EnhancedLLMFactory._get_user_settings(str(mock_user.id), mock_db)
        
        assert settings is None
    
    @pytest.mark.asyncio
    async def test_get_api_key_for_provider_user_key(self, mock_user_settings):
        """Test getting API key from user settings."""
        api_key = await EnhancedLLMFactory._get_api_key_for_provider(
            "anthropic", mock_user_settings
        )
        
        assert api_key == "test-anthropic-key"
    
    @pytest.mark.asyncio
    async def test_get_api_key_for_provider_ollama(self):
        """Test getting API key for Ollama (should be None)."""
        api_key = await EnhancedLLMFactory._get_api_key_for_provider("ollama", None)
        assert api_key is None
    
    @pytest.mark.asyncio
    async def test_get_api_key_for_provider_system_fallback(self):
        """Test falling back to system API key."""
        with patch("src.config.settings.ANTHROPIC_API_KEY", "system-anthropic-key"):
            api_key = await EnhancedLLMFactory._get_api_key_for_provider("anthropic", None)
            assert api_key == "system-anthropic-key"
    
    def test_get_default_model_user_preference(self, mock_user_settings):
        """Test getting default model from user preference."""
        model = EnhancedLLMFactory._get_default_model("anthropic", mock_user_settings)
        assert model == "claude-3-5-sonnet-20241022"
    
    def test_get_default_model_system_default(self):
        """Test getting system default model."""
        model = EnhancedLLMFactory._get_default_model("anthropic", None)
        assert model.startswith("claude-")  # Should use system default
    
    @patch('src.llm.factory_enhanced.ChatOllama')
    def test_create_ollama(self, mock_chat_ollama):
        """Test creating Ollama instance."""
        mock_instance = MagicMock()
        mock_chat_ollama.return_value = mock_instance
        
        result = EnhancedLLMFactory._create_ollama("qwen2.5:3b", 0.7, 4096)
        
        assert result == mock_instance
        mock_chat_ollama.assert_called_once_with(
            model="qwen2.5:3b",
            base_url="http://localhost:11434",
            temperature=0.7,
            num_predict=4096,
        )
    
    @patch('src.llm.factory_enhanced.ChatAnthropic')
    def test_create_anthropic_with_key(self, mock_chat_anthropic):
        """Test creating Anthropic instance with API key."""
        mock_instance = MagicMock()
        mock_chat_anthropic.return_value = mock_instance
        
        result = EnhancedLLMFactory._create_anthropic(
            "test-key", "claude-3-5-sonnet-20241022", 0.7, 4096
        )
        
        assert result == mock_instance
        mock_chat_anthropic.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=4096,
            anthropic_api_key="test-key",
        )
    
    def test_create_anthropic_without_key(self):
        """Test creating Anthropic instance without API key raises error."""
        with pytest.raises(ValueError, match="Anthropic API key is required"):
            EnhancedLLMFactory._create_anthropic("", "claude-3-5-sonnet-20241022", 0.7, 4096)
    
    @patch('src.llm.factory_enhanced.ChatGroq')
    def test_create_groq_with_key(self, mock_chat_groq):
        """Test creating Groq instance with API key."""
        mock_instance = MagicMock()
        mock_chat_groq.return_value = mock_instance
        
        result = EnhancedLLMFactory._create_groq(
            "groq-key", "llama-3.1-8b-instant", 0.7, 4096
        )
        
        assert result == mock_instance
        mock_chat_groq.assert_called_once_with(
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=4096,
            groq_api_key="groq-key",
        )
    
    def test_create_provider_instance_unsupported(self):
        """Test creating instance for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            EnhancedLLMFactory._create_provider_instance(
                "invalid", "key", "model", 0.7, 4096
            )
    
    @pytest.mark.asyncio
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_user_settings')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_api_key_for_provider')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_default_model')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._create_provider_instance')
    async def test_create_for_user_success(
        self, mock_create_provider, mock_get_model, mock_get_api_key, 
        mock_get_settings, mock_db, mock_user, mock_user_settings
    ):
        """Test successful LLM creation for user."""
        # Setup mocks
        mock_get_settings.return_value = mock_user_settings
        mock_get_api_key.return_value = "test-key"
        mock_get_model.return_value = "claude-3-5-sonnet-20241022"
        mock_llm_instance = MagicMock()
        mock_create_provider.return_value = mock_llm_instance
        
        # Call method
        result = await EnhancedLLMFactory.create_for_user(
            str(mock_user.id), mock_db
        )
        
        # Assertions
        assert result == mock_llm_instance
        mock_get_settings.assert_called_once_with(str(mock_user.id), mock_db)
        mock_get_api_key.assert_called_once_with("anthropic", mock_user_settings)
        mock_get_model.assert_called_once_with("anthropic", mock_user_settings)
        mock_create_provider.assert_called_once_with(
            "anthropic", "test-key", "claude-3-5-sonnet-20241022", 0.7, 4096
        )
    
    @pytest.mark.asyncio
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_user_settings')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_api_key_for_provider')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_default_model')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._create_provider_instance')
    async def test_create_for_user_with_fallback(
        self, mock_create_provider, mock_get_model, mock_get_api_key,
        mock_get_settings, mock_db, mock_user, mock_user_settings
    ):
        """Test LLM creation with fallback when primary provider fails."""
        # Setup mocks
        mock_get_settings.return_value = mock_user_settings
        mock_get_api_key.side_effect = ["test-key", None]  # Anthropic key, then None for Ollama
        mock_get_model.side_effect = ["claude-3-5-sonnet-20241022", "qwen2.5:3b"]
        
        # First call fails, second succeeds
        mock_ollama_instance = MagicMock()
        mock_create_provider.side_effect = [
            ValueError("Anthropic failed"),  # First provider fails
            mock_ollama_instance  # Ollama succeeds
        ]
        
        # Call method
        result = await EnhancedLLMFactory.create_for_user(
            str(mock_user.id), mock_db, use_fallback=True
        )
        
        # Should return Ollama instance after Anthropic fails
        assert result == mock_ollama_instance
        assert mock_create_provider.call_count == 2
    
    @pytest.mark.asyncio
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_user_settings')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_api_key_for_provider')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._get_default_model')
    @patch('src.llm.factory_enhanced.EnhancedLLMFactory._create_provider_instance')
    async def test_create_for_user_all_fail(
        self, mock_create_provider, mock_get_model, mock_get_api_key,
        mock_get_settings, mock_db, mock_user
    ):
        """Test LLM creation when all providers fail."""
        # Setup mocks
        mock_get_settings.return_value = None  # No user settings
        mock_get_api_key.return_value = None
        mock_get_model.return_value = "qwen2.5:3b"
        
        # All providers fail
        mock_create_provider.side_effect = ValueError("All providers failed")
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="No working LLM provider available"):
            await EnhancedLLMFactory.create_for_user(
                str(mock_user.id), mock_db, use_fallback=True
            )


class TestLLMConfigAPI:
    """Test the LLM configuration API endpoints."""
    
    def test_provider_config_request_validation(self):
        """Test provider configuration request validation."""
        # Valid request
        valid_request = ProviderConfigRequest(
            preferred_provider="anthropic",
            preferred_model="claude-3-5-sonnet-20241022",
            anthropic_api_key="test-key"
        )
        assert valid_request.preferred_provider == "anthropic"
        
        # Invalid provider should be caught by regex validation
        with pytest.raises(ValueError):
            ProviderConfigRequest(
                preferred_provider="invalid-provider",
                anthropic_api_key="test-key"
            )