"""Domain services layer (target architecture).

Commands should eventually call services here instead of importing client factories
directly. What belongs in a service vs. staying in the client layer is still TBD —
likely orchestration, shared config, and domain-facing APIs while clients keep HTTP
and parsing.
"""