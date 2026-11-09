from datetime import datetime

import pytest

from app.domain.entities import Incident
from app.domain.errors import InvalidIncident


def test_incident_keeps_its_description():
    incident = Incident(None, 1, "Panne de courant", datetime(2027, 6, 18, 20))
    assert incident.description == "Panne de courant"
    assert incident.resolved is False


def test_incident_description_is_trimmed():
    assert Incident(None, 1, "  Panne  ", datetime(2027, 6, 18, 20)).description == "Panne"


@pytest.mark.parametrize("description", ["", "   ", "\n\t"])
def test_incident_description_cannot_be_blank(description):
    with pytest.raises(InvalidIncident):
        Incident(None, 1, description, datetime(2027, 6, 18, 20))
