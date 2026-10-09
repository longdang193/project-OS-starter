from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Protocol


@dataclass(frozen=True)
class ControllerBinding:
    repository_identity: str
    canonical_work: str
    workstream: str
    expected_branch: str
    expected_base: str


@dataclass(frozen=True)
class AttentionDelta:
    reason: str
    constraint_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    decision_needed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraint_refs", tuple(sorted(set(self.constraint_refs))))
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(self.evidence_refs))))


@dataclass(frozen=True)
class CoordinationDelta:
    kind: str
    affected_workstreams: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    decision_needed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "affected_workstreams", tuple(sorted(set(self.affected_workstreams))))
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(self.evidence_refs))))


@dataclass(frozen=True)
class CommunicationEnvelope:
    binding: ControllerBinding
    message_id: str
    canonical_anchor: str
    payload: AttentionDelta | CoordinationDelta


@dataclass(frozen=True)
class ControllerRef:
    binding: ControllerBinding
    controller_id: str

    @property
    def workstream(self) -> str:
        return self.binding.workstream


@dataclass(frozen=True)
class ResolveReceipt:
    binding: ControllerBinding
    controller: ControllerRef | None
    found: bool
    recovery_required: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ActivationReceipt:
    activation_id: str
    binding: ControllerBinding
    controller: ControllerRef | None
    created: bool
    reused: bool
    recovery_required: bool = False
    reason: str | None = None
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
    message_id: str = ""
    payload_fingerprint: str = ""


@dataclass(frozen=True)
class SessionReleaseReceipt:
    controller: ControllerRef
    released: bool
    recovery_required: bool = False
    reason: str | None = None


class ControllerSessionJournal(Protocol):
    def lookup_activation(self, activation_id: str) -> ActivationReceipt | None:
        ...

    def record_activation(self, receipt: ActivationReceipt) -> None:
        ...

    def lookup_controller(self, binding: ControllerBinding) -> ControllerRef | None:
        ...

    def lookup_owner(self, repository_identity: str, workstream: str) -> ControllerRef | None:
        ...

    def record_controller(self, controller: ControllerRef) -> None:
        ...

    def release_controller(self, controller: ControllerRef) -> None:
        ...

    def lookup_delivery(self, controller: ControllerRef, message_id: str) -> str | None:
        ...

    def record_delivery(
        self, controller: ControllerRef, message_id: str, payload_fingerprint: str
    ) -> None:
        ...

    def compact_released(self, controller: ControllerRef) -> bool:
        ...


class ControllerSessionAdapter(Protocol):
    def resolve(self, binding: ControllerBinding) -> ResolveReceipt:
        ...

    def activate(self, binding: ControllerBinding, activation_id: str) -> ActivationReceipt:
        ...

    def resume(self, controller: ControllerRef, binding: ControllerBinding) -> ResumeReceipt:
        ...

    def observe(self, controller: ControllerRef) -> ObservationReceipt:
        ...

    def deliver(self, controller: ControllerRef, envelope: CommunicationEnvelope) -> DeliveryReceipt:
        ...

    def release_session(self, controller: ControllerRef) -> SessionReleaseReceipt:
        ...


class InMemoryControllerSessionJournal:
    def __init__(self) -> None:
        self._activations: dict[str, ActivationReceipt] = {}
        self._controllers: dict[ControllerBinding, ControllerRef] = {}
        self._owners: dict[tuple[str, str], ControllerRef] = {}
        self._deliveries: dict[tuple[str, str], str] = {}
        self._activation_tombstones: dict[str, ActivationReceipt] = {}

    def lookup_activation(self, activation_id: str) -> ActivationReceipt | None:
        return self._activations.get(activation_id) or self._activation_tombstones.get(activation_id)

    def record_activation(self, receipt: ActivationReceipt) -> None:
        current = self._activations.get(receipt.activation_id)
        if current is not None and (
            current.binding != receipt.binding or current.controller != receipt.controller
        ):
            raise ValueError("activation ID already has a different receipt")
        self._activations[receipt.activation_id] = receipt

    def lookup_controller(self, binding: ControllerBinding) -> ControllerRef | None:
        return self._controllers.get(binding)

    def lookup_owner(self, repository_identity: str, workstream: str) -> ControllerRef | None:
        return self._owners.get((repository_identity, workstream))

    def record_controller(self, controller: ControllerRef) -> None:
        self._controllers[controller.binding] = controller
        self._owners[(controller.binding.repository_identity, controller.binding.workstream)] = controller

    def release_controller(self, controller: ControllerRef) -> None:
        if self._controllers.get(controller.binding) == controller:
            del self._controllers[controller.binding]
        owner_key = (controller.binding.repository_identity, controller.binding.workstream)
        if self._owners.get(owner_key) == controller:
            del self._owners[owner_key]
        for activation_id, receipt in tuple(self._activations.items()):
            if receipt.controller == controller:
                self._activations[activation_id] = replace(receipt, released=True)

    def lookup_delivery(self, controller: ControllerRef, message_id: str) -> str | None:
        return self._deliveries.get((controller.controller_id, message_id))

    def record_delivery(
        self, controller: ControllerRef, message_id: str, payload_fingerprint: str
    ) -> None:
        self._deliveries[(controller.controller_id, message_id)] = payload_fingerprint

    def compact_released(self, controller: ControllerRef) -> bool:
        matching = [
            (activation_id, receipt)
            for activation_id, receipt in self._activations.items()
            if receipt.controller == controller and receipt.released
        ]
        if not matching:
            return False
        for activation_id, receipt in matching:
            self._activation_tombstones[activation_id] = replace(
                receipt,
                controller=None,
                created=False,
                reused=False,
                reason="activation compacted; replay remains blocked",
            )
            del self._activations[activation_id]
        self._controllers.pop(controller.binding, None)
        owner_key = (controller.binding.repository_identity, controller.binding.workstream)
        if self._owners.get(owner_key) == controller:
            del self._owners[owner_key]
        return True


class InMemoryControllerSessionAdapter:
    def __init__(self, journal: ControllerSessionJournal | None = None) -> None:
        self.journal = journal or InMemoryControllerSessionJournal()
        self.activation_side_effects = 0
        self.delivery_side_effects = 0

    def resolve(self, binding: ControllerBinding) -> ResolveReceipt:
        controller = self.journal.lookup_controller(binding)
        if controller is None:
            conflicting = self.journal.lookup_owner(
                binding.repository_identity, binding.workstream
            )
            if conflicting is not None:
                return ResolveReceipt(
                    binding=binding,
                    controller=conflicting,
                    found=False,
                    recovery_required=True,
                    reason="binding does not match active controller",
                )
        return ResolveReceipt(
            binding=binding,
            controller=controller,
            found=controller is not None,
        )

    def activate(self, binding: ControllerBinding, activation_id: str) -> ActivationReceipt:
        previous = self.journal.lookup_activation(activation_id)
        if previous is not None:
            if previous.controller is not None and not matches_binding(previous.controller, binding):
                return self._activation_recovery(
                    binding, activation_id, "activation ID has a different binding"
                )
            if previous.released:
                return self._activation_recovery(
                    binding,
                    activation_id,
                    previous.reason or "activation ID belongs to a released controller",
                )
            return replace(previous, created=False, reused=True)

        current = self.journal.lookup_controller(binding)
        if current is None:
            current = self.journal.lookup_owner(
                binding.repository_identity, binding.workstream
            )
        if current is not None:
            return self._activation_recovery(
                binding, activation_id, "binding already has an active controller"
            )

        controller = ControllerRef(
            binding=binding,
            controller_id=f"controller-{_fingerprint({'activation_id': activation_id})[:16]}",
        )
        receipt = ActivationReceipt(
            activation_id=activation_id,
            binding=binding,
            controller=controller,
            created=True,
            reused=False,
        )
        self.journal.record_activation(receipt)
        self.journal.record_controller(controller)
        self.activation_side_effects += 1
        return receipt

    def resume(self, controller: ControllerRef, binding: ControllerBinding) -> ResumeReceipt:
        if not matches_binding(controller, binding):
            return ResumeReceipt(
                controller=controller,
                resumed=False,
                recovery_required=True,
                reason="binding does not match controller",
            )
        if self.journal.lookup_controller(binding) != controller:
            return ResumeReceipt(
                controller=controller,
                resumed=False,
                recovery_required=True,
                reason="controller identity is stale or unknown",
            )
        return ResumeReceipt(controller=controller, resumed=True)

    def observe(self, controller: ControllerRef) -> ObservationReceipt:
        if self.journal.lookup_controller(controller.binding) != controller:
            return ObservationReceipt(
                controller=controller,
                state="unknown",
                recovery_required=True,
                reason="controller identity is stale or unknown",
            )
        return ObservationReceipt(controller=controller, state="observed")

    def deliver(
        self, controller: ControllerRef, envelope: CommunicationEnvelope
    ) -> DeliveryReceipt:
        if not matches_binding(controller, envelope.binding):
            return DeliveryReceipt(
                controller=controller,
                delivered=False,
                recovery_required=True,
                reason="binding does not match controller",
                message_id=envelope.message_id,
            )
        if self.journal.lookup_controller(envelope.binding) != controller:
            return DeliveryReceipt(
                controller=controller,
                delivered=False,
                recovery_required=True,
                reason="controller identity is stale or unknown",
                message_id=envelope.message_id,
            )

        payload_fingerprint = _fingerprint(envelope)
        previous = self.journal.lookup_delivery(controller, envelope.message_id)
        if previous is not None:
            if previous != payload_fingerprint:
                return DeliveryReceipt(
                    controller=controller,
                    delivered=False,
                    recovery_required=True,
                    reason="message ID has a different payload fingerprint",
                    message_id=envelope.message_id,
                    payload_fingerprint=payload_fingerprint,
                )
            return DeliveryReceipt(
                controller=controller,
                delivered=True,
                message_id=envelope.message_id,
                payload_fingerprint=payload_fingerprint,
            )

        self.journal.record_delivery(controller, envelope.message_id, payload_fingerprint)
        self.delivery_side_effects += 1
        return DeliveryReceipt(
            controller=controller,
            delivered=True,
            message_id=envelope.message_id,
            payload_fingerprint=payload_fingerprint,
        )

    def release_session(self, controller: ControllerRef) -> SessionReleaseReceipt:
        if self.journal.lookup_controller(controller.binding) != controller:
            return SessionReleaseReceipt(
                controller=controller,
                released=False,
                recovery_required=True,
                reason="session identity is stale or unknown",
            )
        self.journal.release_controller(controller)
        return SessionReleaseReceipt(controller=controller, released=True)

    def compact_released(self, controller: ControllerRef) -> bool:
        return self.journal.compact_released(controller)

    @staticmethod
    def _activation_recovery(
        binding: ControllerBinding, activation_id: str, reason: str
    ) -> ActivationReceipt:
        return ActivationReceipt(
            activation_id=activation_id,
            binding=binding,
            controller=None,
            created=False,
            reused=False,
            recovery_required=True,
            reason=reason,
        )


def matches_binding(controller: ControllerRef, binding: ControllerBinding) -> bool:
    return controller.binding == binding


def _fingerprint(payload: object) -> str:
    if isinstance(payload, CommunicationEnvelope):
        payload = {
            "binding": payload.binding.__dict__,
            "message_id": payload.message_id,
            "canonical_anchor": payload.canonical_anchor,
            "payload": payload.payload.__dict__,
        }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "ActivationReceipt",
    "AttentionDelta",
    "CommunicationEnvelope",
    "ControllerBinding",
    "ControllerRef",
    "ControllerSessionAdapter",
    "ControllerSessionJournal",
    "CoordinationDelta",
    "DeliveryReceipt",
    "InMemoryControllerSessionAdapter",
    "InMemoryControllerSessionJournal",
    "ObservationReceipt",
    "ResolveReceipt",
    "ResumeReceipt",
    "SessionReleaseReceipt",
    "matches_binding",
]
