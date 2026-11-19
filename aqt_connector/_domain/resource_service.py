from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails


class ResourceService:
    def __init__(self, arnica: ArnicaAdapter) -> None:
        """Initialises the ResourceService with the given ArnicaAdapter.

        Args:
            arnica (ArnicaAdapter): The Arnica adapter to use for fetching resource details.
        """
        self.arnica = arnica

    def get_resource_details(self, token: str, resource_id: str) -> ResourceDetails:
        """Gets details for the resource with the given ID using the provided token.

        Args:
            token (str): The authentication token to use.
            resource_id (str): The ID of the resource to fetch.

        Returns:
            ResourceDetails: Details for the requested resource.
        """
        return self.arnica.get_resource_details(token, resource_id)
