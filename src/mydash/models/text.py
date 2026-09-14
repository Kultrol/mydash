"""Text that came from a provider, made safe to print.

Headlines, place names, and error bodies arrive from servers mydash does not
control, and Rich passes most control characters straight through to the
terminal. An ESC in a headline can clear the screen, retitle the window, or
write to the clipboard (OSC 52); a bidi override can make a line read
differently from what it says. :func:`clean_text` removes both, and
:data:`CleanStr` applies it as models are built — cached payloads are parsed
through the same models, so they are covered too.
"""

from __future__ import annotations

from typing import Annotated, Final

from pydantic import AfterValidator

# Line breaks and tabs become spaces so a headline stays on one line. Every
# other C0/C1 control character, DEL, and the bidi embedding, override, and
# isolate characters are dropped.
_WHITESPACE: Final = (ord("\t"), ord("\n"), ord("\r"))
_CONTROLS: Final = (*range(0x00, 0x20), *range(0x7F, 0xA0))
_BIDI_CONTROLS: Final = (*range(0x202A, 0x202F), *range(0x2066, 0x206A))
_TRANSLATE: Final[dict[int, str | None]] = {
    **{codepoint: None for codepoint in (*_CONTROLS, *_BIDI_CONTROLS)},
    **{codepoint: " " for codepoint in _WHITESPACE},
}


def clean_text(value: str) -> str:
    """Return *value* without terminal control or bidi override characters."""
    return value.translate(_TRANSLATE)


#: A string from outside mydash, cleaned when the model is validated.
CleanStr = Annotated[str, AfterValidator(clean_text)]
