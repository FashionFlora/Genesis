"""Toy test of local synaptic tags capturing a transient shared resource."""

WINDOW = 3


def outcome(delay, tag_enabled=True, unlimited_tag=False):
    tag_until = WINDOW if tag_enabled else -1
    if unlimited_tag and tag_enabled:
        tag_until = 10**9
    resource_arrives = delay
    return int(resource_arrives <= tag_until)


def main():
    delays = range(0, 8)
    intact = [outcome(delay) for delay in delays]
    no_tag = [outcome(delay, tag_enabled=False) for delay in delays]
    unlimited = [outcome(delay, unlimited_tag=True) for delay in delays]
    print(f"window={WINDOW}; delays=0..7")
    print(f"intact durable={sum(intact)}/8 outcomes={intact}")
    print(f"no_local_tag durable={sum(no_tag)}/8 outcomes={no_tag}")
    print(f"unlimited_tag durable={sum(unlimited)}/8 outcomes={unlimited}")


if __name__ == "__main__":
    main()
