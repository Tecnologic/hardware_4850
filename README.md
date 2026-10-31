# hardware_4850
48V at 50A with optimised colling

## KiCad project

The logic board and the power board are combined in a single **KiCad 10** project:
`hardware_4850.kicad_pro`.

| File | Content |
|---|---|
| `hardware_4850.kicad_sch` | Root sheet with the two board sheets |
| `logic.kicad_sch` | Logic board (sub-sheets `controller`, `interfaces`, `analog`, `current_filters`, `power_supply`) |
| `power.kicad_sch` | Power board (sub-sheet `phase`, used three times for phase A/B/C) |
| `hardware_4850.kicad_pcb` | Both boards side by side: logic board on the left, power board on the right |
| `footprints/hardware_4850.pretty` | Project footprint library (shunt, enclosure RND 455-00370) |

Since both boards are in one PCB file, the net names are kept apart by the
schematic hierarchy (`/logic/...`, `/power/...`). The board-to-board connectors
(J101/J102 on the logic board, J104/J105 on the power board) are **not** joined
electrically in the schematic, so each board keeps its own nets.

The production files of the PCB contain both boards. For separate production
data per board, the old KiCad 5 data is in `production/legacy_kicad5/`.

## Other folders

| Folder | Content |
|---|---|
| `datasheets/` | Component datasheets |
| `docs/` | Images (MCU pinning, board pictures) |
| `mechanical/` | DXF exports of the power board, cooler/enclosure drawings are in `footprints/` |
| `pinning/` | STM32CubeMX pinning (`.ioc`) of the STM32F730R8 |
| `sim/` | LTspice simulations of the current filters |
| `production/legacy_kicad5/` | Gerbers, BOMs and iBOM made with KiCad 5 before the merge (as manufactured) |

## Conversion notes (KiCad 5.1 → KiCad 10)

- The schematics were converted with the original KiCad 5 symbols (embedded in the
  schematic files). The MCU footprint pins match the PCB 1:1.
- Known differences between schematic and PCB that were already in the KiCad 5
  design (the PCB was changed later). Resolve with *Tools → Update PCB from
  Schematic* or *Update Schematic from PCB*:
  - Q201–Q204, Q301–Q304, Q401–Q404: schematic `BSC040N08`, PCB `NCEP6080AG`
  - C207, C209, C307, C309, C407, C409: schematic `47u`, PCB `56u`
  - R203–R210, R303–R310, R403–R410: schematic `21R`/`0R`, PCB `1R1`
  - The `Part#` field is only in the schematic.
- Footprints `LFPAK56_ThermalVias-1` and `C_2220_5650Metric` and symbols
  `Device:CP`, `Device:Ferrite_Bead_Small`, `Device:Jumper_NO_Small` are no longer in
  the KiCad 10 standard libraries. The copies embedded in the project still work.
