import pytest

from src.mydash.client.geocoding.factory import get_geocoding_client
from src.mydash.client.geocoding.open_meteo import OpenMeteoClient


def test_get_geocoding_client_provider_empty_return_open_meteo_client():
    assert isinstance(get_geocoding_client(), OpenMeteoClient)


@pytest.mark.parametrize(
    "unknown_provider", ["-", ".", "some_thing", "openMeteo", "fake_provider"]
)
def test_get_geocoding_client_provider_unknown_return_value_error(unknown_provider):
    with pytest.raises(ValueError) as err:
        get_geocoding_client(unknown_provider)
    assert err.type is ValueError
