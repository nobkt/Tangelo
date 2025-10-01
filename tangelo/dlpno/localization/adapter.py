# Copyright SandboxAQ 2021-2024.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Placeholder localization adapter for DLPNO.

Design goals (scaffolding phase):
- No heavy dependencies (PySCF) imported yet.
- Provide stable, minimal API surface:
    * list_supported_methods() -> list[str]
    * get_localized_orbitals(mf, method='pipek') -> raises NotImplementedError
- Deterministic behavior, no side effects on import.
- Clear error messages guiding future implementation tasks.

Future phases will:
- Integrate PySCF localization (Boys, Pipek–Mezey, possibly Edmiston–Ruedenberg).
- Return localized orbital coefficient matrices and orbital ordering.
"""

from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # Only for type checkers; avoids runtime dependency.
    import numpy as np  # noqa: F401


__all__ = [
    "list_supported_methods",
    "get_localized_orbitals",
]


def list_supported_methods() -> List[str]:
    """Return the canonical list of supported localization method identifiers.

    Returns:
        list[str]: Ordered list of method names (lowercase).
    """
    return ["boys", "pipek"]


def get_localized_orbitals(mf, method: str = "pipek") -> Tuple[List[int], "np.ndarray"]:
    """Placeholder for orbital localization interface.

    Args:
        mf: Mean-field / SCF-like object (e.g., PySCF SCF object) or a placeholder.
        method (str): Localization method identifier (case-insensitive expected
            to match one of list_supported_methods()).

    Returns:
        tuple[list[int], np.ndarray]: (orbital_order, localized_coeff_matrix)
            Not returned in this placeholder (always raises).

    Raises:
        NotImplementedError: Always, until localization integration is implemented.
    """
    if method is None:
        raise NotImplementedError(
            "Localization method not specified. Supported methods: "
            f"{', '.join(list_supported_methods())}"
        )

    norm_method = method.lower()
    supported = list_supported_methods()

    if norm_method not in supported:
        raise NotImplementedError(
            f"Localization method '{method}' is not implemented in scaffolding phase. "
            f"Supported placeholders: {', '.join(supported)}. "
            "Future implementation will integrate PySCF localization routines."
        )

    raise NotImplementedError(
        f"get_localized_orbitals(method='{method}') placeholder. "
        "Integration with PySCF (Boys / Pipek–Mezey) will be provided in a later phase."
    )