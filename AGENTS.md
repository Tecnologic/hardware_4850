# Agent rules for this repository

Jacobi is a KiCad 10 project (`jacobi.kicad_pro`, root sheet `jacobi.kicad_sch`).
These rules apply to every schematic change, by humans and by agents.

## Schematic sheet rules

1. **Every sheet is A4.** No A3 or larger. If a sheet does not fit on A4, split it
   into more sheets (new sheets are welcome).
2. **Hierarchy follows the boards.** `jacobi` -> `logic` (controller, power_supply)
   and `power` (connectors, interface, sense, phase_a/b/c). A sheet is either an
   overview (only sheet blocks and notes) or a leaf (only parts).
3. **Every sheet has a title block and notes.** Fill in `title`, `date`, `rev`,
   `company` and add a bold heading plus short text notes on the sheet itself:
   what the sheet does, key parts and values, what connects to it. Put notes in free
   space, never over parts or wires.
4. **One function per sheet.** Keep a sheet readable at a glance: one stage or
   one connector group. Repeated circuits (the three phases) use one file with
   several sheet instances.
5. **Signals leave a sheet through hierarchical labels**, named the same as the net
   on the parent sheet. Supplies use power symbols (`+BATT`, `GNDPWR`, `+12P`, `GND`,
   `+3V3`, `GNDD`, ...). Do not use global labels for signals.
6. **Overview sheets** connect sheet pins with a short wire stub and a net label
   (same name on both ends). No long cross-sheet wire spaghetti.
7. **Wiring style.** Everything on the 1.27 mm grid. Wire directly to pins where it
   is short and clear. Use a net label or a power symbol where a wire would cross
   others. Flow left to right: inputs left, outputs right, supply up, ground down.
   Put a junction on every T connection, including at the end of a bus.
8. **ERC clean.** Every supply net has a `PWR_FLAG` once. No new ERC warnings or
   errors compared to the commit before.
9. **Keep grounds separate.** `GND`/`GNDPWR` (power board), `GNDD`/`GNDA` (logic board)
   are different nets. Do not merge them.

## Rules for refactors

- A refactor must not change the netlist. Export it before and after with
  `kicad-cli sch export netlist --format kicadsexpr` and compare the pin sets of
  every net (net names may change because of the hierarchy path, pin sets may not).
- Keep reference designators and sheet UUIDs of existing sheets (the PCB and the
  project sheet list depend on them). Add new sheets to `sheets` in `jacobi.kicad_pro`.
- Number pages in reading order: root, logic tree, power tree.
- Check the result visually: `kicad-cli sch export pdf jacobi.kicad_sch`, then look
  at every changed page.
- Run `kicad-cli sch erc jacobi.kicad_sch` and compare with the baseline.

## PCB rules

- **Do not move mounting holes H101-H107 (except H106).** They line up with the
  other board when the logic board sits on top of the power board; the boards are
  joined by standoffs through these holes. Move neighbouring parts instead. The
  locked N101 corner pads stay put as well.

## Other

- Datasheets go to `datasheets/`, footprints to `footprints/jacobi.pretty`.
- Commit messages: short imperative subject, then a line or two of why.
