"""Basic autopatching of trackable libraries.

This module should not require any dependencies beyond the standard library. It should
check if libraries are installed and imported and patch in the case that they are.
"""


def autopatch_openai() -> None:
    try:
        import openai  # type: ignore
    except ImportError:
        pass
    else:
        if openai.__version__ < "1":
            print(
                "To automatically track openai calls, upgrade the openai package to a version >= '1.0'"
            )
            return
        from weave.legacy.monitoring.openai import patch

        patch()


def unpatch_openai() -> None:
    try:
        import openai  # type: ignore
    except ImportError:
        pass
    else:
        if openai.__version__ < "1":
            return
        from weave.legacy.monitoring.openai import unpatch

        unpatch()


def autopatch() -> None:
    autopatch_openai()

    from .integrations.anthropic.anthropic_sdk import anthropic_patcher
    from .integrations.litellm.litellm import litellm_patcher
    from .integrations.llamaindex.llamaindex import llamaindex_patcher
    from .integrations.mistral.mistral import mistral_patcher
    from .integrations.cohere.cohere_sdk import cohere_patcher  # Add this line

    mistral_patcher.attempt_patch()
    litellm_patcher.attempt_patch()
    llamaindex_patcher.attempt_patch()
    anthropic_patcher.attempt_patch()
    cohere_patcher.attempt_patch()  # Add this line


def reset_autopatch() -> None:
    unpatch_openai()

    from .integrations.anthropic.anthropic_sdk import anthropic_patcher
    from .integrations.litellm.litellm import litellm_patcher
    from .integrations.llamaindex.llamaindex import llamaindex_patcher
    from .integrations.mistral.mistral import mistral_patcher
    from .integrations.cohere.cohere_sdk import cohere_patcher  # Add this line

    mistral_patcher.undo_patch()
    litellm_patcher.undo_patch()
    llamaindex_patcher.undo_patch()
    anthropic_patcher.undo_patch()
    cohere_patcher.undo_patch()  # Add this line
