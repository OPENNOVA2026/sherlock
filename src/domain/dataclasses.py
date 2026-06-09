from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class InteractionTypes(str, Enum):
    REPOST = "repost"


class ModelTypes(str, Enum):
    POST = "post"


class InteractionNormalized(BaseModel):
    model_config = ConfigDict(frozen=True)

    created_at: datetime
    interaction_type: InteractionTypes
    model_type: ModelTypes
    research_id: str | None = None

    source_author_id: str
    source_author_username: str
    source_model_id: str

    target_author_id: str
    target_author_username: str
    target_model_id: str

    topic_id: str

    @field_validator("created_at")
    @classmethod
    def ensure_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")

        return value.astimezone(UTC)

    @field_validator("source_author_username", "target_author_username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


# Dataclasses
@dataclass(frozen=True)
class ComponentsResult:
    n_components: int
    sizes: list[int]
    membership: list[int]
    largest_component_size: int


@dataclass(frozen=True)
class GraphAnalysis:
    components: ComponentsResult


# Reports Dataclasses


@dataclass
class TextCatalog:
    title: str = "Estudio de actividad coordinada"
    intro_title: str = "Introducción"
    intro_research: str = "Investigación"
    intro_body: str = (
        "El objetivo de este documento es el estudio de la actividad coordinada detectada en la investigación descrita a continuación. "  # noqa: E501
        "Se incluye el estudio de los usuarios que constituyen un nodo relevante de coordinación y un estudio de los grupos más relevantes, "  # noqa: E501
        "donde se identifica para cada grupo cuáles son los usuarios que lo conforman y cuáles son los usuarios y mensajes que están siendo amplificados. "  # noqa: E501
        "Para detalles de la metodología consultar el anexo correspondiente."
    )
    research_placeholder: str = (
        "Aquí debe aparecer una breve descripción de la investigación: título, descripción, query y horizonte temporal (desde/hasta), "  # noqa: E501
        "así como el coeficiente de comportamiento inauténtico."
    )

    most_title: str = "Usuarios que articulan la coordinación"
    most_preamble: str = (
        "Los siguientes usuarios muestran un mayor grado de coordinación dentro de la investigación, ordenados por grado. "  # noqa: E501
        "Un grado de coordinación superior a 8 constituye una evidencia clara de coordinación."  # noqa: E501
    )
    most_empty: str = "No se han encontrado usuarios suficientemente coordinados."

    groups_title: str = "Principales grupos coordinados"
    groups_empty: str = "No se encontraron grupos coordinados significativos."
    groups_users_title: str = "Usuarios que conforman el grupo"
    groups_pushed_users_title: str = "Usuarios que están siendo impulsados por el grupo"
    groups_messages_title: str = "Mensajes que están siendo impulsados por el grupo"
    groups_no_messages: str = "No se encontraron mensajes impulsados por este grupo."

    methodology_title: str = "Metodología"
    methodology_body: str = "Esta sección describe de forma detallada la metodología utilizada para llevar a cabo el estudio de actividad coordinada."  # noqa: E501

    generated_on_prefix: str = "Generado en fecha "


@dataclass
class ReportConfig:
    tz: str = "Europe/Madrid"
    table_style: str = "Table Grid"
    user_col_width_inches: float = 5.2
    degree_col_width_inches: float = 0.8
    two_col_width_inches: float = 3.0
    message_author_col_width_inches: float = 1.6
    message_text_col_width_inches: float = 4.6
    default_cell_margin_inches: float = 0.08


@dataclass
class PublicMetrics:
    followers_count: Optional[int] = None
    tweet_count: Optional[int] = None
    like_count: Optional[int] = None


@dataclass
class UserProfile:
    username: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    metrics: PublicMetrics = field(default_factory=PublicMetrics)


@dataclass
class Message:
    author: Optional[UserProfile]
    text: str
    external_url: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class TopMessage:
    count: int
    message: Message


@dataclass
class CoordinationGroup:
    group_id: int
    size: int
    users: list[UserProfile] = field(default_factory=list)
    pushed_users: list[UserProfile] = field(default_factory=list)
    top_messages: list[TopMessage] = field(default_factory=list)


@dataclass
class CoordinatedAuthor:
    user: UserProfile
    coordination_degree: Optional[int] = None


@dataclass
class CoordinationAnalysis:
    request_title: Optional[str] = None
    request_description: Optional[str] = None
    request_query: Optional[str] = None
    time_from: Optional[str] = None
    time_to: Optional[str] = None
    inauthenticity_score: Optional[float] = None

    most_coordinated_authors: list[CoordinatedAuthor] = field(default_factory=list)
    coordination_groups: list[CoordinationGroup] = field(default_factory=list)
