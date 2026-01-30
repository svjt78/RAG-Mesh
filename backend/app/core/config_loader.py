"""
Configuration loader for RAGMesh
Loads and validates all JSON configurations against Pydantic schemas
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.models import (
    ChunkingProfile,
    GraphExtractionProfile,
    RetrievalProfile,
    FusionProfile,
    RerankProfile,
    ContextProfile,
    JudgeProfile,
    ChatProfile,
    WorkflowProfile,
    TelemetryConfig,
    CheckConfig,
)

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and manages all system configurations"""

    def __init__(self, config_dir: Path = Path("config")):
        """
        Initialize config loader

        Args:
            config_dir: Path to configuration directory
        """
        self.config_dir = config_dir
        self.configs: Dict[str, Any] = {}
        self._load_all_configs()

    @property
    def config(self) -> Dict[str, Any]:
        """Alias for configs to maintain backward compatibility"""
        return self.configs

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """
        Load a JSON configuration file

        Args:
            filename: Name of the config file

        Returns:
            Parsed JSON as dictionary
        """
        file_path = self.config_dir / filename
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded configuration: {filename}")
                return data
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            raise

    def _load_all_configs(self) -> None:
        """Load all configuration files"""
        logger.info("Loading all configurations...")

        # Load raw configurations
        self.configs = {
            "models": self._load_json("models.json"),
            "workflows": self._load_json("workflows.json"),
            "chunking_profiles": self._load_json("chunking_profiles.json"),
            "graph_extraction_profiles": self._load_json("graph_extraction_profiles.json"),
            "retrieval_profiles": self._load_json("retrieval_profiles.json"),
            "fusion_profiles": self._load_json("fusion_profiles.json"),
            "reranking_profiles": self._load_json("reranking_profiles.json"),
            "context_profiles": self._load_json("context_profiles.json"),
            "judge_profiles": self._load_json("judge_profiles.json"),
            "chat_profiles": self._load_json("chat_profiles.json"),
            "telemetry": self._load_json("telemetry.json"),
            "prompts": self._load_json("prompts.json"),
        }

        logger.info("All configurations loaded successfully")

    def get_chunking_profile(self, profile_id: str = "default") -> ChunkingProfile:
        """
        Get a validated chunking profile

        Args:
            profile_id: Profile identifier

        Returns:
            Validated ChunkingProfile
        """
        profiles = self.configs["chunking_profiles"]["profiles"]
        if profile_id not in profiles:
            logger.warning(f"Chunking profile '{profile_id}' not found, using default")
            profile_id = self.configs["chunking_profiles"]["default_profile"]

        return ChunkingProfile(**profiles[profile_id])

    def get_graph_extraction_profile(self, profile_id: str = "generic") -> GraphExtractionProfile:
        """
        Get a validated graph extraction profile

        Args:
            profile_id: Profile identifier

        Returns:
            Validated GraphExtractionProfile
        """
        profiles = self.configs["graph_extraction_profiles"]["profiles"]
        if profile_id not in profiles:
            logger.warning(f"Graph extraction profile '{profile_id}' not found, using default")
            profile_id = self.configs["graph_extraction_profiles"]["default_profile"]

        return GraphExtractionProfile(**profiles[profile_id])

    def get_retrieval_profile(self, profile_id: str = "balanced_insurance") -> RetrievalProfile:
        """
        Get a validated retrieval profile

        Args:
            profile_id: Profile identifier

        Returns:
            Validated RetrievalProfile
        """
        profiles = self.configs["retrieval_profiles"]["profiles"]
        if profile_id not in profiles:
            logger.warning(f"Retrieval profile '{profile_id}' not found, using default")
            profile_id = self.configs["retrieval_profiles"]["default_profile"]

        return RetrievalProfile(**profiles[profile_id])

    def get_fusion_profile(self, profile_id: str = "balanced") -> FusionProfile:
        """
        Get a validated fusion profile

        Args:
            profile_id: Profile identifier

        Returns:
            Validated FusionProfile
        """
        profiles = self.configs["fusion_profiles"]["profiles"]
        if profile_id not in profiles:
            logger.warning(f"Fusion profile '{profile_id}' not found, using default")
            profile_id = self.configs["fusion_profiles"]["default_profile"]

        return FusionProfile(**profiles[profile_id])

    def get_context_profile(self, profile_id: str = "default") -> ContextProfile:
        """
        Get a validated context profile

        Args:
            profile_id: Profile identifier

        Returns:
            Validated ContextProfile
        """
        profiles = self.configs["context_profiles"]["profiles"]
        if profile_id not in profiles:
            logger.warning(f"Context profile '{profile_id}' not found, using default")
            profile_id = self.configs["context_profiles"]["default_profile"]

        return ContextProfile(**profiles[profile_id])

    def get_reranking_profile(self, profile_id: str = "default") -> RerankProfile:
        """
        Get a validated reranking profile

        Args:
            profile_id: Profile identifier

        Returns:
            Validated RerankProfile
        """
        profiles = self.configs["reranking_profiles"]["profiles"]
        if profile_id not in profiles:
            logger.warning(f"Reranking profile '{profile_id}' not found, using default")
            profile_id = self.configs["reranking_profiles"]["default_profile"]

        return RerankProfile(**profiles[profile_id])

    def get_judge_profile(self, profile_id: str = "strict_insurance") -> JudgeProfile:
        """
        Get a validated judge profile

        Args:
            profile_id: Profile identifier

        Returns:
            Validated JudgeProfile
        """
        profiles = self.configs["judge_profiles"]["profiles"]
        if profile_id not in profiles:
            logger.warning(f"Judge profile '{profile_id}' not found, using default")
            profile_id = self.configs["judge_profiles"]["default_profile"]

        profile_data = profiles[profile_id]

        # Convert check configurations to CheckConfig objects
        judge_profile = JudgeProfile(
            citation_coverage=CheckConfig(**profile_data["citation_coverage"]),
            groundedness=CheckConfig(**profile_data["groundedness"]),
            hallucination=CheckConfig(**profile_data["hallucination"]),
            relevance=CheckConfig(**profile_data["relevance"]),
            consistency=CheckConfig(**profile_data["consistency"]),
            toxicity=CheckConfig(**profile_data["toxicity"]),
            pii_leakage=CheckConfig(**profile_data["pii_leakage"]),
            bias=CheckConfig(**profile_data["bias"]),
            contradiction=CheckConfig(**profile_data["contradiction"]),
        )

        return judge_profile

    def get_chat_profile(self, profile_id: str = "default") -> ChatProfile:
        """
        Get a validated chat profile

        Args:
            profile_id: Profile identifier

        Returns:
            Validated ChatProfile
        """
        profiles = self.configs["chat_profiles"]["profiles"]
        if profile_id not in profiles:
            logger.warning(f"Chat profile '{profile_id}' not found, using default")
            profile_id = self.configs["chat_profiles"]["default_profile"]

        return ChatProfile(**profiles[profile_id])

    def get_workflow_profile(self, workflow_id: str = "default_workflow") -> WorkflowProfile:
        """
        Get a validated workflow profile

        Args:
            workflow_id: Workflow identifier

        Returns:
            Validated WorkflowProfile
        """
        workflows = self.configs["workflows"]["workflows"]
        if workflow_id not in workflows:
            logger.warning(f"Workflow '{workflow_id}' not found, using default")
            workflow_id = self.configs["workflows"]["default_workflow"]

        return WorkflowProfile(**workflows[workflow_id])

    def get_telemetry_config(self, profile: str = "standard") -> TelemetryConfig:
        """
        Get a validated telemetry configuration

        Args:
            profile: Telemetry profile name

        Returns:
            Validated TelemetryConfig
        """
        profiles = self.configs["telemetry"]["profiles"]
        if profile not in profiles:
            logger.warning(f"Telemetry profile '{profile}' not found, using default")
            profile_data = self.configs["telemetry"]["default"]
        else:
            profile_data = profiles[profile]

        return TelemetryConfig(**profile_data)

    def get_model_config(self, model_name: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """
        Get model configuration

        Args:
            model_name: Model name

        Returns:
            Model configuration dictionary
        """
        models = self.configs["models"]["models"]
        if model_name not in models:
            logger.warning(f"Model '{model_name}' not found in config")
            return {}

        return models[model_name]

    def get_generation_system_prompt(self) -> str:
        """
        Get the generation system prompt template

        Returns:
            System prompt string
        """
        return self.configs.get("prompts", {}).get("generation", {}).get("system_prompt", "")

    def create_config_snapshot(
        self,
        workflow_id: str,
        retrieval_profile_id: str,
        context_profile_id: str,
        judge_profile_id: str,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a configuration snapshot for deterministic replay

        Args:
            workflow_id: Workflow identifier
            retrieval_profile_id: Retrieval profile identifier
            context_profile_id: Context profile identifier
            judge_profile_id: Judge profile identifier
            overrides: Optional runtime overrides

        Returns:
            Complete configuration snapshot
        """
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "workflow": self.get_workflow_profile(workflow_id).model_dump(),
            "retrieval": self.get_retrieval_profile(retrieval_profile_id).model_dump(),
            "context": self.get_context_profile(context_profile_id).model_dump(),
            "judge": self.get_judge_profile(judge_profile_id).model_dump(),
            "prompts": self.configs.get("prompts", {}),
            "models": self.configs["models"],
            "overrides": overrides or {},
        }

        logger.info(f"Created configuration snapshot for workflow '{workflow_id}'")
        return snapshot

    def list_profiles(self) -> Dict[str, list]:
        """
        List all available profiles

        Returns:
            Dictionary of profile types to profile IDs
        """
        return {
            "chunking": list(self.configs["chunking_profiles"]["profiles"].keys()),
            "graph_extraction": list(self.configs["graph_extraction_profiles"]["profiles"].keys()),
            "retrieval": list(self.configs["retrieval_profiles"]["profiles"].keys()),
            "fusion": list(self.configs["fusion_profiles"]["profiles"].keys()),
            "reranking": list(self.configs["reranking_profiles"]["profiles"].keys()),
            "context": list(self.configs["context_profiles"]["profiles"].keys()),
            "judge": list(self.configs["judge_profiles"]["profiles"].keys()),
            "chat": list(self.configs["chat_profiles"]["profiles"].keys()),
            "workflows": list(self.configs["workflows"]["workflows"].keys()),
            "prompts": ["generation"],
        }

    def save_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> None:
        """
        Save or update a workflow configuration

        Args:
            workflow_id: Workflow identifier
            workflow_data: Workflow configuration data

        Raises:
            ValueError: If workflow data is invalid
        """
        # Validate using Pydantic model
        try:
            validated_workflow = WorkflowProfile(**workflow_data)
        except Exception as e:
            logger.error(f"Invalid workflow data: {e}")
            raise ValueError(f"Invalid workflow configuration: {e}")

        # Update in-memory config
        self.configs["workflows"]["workflows"][workflow_id] = validated_workflow.model_dump()

        # Save to file
        file_path = self.config_dir / "workflows.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["workflows"], f, indent=2)
            logger.info(f"Saved workflow configuration: {workflow_id}")
        except Exception as e:
            logger.error(f"Failed to save workflow configuration: {e}")
            raise

    def save_chunking_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save or update a chunking profile configuration

        Args:
            profile_id: Chunking profile identifier
            profile_data: Chunking profile configuration data

        Raises:
            ValueError: If profile data is invalid
        """
        # Validate using Pydantic model
        try:
            validated_profile = ChunkingProfile(**profile_data)
        except Exception as e:
            logger.error(f"Invalid chunking profile data: {e}")
            raise ValueError(f"Invalid chunking profile configuration: {e}")

        # Update in-memory config
        self.configs["chunking_profiles"]["profiles"][profile_id] = validated_profile.model_dump()

        # Save to file
        file_path = self.config_dir / "chunking_profiles.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["chunking_profiles"], f, indent=2)
            logger.info(f"Saved chunking profile configuration: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to save chunking profile configuration: {e}")
            raise

    def save_graph_extraction_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save or update a graph extraction profile configuration

        Args:
            profile_id: Graph extraction profile identifier
            profile_data: Graph extraction profile configuration data

        Raises:
            ValueError: If profile data is invalid
        """
        # Validate using Pydantic model
        try:
            validated_profile = GraphExtractionProfile(**profile_data)
        except Exception as e:
            logger.error(f"Invalid graph extraction profile data: {e}")
            raise ValueError(f"Invalid graph extraction profile configuration: {e}")

        # Update in-memory config
        self.configs["graph_extraction_profiles"]["profiles"][profile_id] = validated_profile.model_dump()

        # Save to file
        file_path = self.config_dir / "graph_extraction_profiles.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["graph_extraction_profiles"], f, indent=2)
            logger.info(f"Saved graph extraction profile configuration: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to save graph extraction profile configuration: {e}")
            raise

    def save_retrieval_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save or update a retrieval profile configuration

        Args:
            profile_id: Retrieval profile identifier
            profile_data: Retrieval profile configuration data

        Raises:
            ValueError: If profile data is invalid
        """
        # Validate using Pydantic model
        try:
            validated_profile = RetrievalProfile(**profile_data)
        except Exception as e:
            logger.error(f"Invalid retrieval profile data: {e}")
            raise ValueError(f"Invalid retrieval profile configuration: {e}")

        # Update in-memory config
        self.configs["retrieval_profiles"]["profiles"][profile_id] = validated_profile.model_dump()

        # Save to file
        file_path = self.config_dir / "retrieval_profiles.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["retrieval_profiles"], f, indent=2)
            logger.info(f"Saved retrieval profile configuration: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to save retrieval profile configuration: {e}")
            raise

    def save_fusion_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save or update a fusion profile configuration

        Args:
            profile_id: Fusion profile identifier
            profile_data: Fusion profile configuration data

        Raises:
            ValueError: If profile data is invalid
        """
        # Validate using Pydantic model
        try:
            validated_profile = FusionProfile(**profile_data)
        except Exception as e:
            logger.error(f"Invalid fusion profile data: {e}")
            raise ValueError(f"Invalid fusion profile configuration: {e}")

        # Update in-memory config
        self.configs["fusion_profiles"]["profiles"][profile_id] = validated_profile.model_dump()

        # Save to file
        file_path = self.config_dir / "fusion_profiles.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["fusion_profiles"], f, indent=2)
            logger.info(f"Saved fusion profile configuration: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to save fusion profile configuration: {e}")
            raise

    def save_context_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save or update a context profile configuration

        Args:
            profile_id: Context profile identifier
            profile_data: Context profile configuration data

        Raises:
            ValueError: If profile data is invalid
        """
        # Validate using Pydantic model
        try:
            validated_profile = ContextProfile(**profile_data)
        except Exception as e:
            logger.error(f"Invalid context profile data: {e}")
            raise ValueError(f"Invalid context profile configuration: {e}")

        # Update in-memory config
        self.configs["context_profiles"]["profiles"][profile_id] = validated_profile.model_dump()

        # Save to file
        file_path = self.config_dir / "context_profiles.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["context_profiles"], f, indent=2)
            logger.info(f"Saved context profile configuration: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to save context profile configuration: {e}")
            raise

    def save_reranking_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save or update a reranking profile configuration

        Args:
            profile_id: Reranking profile identifier
            profile_data: Reranking profile configuration data

        Raises:
            ValueError: If profile data is invalid
        """
        try:
            validated_profile = RerankProfile(**profile_data)
        except Exception as e:
            logger.error(f"Invalid reranking profile data: {e}")
            raise ValueError(f"Invalid reranking profile configuration: {e}")

        self.configs["reranking_profiles"]["profiles"][profile_id] = validated_profile.model_dump()

        file_path = self.config_dir / "reranking_profiles.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["reranking_profiles"], f, indent=2)
            logger.info(f"Saved reranking profile configuration: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to save reranking profile configuration: {e}")
            raise

    def save_judge_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save or update a judge profile configuration

        Args:
            profile_id: Judge profile identifier
            profile_data: Judge profile configuration data

        Raises:
            ValueError: If profile data is invalid
        """
        # Validate using Pydantic model
        try:
            validated_profile = JudgeProfile(**profile_data)
        except Exception as e:
            logger.error(f"Invalid judge profile data: {e}")
            raise ValueError(f"Invalid judge profile configuration: {e}")

        # Update in-memory config
        self.configs["judge_profiles"]["profiles"][profile_id] = validated_profile.model_dump()

        # Save to file
        file_path = self.config_dir / "judge_profiles.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["judge_profiles"], f, indent=2)
            logger.info(f"Saved judge profile configuration: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to save judge profile configuration: {e}")
            raise

    def save_prompts(self, prompts_data: Dict[str, Any]) -> None:
        """
        Save prompt templates configuration

        Args:
            prompts_data: Prompt templates configuration data

        Raises:
            ValueError: If prompt data is invalid
        """
        if not isinstance(prompts_data, dict):
            raise ValueError("Prompts configuration must be an object")

        generation = prompts_data.get("generation", {})
        system_prompt = generation.get("system_prompt")
        if not isinstance(system_prompt, str) or not system_prompt.strip():
            raise ValueError("generation.system_prompt must be a non-empty string")

        self.configs["prompts"] = prompts_data

        file_path = self.config_dir / "prompts.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["prompts"], f, indent=2)
            logger.info("Saved prompt configuration")
        except Exception as e:
            logger.error(f"Failed to save prompt configuration: {e}")
            raise

    def save_chat_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Save or update a chat profile configuration

        Args:
            profile_id: Chat profile identifier
            profile_data: Chat profile configuration data

        Raises:
            ValueError: If profile data is invalid
        """
        # Validate using Pydantic model
        try:
            validated_profile = ChatProfile(**profile_data)
        except Exception as e:
            logger.error(f"Invalid chat profile data: {e}")
            raise ValueError(f"Invalid chat profile configuration: {e}")

        # Update in-memory config
        self.configs["chat_profiles"]["profiles"][profile_id] = validated_profile.model_dump()

        # Save to file
        file_path = self.config_dir / "chat_profiles.json"
        try:
            with open(file_path, 'w') as f:
                json.dump(self.configs["chat_profiles"], f, indent=2)
            logger.info(f"Saved chat profile configuration: {profile_id}")
        except Exception as e:
            logger.error(f"Failed to save chat profile configuration: {e}")
            raise

    def reload(self) -> None:
        """Reload all configurations from files"""
        self._load_all_configs()
        logger.info("All configurations reloaded")


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """
    Get the global config loader instance

    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def reload_configs() -> None:
    """Reload all configurations"""
    global _config_loader
    _config_loader = ConfigLoader()
    logger.info("Configurations reloaded")
