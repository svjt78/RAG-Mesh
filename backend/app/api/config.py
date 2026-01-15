"""
Configuration API routes
Handles configuration profile queries and management
"""

from fastapi import APIRouter, HTTPException
import logging

from app.core.config_loader import get_config_loader

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize config loader
config_loader = get_config_loader()


@router.get("/config/profiles")
async def list_all_profiles():
    """
    List all available configuration profiles

    Returns:
        All profile IDs organized by type
    """
    logger.info("Listing all configuration profiles")

    try:
        profiles = config_loader.list_profiles()
        return {
            "profiles": profiles,
            "total": sum(len(v) for v in profiles.values())
        }

    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/workflows")
async def list_workflows():
    """
    List available workflow profiles

    Returns:
        Workflow profile IDs and descriptions
    """
    logger.info("Listing workflows")

    try:
        workflows = config_loader.config["workflows"]
        return {
            "workflows": [
                {
                    "workflow_id": wf_id,
                    "name": wf.get("name", wf_id),
                    "description": wf.get("description", ""),
                    "steps": wf.get("steps", [])
                }
                for wf_id, wf in workflows.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/workflow/{workflow_id}")
async def get_workflow(workflow_id: str):
    """
    Get a specific workflow profile

    Args:
        workflow_id: Workflow profile ID

    Returns:
        Workflow configuration
    """
    logger.info(f"Getting workflow: {workflow_id}")

    try:
        workflow = config_loader.get_workflow_profile(workflow_id)
        return {"workflow": workflow.model_dump()}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    except Exception as e:
        logger.error(f"Error getting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/chunking")
async def list_chunking_profiles():
    """
    List available chunking profiles

    Returns:
        Chunking profile IDs and descriptions
    """
    logger.info("Listing chunking profiles")

    try:
        profiles = config_loader.config["chunking_profiles"]
        return {
            "profiles": [
                {
                    "profile_id": profile_id,
                    "strategy": profile.get("strategy", "unknown"),
                    "chunk_size": profile.get("chunk_size", 0),
                    "chunk_overlap": profile.get("chunk_overlap", 0)
                }
                for profile_id, profile in profiles.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error listing chunking profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/chunking/{profile_id}")
async def get_chunking_profile(profile_id: str):
    """
    Get a specific chunking profile

    Args:
        profile_id: Chunking profile ID

    Returns:
        Chunking configuration
    """
    logger.info(f"Getting chunking profile: {profile_id}")

    try:
        profile = config_loader.get_chunking_profile(profile_id)
        return {"profile": profile.model_dump()}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Chunking profile not found: {profile_id}")
    except Exception as e:
        logger.error(f"Error getting chunking profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/chunking/{profile_id}")
async def update_chunking_profile(profile_id: str, profile_data: dict):
    """
    Update a chunking profile configuration

    Args:
        profile_id: Chunking profile ID
        profile_data: Updated chunking profile configuration

    Returns:
        Updated chunking profile configuration
    """
    logger.info(f"Updating chunking profile: {profile_id}")

    try:
        config_loader.save_chunking_profile(profile_id, profile_data)
        updated_profile = config_loader.get_chunking_profile(profile_id)
        return {
            "status": "updated",
            "profile_id": profile_id,
            "profile": updated_profile.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating chunking profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/retrieval")
async def list_retrieval_profiles():
    """
    List available retrieval profiles

    Returns:
        Retrieval profile IDs and descriptions
    """
    logger.info("Listing retrieval profiles")

    try:
        profiles = config_loader.config["retrieval_profiles"]
        return {
            "profiles": [
                {
                    "profile_id": profile_id,
                    "vector_weight": profile.get("vector_weight", 1.0),
                    "document_weight": profile.get("document_weight", 1.0),
                    "graph_weight": profile.get("graph_weight", 1.0),
                    "vector_k": profile.get("vector_k", 10)
                }
                for profile_id, profile in profiles.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error listing retrieval profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/retrieval/{profile_id}")
async def get_retrieval_profile(profile_id: str):
    """
    Get a specific retrieval profile

    Args:
        profile_id: Retrieval profile ID

    Returns:
        Retrieval configuration
    """
    logger.info(f"Getting retrieval profile: {profile_id}")

    try:
        profile = config_loader.get_retrieval_profile(profile_id)
        return {"profile": profile.model_dump()}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Retrieval profile not found: {profile_id}")
    except Exception as e:
        logger.error(f"Error getting retrieval profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/retrieval/{profile_id}")
async def update_retrieval_profile(profile_id: str, profile_data: dict):
    """
    Update a retrieval profile configuration

    Args:
        profile_id: Retrieval profile ID
        profile_data: Updated retrieval profile configuration

    Returns:
        Updated retrieval profile configuration
    """
    logger.info(f"Updating retrieval profile: {profile_id}")

    try:
        config_loader.save_retrieval_profile(profile_id, profile_data)
        updated_profile = config_loader.get_retrieval_profile(profile_id)
        return {
            "status": "updated",
            "profile_id": profile_id,
            "profile": updated_profile.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating retrieval profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/fusion")
async def list_fusion_profiles():
    """
    List available fusion profiles

    Returns:
        Fusion profile IDs and descriptions
    """
    logger.info("Listing fusion profiles")

    try:
        profiles = config_loader.config["fusion_profiles"]
        return {
            "profiles": [
                {
                    "profile_id": profile_id,
                    "rrf_k": profile.get("rrf_k", 60),
                    "vector_weight": profile.get("vector_weight", 1.0),
                    "document_weight": profile.get("document_weight", 1.0),
                    "graph_weight": profile.get("graph_weight", 1.0)
                }
                for profile_id, profile in profiles.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error listing fusion profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/fusion/{profile_id}")
async def get_fusion_profile(profile_id: str):
    """
    Get a specific fusion profile

    Args:
        profile_id: Fusion profile ID

    Returns:
        Fusion configuration
    """
    logger.info(f"Getting fusion profile: {profile_id}")

    try:
        profile = config_loader.get_fusion_profile(profile_id)
        return {"profile": profile.model_dump()}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Fusion profile not found: {profile_id}")
    except Exception as e:
        logger.error(f"Error getting fusion profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/fusion/{profile_id}")
async def update_fusion_profile(profile_id: str, profile_data: dict):
    """
    Update a fusion profile configuration

    Args:
        profile_id: Fusion profile ID
        profile_data: Updated fusion profile configuration

    Returns:
        Updated fusion profile configuration
    """
    logger.info(f"Updating fusion profile: {profile_id}")

    try:
        config_loader.save_fusion_profile(profile_id, profile_data)
        updated_profile = config_loader.get_fusion_profile(profile_id)
        return {
            "status": "updated",
            "profile_id": profile_id,
            "profile": updated_profile.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating fusion profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/reranking")
async def list_reranking_profiles():
    """
    List available reranking profiles

    Returns:
        Reranking profile IDs and descriptions
    """
    logger.info("Listing reranking profiles")

    try:
        profiles = config_loader.config["reranking_profiles"]["profiles"]
        return {
            "profiles": [
                {
                    "profile_id": profile_id,
                    "model": profile.get("model", ""),
                    "enabled": profile.get("enabled", False),
                    "max_chunks": profile.get("max_chunks", 0)
                }
                for profile_id, profile in profiles.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error listing reranking profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/reranking/{profile_id}")
async def get_reranking_profile(profile_id: str):
    """
    Get a specific reranking profile

    Args:
        profile_id: Reranking profile ID

    Returns:
        Reranking configuration
    """
    logger.info(f"Getting reranking profile: {profile_id}")

    try:
        profile = config_loader.get_reranking_profile(profile_id)
        return {"profile": profile.model_dump()}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Reranking profile not found: {profile_id}")
    except Exception as e:
        logger.error(f"Error getting reranking profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/reranking/{profile_id}")
async def update_reranking_profile(profile_id: str, profile_data: dict):
    """
    Update a reranking profile configuration

    Args:
        profile_id: Reranking profile ID
        profile_data: Updated reranking profile configuration

    Returns:
        Updated reranking profile configuration
    """
    logger.info(f"Updating reranking profile: {profile_id}")

    try:
        config_loader.save_reranking_profile(profile_id, profile_data)
        updated_profile = config_loader.get_reranking_profile(profile_id)
        return {
            "status": "updated",
            "profile_id": profile_id,
            "profile": updated_profile.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating reranking profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/context")
async def list_context_profiles():
    """
    List available context profiles

    Returns:
        Context profile IDs and descriptions
    """
    logger.info("Listing context profiles")

    try:
        profiles = config_loader.config["context_profiles"]
        return {
            "profiles": [
                {
                    "profile_id": profile_id,
                    "max_context_tokens": profile.get("max_context_tokens", 0),
                    "citation_style": profile.get("citation_style", "compact")
                }
                for profile_id, profile in profiles.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error listing context profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/context/{profile_id}")
async def get_context_profile(profile_id: str):
    """
    Get a specific context profile

    Args:
        profile_id: Context profile ID

    Returns:
        Context configuration
    """
    logger.info(f"Getting context profile: {profile_id}")

    try:
        profile = config_loader.get_context_profile(profile_id)
        return {"profile": profile.model_dump()}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Context profile not found: {profile_id}")
    except Exception as e:
        logger.error(f"Error getting context profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/context/{profile_id}")
async def update_context_profile(profile_id: str, profile_data: dict):
    """
    Update a context profile configuration

    Args:
        profile_id: Context profile ID
        profile_data: Updated context profile configuration

    Returns:
        Updated context profile configuration
    """
    logger.info(f"Updating context profile: {profile_id}")

    try:
        config_loader.save_context_profile(profile_id, profile_data)
        updated_profile = config_loader.get_context_profile(profile_id)
        return {
            "status": "updated",
            "profile_id": profile_id,
            "profile": updated_profile.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating context profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/judge")
async def list_judge_profiles():
    """
    List available judge profiles

    Returns:
        Judge profile IDs and descriptions
    """
    logger.info("Listing judge profiles")

    try:
        profiles = config_loader.config["judge_profiles"]
        return {
            "profiles": [
                {
                    "profile_id": profile_id,
                    "checks_enabled": len(profile.get("checks", {})),
                    "checks": list(profile.get("checks", {}).keys())
                }
                for profile_id, profile in profiles.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error listing judge profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/judge/{profile_id}")
async def get_judge_profile(profile_id: str):
    """
    Get a specific judge profile

    Args:
        profile_id: Judge profile ID

    Returns:
        Judge configuration
    """
    logger.info(f"Getting judge profile: {profile_id}")

    try:
        profile = config_loader.get_judge_profile(profile_id)
        return {"profile": profile.model_dump()}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Judge profile not found: {profile_id}")
    except Exception as e:
        logger.error(f"Error getting judge profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/judge/{profile_id}")
async def update_judge_profile(profile_id: str, profile_data: dict):
    """
    Update a judge profile configuration

    Args:
        profile_id: Judge profile ID
        profile_data: Updated judge profile configuration

    Returns:
        Updated judge profile configuration
    """
    logger.info(f"Updating judge profile: {profile_id}")

    try:
        config_loader.save_judge_profile(profile_id, profile_data)
        updated_profile = config_loader.get_judge_profile(profile_id)
        return {
            "status": "updated",
            "profile_id": profile_id,
            "profile": updated_profile.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating judge profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/models")
async def get_model_config():
    """
    Get model configuration

    Returns:
        Model configurations and pricing
    """
    logger.info("Getting model config")

    try:
        models = config_loader.config["models"]
        return {
            "models": models,
            "default_generation": config_loader.config["models"].get("default_generation_model"),
            "default_embedding": config_loader.config["models"].get("default_embedding_model")
        }

    except Exception as e:
        logger.error(f"Error getting model config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/workflow/{workflow_id}")
async def update_workflow(workflow_id: str, workflow_data: dict):
    """
    Update a workflow configuration

    Args:
        workflow_id: Workflow profile ID
        workflow_data: Updated workflow configuration

    Returns:
        Updated workflow configuration
    """
    logger.info(f"Updating workflow: {workflow_id}")

    try:
        config_loader.save_workflow(workflow_id, workflow_data)
        updated_workflow = config_loader.get_workflow_profile(workflow_id)
        return {
            "status": "updated",
            "workflow_id": workflow_id,
            "workflow": updated_workflow.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/prompts")
async def get_prompts():
    """
    Get prompt templates configuration

    Returns:
        Prompt templates configuration
    """
    logger.info("Getting prompt configuration")

    try:
        return {"prompts": config_loader.configs.get("prompts", {})}

    except Exception as e:
        logger.error(f"Error getting prompt configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/prompts")
async def update_prompts(prompts_data: dict):
    """
    Update prompt templates configuration

    Args:
        prompts_data: Prompt templates configuration data

    Returns:
        Updated prompt configuration
    """
    logger.info("Updating prompt configuration")

    try:
        config_loader.save_prompts(prompts_data)
        return {
            "status": "updated",
            "prompts": config_loader.configs.get("prompts", {})
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating prompt configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/chat")
async def list_chat_profiles():
    """
    List available chat profiles

    Returns:
        Chat profile IDs and descriptions
    """
    logger.info("Listing chat profiles")

    try:
        profiles = config_loader.config["chat_profiles"]["profiles"]
        return {
            "profiles": [
                {
                    "profile_id": profile_id,
                    "description": profile.get("description", ""),
                    "compaction_threshold_tokens": profile.get("compaction_threshold_tokens", 0),
                    "max_history_turns": profile.get("max_history_turns", 0)
                }
                for profile_id, profile in profiles.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error listing chat profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/chat/{profile_id}")
async def get_chat_profile(profile_id: str):
    """
    Get a specific chat profile

    Args:
        profile_id: Chat profile ID

    Returns:
        Chat configuration
    """
    logger.info(f"Getting chat profile: {profile_id}")

    try:
        profile = config_loader.get_chat_profile(profile_id)
        return {"profile": profile.model_dump()}

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Chat profile not found: {profile_id}")
    except Exception as e:
        logger.error(f"Error getting chat profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/chat/{profile_id}")
async def update_chat_profile(profile_id: str, profile_data: dict):
    """
    Update a chat profile configuration

    Args:
        profile_id: Chat profile ID
        profile_data: Updated chat profile configuration

    Returns:
        Updated chat profile configuration
    """
    logger.info(f"Updating chat profile: {profile_id}")

    try:
        config_loader.save_chat_profile(profile_id, profile_data)
        updated_profile = config_loader.get_chat_profile(profile_id)
        return {
            "status": "updated",
            "profile_id": profile_id,
            "profile": updated_profile.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating chat profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/reload")
async def reload_config():
    """
    Reload configuration from files

    Returns:
        Reload status
    """
    logger.info("Reloading configuration")

    try:
        config_loader.reload()
        return {
            "status": "reloaded",
            "profiles": config_loader.list_profiles()
        }

    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
