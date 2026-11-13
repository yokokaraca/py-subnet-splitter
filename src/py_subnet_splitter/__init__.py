"""py-subnet-splitter: split CIDR blocks into equal-sized subnets.

This package exposes a small, dependency-free API for dividing an IPv4 or IPv6
network into either N equal-sized subnets or subnets large enough to hold a
given number of usable hosts.
"""

from .core import (
    InvalidPrefixError,
    SubnetSplitError,
    TooManySubnetsError,
    split_by_count,
    split_by_hosts,
)

__all__ = [
    "InvalidPrefixError",
    "SubnetSplitError",
    "TooManySubnetsError",
    "split_by_count",
    "split_by_hosts",
]
