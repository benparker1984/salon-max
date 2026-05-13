# Multi-Site Terminal Simulator v1

This is the quickest way to prove one Salon Max business can support multiple sites and multiple tills before extra Raspberry Pi hardware arrives.

## Goal

Prove that:

- one business can have multiple sites
- each site can have its own terminal identity
- multiple terminals can pair into the same business
- shared customer data is available across those terminals

## What this does not prove

This simulator does not replace real hardware testing for:

- true simultaneous live usage on separate Pis
- separate network reliability and offline recovery on multiple devices
- device-level kiosk/UI behavior

It does prove the most important shared-cloud parts:

- pairing
- identity
- check-ins
- config fetch
- shared customer directory
- cloud correction feed

## Files

- `simulate_terminal_client.py`

## Recommended setup

Create:

- one business
- three sites
- three terminals

Example:

- Business: `Liverpool Test Group`
- Site 1: `Liscard`
- Site 2: `Birkenhead`
- Site 3: `Hoylake`

Then generate a pairing code for each terminal from the owner platform.

## Suggested local state files

Use one state file per simulated terminal:

- `sim-terminal-1.json`
- `sim-terminal-2.json`
- `sim-terminal-3.json`

## Pair three simulated terminals

```bash
python simulate_terminal_client.py pair --base-url http://100.71.173.23:5001 --pairing-code ABC123 --terminal-name "Sim Till 1" --state-file sim-terminal-1.json
python simulate_terminal_client.py pair --base-url http://100.71.173.23:5001 --pairing-code DEF456 --terminal-name "Sim Till 2" --state-file sim-terminal-2.json
python simulate_terminal_client.py pair --base-url http://100.71.173.23:5001 --pairing-code GHI789 --terminal-name "Sim Till 3" --state-file sim-terminal-3.json
```

## Check in each simulated terminal

```bash
python simulate_terminal_client.py check-in --state-file sim-terminal-1.json
python simulate_terminal_client.py check-in --state-file sim-terminal-2.json
python simulate_terminal_client.py check-in --state-file sim-terminal-3.json
```

## Fetch config for each terminal

```bash
python simulate_terminal_client.py config --state-file sim-terminal-1.json
python simulate_terminal_client.py config --state-file sim-terminal-2.json
python simulate_terminal_client.py config --state-file sim-terminal-3.json
```

## Prove shared customer data

Import or create customers into the shared business, then fetch the customer directory from each simulated terminal:

```bash
python simulate_terminal_client.py customers --state-file sim-terminal-1.json
python simulate_terminal_client.py customers --state-file sim-terminal-2.json
python simulate_terminal_client.py customers --state-file sim-terminal-3.json
```

If the same customers appear for all three, then the shared business customer directory is behaving centrally rather than per-device.

## Prove manual corrections are shared

After making a minute or balance correction in the owner platform, fetch corrections from each simulated terminal:

```bash
python simulate_terminal_client.py corrections --state-file sim-terminal-1.json
python simulate_terminal_client.py corrections --state-file sim-terminal-2.json
python simulate_terminal_client.py corrections --state-file sim-terminal-3.json
```

## Good proof sequence

1. Create one business with three sites.
2. Create one terminal under each site.
3. Pair three simulated terminals using three different pairing codes.
4. Check in all three.
5. Import a customer list into the business.
6. Fetch the customer directory from all three simulated terminals.
7. Make a manual customer minute correction in the owner platform.
8. Fetch corrections from all three simulated terminals.

## Next step after simulation

Once extra Raspberry Pis arrive:

1. keep the same multi-site business
2. replace each simulated terminal with a real paired Pi
3. repeat the same shared-customer and shared-correction proof with real hardware
