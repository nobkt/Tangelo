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

"""Utility functions for DLPNO calculations."""


def pair_key(i: int, j: int) -> str:
    """Generate a canonical key for an orbital pair.
    
    Always orders indices so that i < j to ensure consistent keys
    regardless of input order.
    
    Args:
        i: First orbital index
        j: Second orbital index
        
    Returns:
        str: Canonical pair key in format "i_j" where i < j
    """
    if i > j:
        i, j = j, i
    return f"{i}_{j}"
