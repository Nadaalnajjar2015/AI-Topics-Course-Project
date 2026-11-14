"""Request Investigator placeholder used while the real agent is in development."""

from contracts.schemas import Investigation, Request


def investigate(request: Request) -> Investigation:
    """Return the contract example as a placeholder investigation."""
    example = Investigation.model_config["json_schema_extra"]["example"]
    return Investigation.model_validate(example).model_copy(
        update={"request_id": request.request_id}
    )
