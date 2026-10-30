"""Connector names are selected exclusively by template configuration."""
from part1_templates.connectors.registration_lookup import RegistrationLookup
from part1_templates.connectors.transaction_lookup import TransactionLookup

CONNECTORS = {
    "transaction_lookup": TransactionLookup,
    "registration_lookup": RegistrationLookup,
}
