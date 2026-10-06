from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Protocol


@dataclass(frozen=True)
class ControllerRef:
    workstream: str
    controller_id: str
    branch: str
    base_commit: str
    repository_identity: str = "repository"
    canonical_work: str = ""


@dataclass(frozen=True)
class AttentionBrief:
    workstream: str
    objective: str
    evidence_refs: tuple[str, ...] = ()
    repository_identity: str = "repository"
    canonical_work: str = ""
    expected_branch: str = "main"
    expected_base: str = "test-base"


@dataclass(frozen=True)
class CoordinationDelta:
    kind: str
    summary: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolveReceipt:
    workstream: str
    controller: ControllerRef | None
    found: bool
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ActivationReceipt:
    activation_key: str
    workstream: str
    controller: ControllerRef | None
    created: bool
    reused: bool
    recovery_required: bool = False
    reason: str | None = None
    request_fingerprint: str = ""
    released: bool = False


@dataclass(frozen=True)
class ResumeReceipt:
    controller: ControllerRef
    resumed: bool
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ObservationReceipt:
    controller: ControllerRef
    state: str
    deltas: tuple[CoordinationDelta, ...] = ()
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class DeliveryReceipt:
    controller: ControllerRef
    delivered: bool
    recovery_required: bool = False
    reason: str | None = None
    delivery_identity: str = ""
    payload_fingerprint: str = ""


@dataclass(frozen=True)
class SessionReleaseReceipt:
    controller: ControllerRef
    released: bool
    recovery_required: bool = False
    reason: str | None = None


class ActivationReceiptJournal(Protocol):
    def lookup_activation(self, activation_key: str) -> ActivationReceipt | None:
        ...

    def record_activation(self, receipt: ActivationReceipt) -> None:
        ...

    def mark_released(self, activation_key: str) -> None:
        ...


class ControllerSessionAdapter(Protocol):
    def resolve(self, workstream: str) -> ResolveReceipt:
        ...

    def lookup_activation(self, activation_key: str) -> ActivationReceipt | None:
        ...

    def activate(
        self,
        workstream: str,
        activation_key: str,
        brief: AttentionBrief,
    ) -> ActivationReceipt:
        ...

    def resume(self, controller: ControllerRef, brief: AttentionBrief) -> ResumeReceipt:
        ...

    def observe(self, controller: ControllerRef) -> ObservationReceipt:
        ...

    def deliver(
        self,
        controller: ControllerRef,
        brief: AttentionBrief,
        delivery_identity: str = "default",
    ) -> DeliveryReceipt:
        ...

    def release_session(self, controller: ControllerRef) -> SessionReleaseReceipt:
        ...


class InMemoryActivationReceiptJournal:
    def __init__(self) -> None:
        self._receipts: dict[str, ActivationReceipt] = {}

    def lookup_activation(self, activation_key: str) -> ActivationReceipt | None:
        return self._receipts.get(activation_key)

    def record_activation(self, receipt: ActivationReceipt) -> None:
        current = self._receipts.get(receipt.activation_key)
        if current is not None and (
            current.request_fingerprint != receipt.request_fingerprint
            or current.controller != receipt.controller
        ):
            raise ValueError("activation key already has a different receipt")
        self._receipts[receipt.activation_key] = receipt

    def mark_released(self, activation_key: str) -> None:
        receipt = self._receipts.get(activation_key)
        if receipt is not None:
            self._receipts[activation_key] = replace(receipt, released=True)


class InMemoryControllerSessionAdapter:
    def __init__(self, journal: ActivationReceiptJournal | None = None) -> None:
        self.journal = journal or InMemoryActivationReceiptJournal()
        self._controllers: dict[tuple[str, str], ControllerRef] = {}
        self._activation_keys: dict[tuple[str, str], str] = {}
        self._deliveries: dict[tuple[ControllerRef, str], str] = {}
        self._next_controller = 1
        self.activation_side_effects = 0
        self.delivery_side_effects = 0

    def resolve(self, workstream: str, repository_identity: str = "repository") -> ResolveReceipt:
        controller = self._controllers.get((repository_identity, workstream))
        if controller is None:
            return ResolveReceipt(workstream=workstream, controller=None, found=False)
        return ResolveReceipt(workstream=workstream, controller=controller, found=True)

    def lookup_activation(self, activation_key: str) -> ActivationReceipt | None:
        return self.journal.lookup_activation(activation_key)

    def activate(
        self,
        workstream: str,
        activation_key: str,
        brief: AttentionBrief,
    ) -> ActivationReceipt:
        if brief.workstream != workstream:
            return ActivationReceipt(
                activation_key=activation_key,
                workstream=workstream,
                controller=None,
                created=False,
                reused=False,
                recovery_required=True,
                reason="brief workstream does not match activation workstream",
            )

        owner_key = (brief.repository_identity, workstream)
        request_fingerprint = _fingerprint(
            {
                "repository_identity": brief.repository_identity,
                "canonical_work": brief.canonical_work or workstream,
                "expected_branch": brief.expected_branch,
                "expected_base": brief.expected_base,
                "objective": brief.objective.strip(),
                "evidence_refs": sorted(set(brief.evidence_refs)),
            }
        )
        existing = self.journal.lookup_activation(activation_key)
        if existing is not None:
            if existing.workstream != workstream:
                return replace(
                    existing,
                    recovery_required=True,
                    reason="activation key belongs to another workstream",
                )
            if existing.request_fingerprint != request_fingerprint:
                return replace(
                    existing,
                    recovery_required=True,
                    reason="activation key has a different request fingerprint",
                )
            if existing.released:
                return replace(
                    existing,
                    created=False,
                    reused=False,
                    recovery_required=True,
                    reason="activation receipt was released; new activation is required",
                )
            if existing.controller is not None:
                self._controllers[owner_key] = existing.controller
                self._activation_keys[owner_key] = activation_key
            return replace(existing, created=False, reused=True)

        if owner_key in self._controllers:
            return ActivationReceipt(
                activation_key=activation_key,
                workstream=workstream,
                controller=self._controllers[owner_key],
                created=False,
                reused=False,
                recovery_required=True,
                reason="workstream already has an active controller",
                request_fingerprint=request_fingerprint,
            )

        controller = ControllerRef(
            workstream=workstream,
            controller_id=f"controller-{self._next_controller}",
            branch=brief.expected_branch,
            base_commit=brief.expected_base,
            repository_identity=brief.repository_identity,
            canonical_work=brief.canonical_work or workstream,
        )
        self._next_controller += 1
        receipt = ActivationReceipt(
            activation_key=activation_key,
            workstream=workstream,
            controller=controller,
            created=True,
            reused=False,
            request_fingerprint=request_fingerprint,
        )
        self.journal.record_activation(receipt)
        self._controllers[owner_key] = controller
        self._activation_keys[owner_key] = activation_key
        self.activation_side_effects += 1
        return receipt

    def resume(self, controller: ControllerRef, brief: AttentionBrief) -> ResumeReceipt:
        current = self._controllers.get((controller.repository_identity, controller.workstream))
        if brief.workstream != controller.workstream:
            return ResumeReceipt(
                controller=controller,
                resumed=False,
                recovery_required=True,
                reason="brief workstream does not match controller workstream",
            )
        if current != controller:
            return ResumeReceipt(
                controller=controller,
                resumed=False,
                recovery_required=True,
                reason="controller identity is stale or unknown",
            )
        return ResumeReceipt(controller=controller, resumed=True)

    def observe(self, controller: ControllerRef) -> ObservationReceipt:
        if self._controllers.get((controller.repository_identity, controller.workstream)) != controller:
            return ObservationReceipt(
                controller=controller,
                state="unknown",
                recovery_required=True,
                reason="controller identity is stale or unknown",
            )
        return ObservationReceipt(controller=controller, state="observed")

    def deliver(
        self,
        controller: ControllerRef,
        brief: AttentionBrief,
        delivery_identity: str = "default",
    ) -> DeliveryReceipt:
        if brief.workstream != controller.workstream:
            return DeliveryReceipt(
                controller=controller,
                delivered=False,
                recovery_required=True,
                reason="brief workstream does not match controller workstream",
            )
        if self._controllers.get((controller.repository_identity, controller.workstream)) != controller:
            return DeliveryReceipt(
                controller=controller,
                delivered=False,
                recovery_required=True,
                reason="controller identity is stale or unknown",
            )
        payload_fingerprint = _fingerprint(
            {
                "objective": brief.objective.strip(),
                "evidence_refs": sorted(set(brief.evidence_refs)),
                "repository_identity": brief.repository_identity,
                "canonical_work": brief.canonical_work or brief.workstream,
            }
        )
        delivery_key = (controller, delivery_identity)
        previous = self._deliveries.get(delivery_key)
        if previous is not None:
            if previous != payload_fingerprint:
                return DeliveryReceipt(
                    controller=controller,
                    delivered=False,
                    recovery_required=True,
                    reason="delivery identity has a different payload fingerprint",
                    delivery_identity=delivery_identity,
                    payload_fingerprint=payload_fingerprint,
                )
            return DeliveryReceipt(
                controller=controller,
                delivered=True,
                delivery_identity=delivery_identity,
                payload_fingerprint=payload_fingerprint,
            )
        self._deliveries[delivery_key] = payload_fingerprint
        self.delivery_side_effects += 1
        return DeliveryReceipt(
            controller=controller,
            delivered=True,
            delivery_identity=delivery_identity,
            payload_fingerprint=payload_fingerprint,
        )

    def release_session(self, controller: ControllerRef) -> SessionReleaseReceipt:
        owner_key = (controller.repository_identity, controller.workstream)
        if self._controllers.get(owner_key) != controller:
            return SessionReleaseReceipt(
                controller=controller,
                released=False,
                recovery_required=True,
                reason="session identity is stale or unknown",
            )
        del self._controllers[owner_key]
        activation_key = self._activation_keys.pop(owner_key, None)
        if activation_key is not None:
            self.journal.mark_released(activation_key)
        return SessionReleaseReceipt(controller=controller, released=True)


def _fingerprint(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "ActivationReceipt",
    "ActivationReceiptJournal",
    "AttentionBrief",
    "ControllerRef",
    "ControllerSessionAdapter",
    "CoordinationDelta",
    "DeliveryReceipt",
    "InMemoryActivationReceiptJournal",
    "InMemoryControllerSessionAdapter",
    "ObservationReceipt",
    "ResolveReceipt",
    "ResumeReceipt",
    "SessionReleaseReceipt",
]
