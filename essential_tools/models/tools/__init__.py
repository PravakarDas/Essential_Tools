from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass(frozen=True)
class Tool:
    slug: str
    title: str
    desc: str
    category: str
    processor: Optional[Callable] = None  # Callable[[Job, List[str]], Dict[str, Any]]


_REGISTRY: Dict[str, Tool] = {}


def register(tool: Tool) -> None:
    _REGISTRY[tool.slug] = tool


def get(slug: str) -> Optional[Tool]:
    return _REGISTRY.get(slug)


def all_tools() -> List[Tool]:
    return list(_REGISTRY.values())


# Implemented tools
from . import merge as _merge  # noqa: E402
from . import split as _split  # noqa: E402
from . import rotate as _rotate  # noqa: E402
from . import compress as _compress  # noqa: E402
from . import pdf_to_word as _pdf_to_word  # noqa: E402
from . import pdf_to_pptx as _pdf_to_pptx  # noqa: E402
from . import word_to_pdf as _word_to_pdf  # noqa: E402
from . import pptx_to_pdf as _pptx_to_pdf  # noqa: E402
from . import pdf_to_images as _pdf_to_images  # noqa: E402
from . import images_to_pdf as _images_to_pdf  # noqa: E402
from . import sign as _sign  # noqa: E402
from . import watermark as _watermark  # noqa: E402

register(
    Tool(
        slug="merge",
        title="Merge PDF",
        desc="Combine multiple PDFs into one.",
        category="organize",
        processor=_merge.process,
    )
)

register(
    Tool(
        slug="split",
        title="Split PDF",
        desc="Extract page ranges into new files.",
        category="organize",
        processor=_split.process,
    )
)

register(
    Tool(
        slug="rotate",
        title="Rotate PDF",
        desc="Rotate pages 90/180/270.",
        category="organize",
        processor=_rotate.process,
    )
)

register(
    Tool(
        slug="compress",
        title="Compress PDF",
        desc="Reduce file size with presets.",
        category="optimize",
        processor=_compress.process,
    )
)

# Converters (implemented)
register(
    Tool(
        slug="pdf-to-word",
        title="PDF -> Word",
        desc="Convert PDF to DOCX.",
        category="convert",
        processor=_pdf_to_word.process,
    )
)

register(
    Tool(
        slug="pdf-to-pptx",
        title="PDF -> PowerPoint",
        desc="Pages to slides.",
        category="convert",
        processor=_pdf_to_pptx.process,
    )
)

# UI-only placeholders (not implemented yet)
register(
    Tool(
        slug="word-to-pdf",
        title="Word -> PDF",
        desc="DOC/DOCX to PDF.",
        category="convert",
        processor=_word_to_pdf.process,
    )
)
register(
    Tool(
        slug="pptx-to-pdf",
        title="PowerPoint -> PDF",
        desc="PPT/PPTX to PDF.",
        category="convert",
        processor=_pptx_to_pdf.process,
    )
)
register(
    Tool(
        slug="pdf-to-images",
        title="PDF -> Images",
        desc="Export pages as PNGs (ZIP)",
        category="convert",
        processor=_pdf_to_images.process,
    )
)
register(
    Tool(
        slug="images-to-pdf",
        title="Images -> PDF",
        desc="One page per image.",
        category="convert",
        processor=_images_to_pdf.process,
    )
)
register(
    Tool(
        slug="sign",
        title="Sign PDF",
        desc="Place signature image onto PDF pages.",
        category="secure",
        processor=_sign.process,
    )
)
register(
    Tool(
        slug="watermark",
        title="Watermark",
        desc="Add image or text watermark.",
        category="edit",
        processor=_watermark.process,
    )
)
register(Tool(slug="html-to-pdf", title="HTML -> PDF", desc="URL or HTML to PDF.", category="convert"))
register(Tool(slug="unlock", title="Unlock PDF", desc="Remove password (with key).", category="secure"))
register(Tool(slug="protect", title="Protect PDF", desc="Add password & permissions.", category="secure"))
