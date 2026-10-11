from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class SkippedItem:
    position: int
    context: str
    reason: str
    item_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'position': self.position,
            'context': self.context,
            'reason': self.reason,
            'id': self.item_id,
        }


@dataclass
class NormalizedTrack:
    position: int
    context: str
    raw: Any
    mapped: Optional[Dict[str, Any]] = None
    skipped: Optional[SkippedItem] = None


@dataclass
class CollectionAccounting:
    source_count: int = 0
    accepted_count: int = 0
    skipped_count: int = 0
    failed_download_count: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            'source_count': self.source_count,
            'accepted_count': self.accepted_count,
            'skipped_count': self.skipped_count,
            'failed_download_count': self.failed_download_count,
        }


@dataclass
class DownloadFailure:
    stage: str
    message: str
    link: Optional[str] = None
    item_id: Optional[str] = None


@dataclass
class DownloadRunResult:
    generated_items: int = 0
    converted_items: int = 0
    completed_items: int = 0
    generation_failures: List[DownloadFailure] = field(default_factory=list)
    queue_failures: List[DownloadFailure] = field(default_factory=list)


def _payload_id(track_data: Any) -> Optional[str]:
    if not isinstance(track_data, dict):
        return None
    for key in ('id', 'SNG_ID', 'TRACK_ID'):
        if key in track_data and track_data[key] is not None:
            return str(track_data[key])
    return None


def normalize_external_track_payload(track_data: Any, *, context: str, position: int, mapper: Callable[[Dict[str, Any]], Dict[str, Any]]) -> NormalizedTrack:
    """Normalize a Deezer payload without mutating caller-owned data."""
    if not isinstance(track_data, dict):
        skipped = SkippedItem(position=position, context=context, reason='payload is not a dictionary')
        return NormalizedTrack(position=position, context=context, raw=track_data, skipped=skipped)

    media = track_data.get('MEDIA')
    if isinstance(media, list) and len(media) == 0:
        skipped = SkippedItem(position=position, context=context, reason='empty MEDIA list', item_id=_payload_id(track_data))
        return NormalizedTrack(position=position, context=context, raw=track_data, skipped=skipped)

    try:
        mapped = mapper(deepcopy(track_data))
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        skipped = SkippedItem(position=position, context=context, reason=f'invalid payload ({exc})', item_id=_payload_id(track_data))
        return NormalizedTrack(position=position, context=context, raw=track_data, skipped=skipped)

    if not isinstance(mapped, dict):
        skipped = SkippedItem(position=position, context=context, reason='track mapper returned a non-dict value', item_id=_payload_id(track_data))
        return NormalizedTrack(position=position, context=context, raw=track_data, skipped=skipped)

    return NormalizedTrack(position=position, context=context, raw=track_data, mapped=mapped)
