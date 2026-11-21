# py-subnet-splitter

Divide a CIDR block into N equal-sized subnets or subnets sized for a host count.

```python
from py_subnet_splitter import split_by_count, split_by_hosts

# Four /26 networks from a /24.
split_by_count("192.0.2.0/24", 4)
# [IPv4Network('192.0.2.0/26'), IPv4Network('192.0.2.64/26'),
#  IPv4Network('192.0.2.128/26'), IPv4Network('192.0.2.192/26')]

# Three requested subnets still yields four equal /26s.
split_by_count("192.0.2.0/24", 3)

# Subnets large enough for 62 usable IPv4 hosts: four /26s.
split_by_hosts("192.0.2.0/24", 62)

# IPv6 works the same way; one address per subnet is reserved.
split_by_hosts("2001:db8::/120", 3)
```

## Why this exists

Splitting a network by hand is easy to get wrong at the boundaries: host bits
creep into the result, a request for a non-power-of-two count silently produces
uneven blocks, and IPv6's lack of broadcast address changes the host arithmetic.
This library wraps `ipaddress` with two functions that make the intended
behaviour explicit.

The trade-off is deliberate: `split_by_count` always returns equal-sized
subnets, so a request for 3 subnets from a /24 returns 4 /26s rather than a mix
of /25 and /26 blocks. This keeps every returned subnet identical in size and
makes the result easy to reason about.

## Edge cases

A network with no host bits left (for example `192.0.2.1/32`) cannot be split
and raises `InvalidPrefixError`. Requesting more subnets or hosts than the
address space allows raises `TooManySubnetsError`. For IPv4, `split_by_hosts`
subtracts two addresses per subnet for the network and broadcast addresses; for
IPv6 it subtracts one for the subnet-router anycast address.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

