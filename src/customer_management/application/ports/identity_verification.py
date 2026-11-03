from __future__ import annotations

from abc import ABC, abstractmethod

from customer_management.domain.subscriber.identity_document import (
    DocumentType,
    IdentityDocument,
)


class IdentityVerificationPort(ABC):
    @abstractmethod
    def verify_identity(
        self,
        document_type: DocumentType,
        document_number: str,
    ) -> IdentityDocument | None:
        """Return authoritative verified data, or None for a rejected identity."""
        raise NotImplementedError

