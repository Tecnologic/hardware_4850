# hardware_4850
48V at 50A with optimised colling

## KiCad project

The logic board and the power board are combined in a single **KiCad 10** project:
`hardware_4850.kicad_pro`.

| File | Content |
|---|---|
| `hardware_4850.kicad_sch` | Root sheet with the two board sheets |
| `logic.kicad_sch` | Logic board (sub-sheets `controller`, `interfaces`, `analog`, `current_filters`, `power_supply`) |
| `power.kicad_sch` | Power board (sub-sheet `phase`, used three times for phase A/B/C; sub-sheet `aux_leg`, used twice for the aux bridge) |
| `hardware_4850.kicad_pcb` | Both boards side by side: logic board on the left, power board on the right |
| `footprints/hardware_4850.pretty` | Project footprint library (shunt, enclosure RND 455-00370) |

Since both boards are in one PCB file, the net names are kept apart by the
schematic hierarchy (`/logic/...`, `/power/...`). The board-to-board connectors
(J101/J102 on the logic board, J103/J104 on the power board) are **not** joined
electrically in the schematic, so each board keeps its own nets.

## Aux bridge (in the schematic, not yet on the PCB)

The power board has two more half bridges (`aux_a`, `aux_b`, same parts as the
phases) with a low-side shunt each: an asymmetric H-bridge for the field
winding of an EESM (F1 = J111, F2 = J112) or a brake chopper for a PMSM (brake
resistor between DC+ = J113 and F2). J110 AUX carries their PWM signals and the
Kelvin pairs of the shunts to the logic board. The footprints are not placed on
the PCB yet (*Tools → Update PCB from Schematic*, then layout).

The logic board is to be redesigned around an STM32H743VIT6 (like the BCC):
[docs/h743_logic_board.md](docs/h743_logic_board.md).

## Production data

The production files of the PCB contain both boards. For separate production
data per board, the old KiCad 5 data is in `production/legacy_kicad5/`.

## Other folders

| Folder | Content |
|---|---|
| `datasheets/` | Component datasheets |
| `docs/` | Images (MCU pinning, board pictures), H743 logic board concept |
| `mechanical/` | DXF exports of the power board, cooler/enclosure drawings are in `footprints/` |
| `pinning/` | STM32CubeMX pinning (`.ioc`) of the STM32F730R8 |
| `sim/` | LTspice simulations of the current filters |
| `production/legacy_kicad5/` | Gerbers, BOMs and iBOM made with KiCad 5 before the merge (as manufactured) |

## Conversion notes (KiCad 5.1 → KiCad 10)

- The schematics were converted with the original KiCad 5 symbols (embedded in the
  schematic files). The MCU footprint pins match the PCB 1:1.
- The KiCad 5 schematic had other values than the PCB on the power board (the
  PCB was changed later). The schematic now follows the PCB: Q`x`01–Q`x`04
  `NCEP6080AG`, C`x`07/C`x`09 `56u`, R`x`03–R`x`10 `1R1`. Their old `Part#`
  order numbers were removed and still have to be filled in.
- Footprints `LFPAK56_ThermalVias-1` and `C_2220_5650Metric` and symbols
  `Device:CP`, `Device:Ferrite_Bead_Small`, `Device:Jumper_NO_Small` are no longer in
  the KiCad 10 standard libraries. The copies embedded in the project still work.
