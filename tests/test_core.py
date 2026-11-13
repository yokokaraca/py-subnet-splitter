import ipaddress
import unittest

from py_subnet_splitter import (
    InvalidPrefixError,
    SubnetSplitError,
    TooManySubnetsError,
    split_by_count,
    split_by_hosts,
)


class SplitByCountTests(unittest.TestCase):
    def test_exact_power_of_two(self):
        subnets = split_by_count("192.0.2.0/24", 4)
        self.assertEqual(len(subnets), 4)
        self.assertEqual(subnets[0], ipaddress.ip_network("192.0.2.0/26"))
        self.assertEqual(subnets[-1], ipaddress.ip_network("192.0.2.192/26"))
        self.assertTrue(all(s.prefixlen == 26 for s in subnets))

    def test_non_power_of_two_rounds_up(self):
        subnets = split_by_count("192.0.2.0/24", 3)
        self.assertEqual(len(subnets), 4)
        self.assertTrue(all(s.prefixlen == 26 for s in subnets))

    def test_count_one_returns_original(self):
        subnets = split_by_count("10.0.0.0/8", 1)
        self.assertEqual(subnets, [ipaddress.ip_network("10.0.0.0/8")])

    def test_ipv6(self):
        subnets = split_by_count("2001:db8::/32", 2)
        self.assertEqual(len(subnets), 2)
        self.assertEqual(subnets[0], ipaddress.ip_network("2001:db8::/33"))
        self.assertEqual(subnets[1], ipaddress.ip_network("2001:db8:8000::/33"))

    def test_host_bits_are_masked_off(self):
        subnets = split_by_count("192.0.2.7/24", 2)
        self.assertEqual(subnets[0], ipaddress.ip_network("192.0.2.0/25"))
        self.assertEqual(subnets[1], ipaddress.ip_network("192.0.2.128/25"))

    def test_zero_count_rejected(self):
        with self.assertRaises(SubnetSplitError):
            split_by_count("10.0.0.0/8", 0)

    def test_negative_count_rejected(self):
        with self.assertRaises(SubnetSplitError):
            split_by_count("10.0.0.0/8", -1)

    def test_too_many_subnets(self):
        with self.assertRaises(TooManySubnetsError):
            split_by_count("192.0.2.0/30", 8)

    def test_single_host_network_rejected(self):
        with self.assertRaises(InvalidPrefixError):
            split_by_count("192.0.2.1/32", 2)

    def test_bad_cidr_rejected(self):
        with self.assertRaises(SubnetSplitError):
            split_by_count("not-a-network", 2)


class SplitByHostsTests(unittest.TestCase):
    def test_ipv4_hosts_include_network_and_broadcast(self):
        # A /26 has 64 addresses; two are reserved, leaving 62 usable hosts.
        subnets = split_by_hosts("192.0.2.0/24", 62)
        self.assertEqual(len(subnets), 4)
        self.assertTrue(all(s.prefixlen == 26 for s in subnets))

    def test_ipv4_hosts_that_need_a_larger_block(self):
        subnets = split_by_hosts("192.0.2.0/24", 63)
        self.assertEqual(len(subnets), 2)
        self.assertTrue(all(s.prefixlen == 25 for s in subnets))

    def test_ipv4_small_host_count(self):
        # /30 has 4 addresses, 2 usable.  A /24 contains 64 /30s.
        subnets = split_by_hosts("192.0.2.0/24", 2)
        self.assertEqual(len(subnets), 64)
        self.assertTrue(all(s.prefixlen == 30 for s in subnets))

    def test_ipv6_reserves_one_address(self):
        # A /126 has 4 addresses; one is reserved, leaving 3 usable.
        subnets = split_by_hosts("2001:db8::/120", 3)
        self.assertEqual(len(subnets), 64)
        self.assertTrue(all(s.prefixlen == 126 for s in subnets))

    def test_ipv6_hosts_that_need_a_larger_block(self):
        subnets = split_by_hosts("2001:db8::/120", 4)
        self.assertEqual(len(subnets), 32)
        self.assertTrue(all(s.prefixlen == 125 for s in subnets))

    def test_zero_hosts_rejected(self):
        with self.assertRaises(SubnetSplitError):
            split_by_hosts("10.0.0.0/8", 0)

    def test_hosts_do_not_fit(self):
        with self.assertRaises(TooManySubnetsError):
            split_by_hosts("192.0.2.0/30", 3)

    def test_single_host_network_rejected(self):
        with self.assertRaises(InvalidPrefixError):
            split_by_hosts("192.0.2.1/32", 1)

    def test_bad_cidr_rejected(self):
        with self.assertRaises(SubnetSplitError):
            split_by_hosts("192.0.2.0/33", 1)


if __name__ == "__main__":
    unittest.main()
