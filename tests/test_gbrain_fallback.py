from app.core.config import Settings
from app.memory.gbrain import LocalGBrain
from pytest import MonkeyPatch


class FakeQdrantClient:
    def __init__(self, url: str, prefer_grpc: bool = False) -> None:
        self.url = url
        self.prefer_grpc = prefer_grpc

    def get_collections(self) -> object:
        raise RuntimeError("qdrant is down")


class FakeSession:
    pass


def test_local_gbrain_disables_vector_index_when_qdrant_is_unavailable(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.memory.gbrain.QdrantClient", FakeQdrantClient)

    gbrain = LocalGBrain(FakeSession(), Settings(QDRANT_URL="http://localhost:6333"))  # type: ignore[arg-type]

    assert gbrain.vector_index_available is False
