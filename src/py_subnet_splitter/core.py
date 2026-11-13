"""Core splitting logic for py-subnet-splitter.

Everything here uses only :mod:`ipaddress` from the standard library, so the
package stays installable in offline environments.
"""

from __future__ import annotations

import ipaddress
from typing import List, Union

IPNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]


class SubnetSplitError(ValueError):
    """Base class for all errors raised by this package."""


class InvalidPrefixError(SubnetSplitError):
    """Raised when a prefix length cannot be used for splitting."""


class TooManySubnetsError(SubnetSplitError):
    """Raised when the requested number of subnets exceeds the address space."""


# IPv4 has 32 bits, IPv6 has 128.  The extra host bits in IPv6 are large enough
# that we can safely compute 2**extra without overflowing a Python int.
_MAX_PREFIX = {4: 32, 6: 128}


def _parse_network(cidr: str) -> IPNetwork:
    """Parse *cidr* into an IPv4Network or IPv6Network.

    ``strict=False`` is used deliberately: callers routinely pass a host
    address such as ``192.0.2.1/24`` and expect the containing network.
    """
    try:
        return ipaddress.ip_network(cidr, strict=False)
    except ValueError as exc:
        raise SubnetSplitError(f"cannot parse {cidr!r} as a network: {exc}") from exc


def _subnets_for_count(network: IPNetwork, count: int) -> List[IPNetwork]:
    if count <= 0:
        raise SubnetSplitError("count must be a positive integer")

    max_prefix = _MAX_PREFIX[network.version]
    extra = max_prefix - network.prefixlen
    if extra <= 0:
        raise InvalidPrefixError(
            f"network {network} has no room to split (prefix /{network.prefixlen})"
        )

    if count > (1 << extra):
        raise TooManySubnetsError(
            f"cannot split {network} into {count} subnets; only {1 << extra} available"
        )

    # We always split into the next power of two at least as large as *count*.
    # This keeps every returned subnet the same size, which is what "equal-sized"
    # means here.  The trade-off is documented in the README: a request for 3
    # subnets from a /24 yields four /26s, not three mixed-size blocks.
    new_prefix = network.prefixlen
    while (1 << (new_prefix - network.prefixlen)) < count:
        new_prefix += 1

    return list(network.subnets(new_prefix=new_prefix))


def _subnets_for_hosts(network: IPNetwork, hosts: int) -> List[IPNetwork]:
    if hosts <= 0:
        raise SubnetSplitError("hosts must be a positive integer")

    max_prefix = _MAX_PREFIX[network.version]
    extra = max_prefix - network.prefixlen
    if extra <= 0:
        raise InvalidPrefixError(
            f"network {network} has no room to split (prefix /{network.prefixlen})"
        )

    # ``hosts`` counts usable addresses.  IPv4 subnets lose two addresses to the
    # network and broadcast addresses; IPv6 subnets do not have a broadcast
    # address, but the all-zero interface identifier is conventionally reserved
    # as the subnet-router anycast address, so we still reserve one address.
    reserved = 2 if network.version == 4 else 1
    needed = hosts + reserved

    host_bits = 0
    while (1 << host_bits) < needed:
        host_bits += 1

    new_prefix = max_prefix - host_bits
    if new_prefix < network.prefixlen:
        raise TooManySubnetsError(
            f"{hosts} hosts do not fit in {network} (needs /{new_prefix})"
        )

    return list(network.subnets(new_prefix=new_prefix))


def split_by_count(cidr: str, count: int) -> List[IPNetwork]:
    """Split *cidr* into *count* equal-sized subnets.

    Returns a list of :class:`ipaddress.IPv4Network` or
    :class:`ipaddress.IPv6Network` objects.  The number returned is the smallest
    power of two greater than or equal to *count*, so ``split_by_count('10.0.0.0/24', 3)``
    returns four ``/26`` networks.

    Raises :class:`SubnetSplitError` if *count* is not positive,
    :class:`InvalidPrefixError` if the network is already a single host, and
    :class:`TooManySubnetsError` if *count* exceeds the available address space.
    """
    network = _parse_network(cidr)
    return _subnets_for_count(network, count)


def split_by_hosts(cidr: str, hosts: int) -> List[IPNetwork]:
    """Split *cidr* into the largest subnets that still hold *hosts* usable hosts.

    The returned list contains every subnet of that size within *cidr*.  For
    IPv4 the network and broadcast addresses are not counted as usable; for IPv6
    the subnet-router anycast address is reserved, so one address is subtracted.

    Raises :class:`SubnetSplitError` if *hosts* is not positive,
    :class:`InvalidPrefixError` if the network is already a single host, and
    :class:`TooManySubnetsError` if *hosts* cannot fit in *cidr*.
    """
    network = _parse_network(cidr)
    return _subnets_for_hosts(network, hosts)
