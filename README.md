# hardware_4850
48 V at 50 A with optimised cooling

## KiCad project

The logic board and the power board are combined in a single **KiCad 10** project:
[`hardware_4850.kicad_pro`](hardware_4850.kicad_pro).

| File | Content |
|---|---|
| [`hardware_4850.kicad_sch`](hardware_4850.kicad_sch) | Root sheet with the two board sheets |
| [`logic.kicad_sch`](logic.kicad_sch) | Logic board: sub-sheets [`power_supply`](power_supply.kicad_sch) and [`controller`](controller.kicad_sch); `controller` has the sub-sheets [`interfaces`](interfaces.kicad_sch) and [`analog`](analog.kicad_sch) |
| [`power.kicad_sch`](power.kicad_sch) | Power board: sub-sheet [`phase`](phase.kicad_sch), used three times for phase A/B/C |
| [`hardware_4850.kicad_pcb`](hardware_4850.kicad_pcb) | Both boards side by side: logic board on the left, power board on the right |
| [`footprints/hardware_4850.pretty`](footprints/hardware_4850.pretty) | Project footprint library: enclosure RND 455-00370, and `LFPAK56_ThermalVias-1` and `C_2220_5650Metric`, which KiCad 10 no longer ships |

Since both boards are in one PCB file, the net names are kept apart by the
schematic hierarchy (`/logic/...`, `/power/...`). The board-to-board connectors
(J101/J102 on the logic board, J103/J104 on the power board) are **not** joined
electrically in the schematic, so each board keeps its own nets.

## Schematic ahead of the PCB

The schematic is ahead of the PCB. The logic board will be laid out again;
the PCB still shows the old F730 board.

- **MCU: STM32H743ZIT6** (LQFP144, Mouser `511-STM32H743ZIT6`) instead of the
  STM32F730R8. It sits on the `controller` sheet (now A3) and connects by net
  labels; the old wires end in labels of the same names. Added decoupling
  C613–C622; C603 is now 2.2 µF (VCAP). Pin plan and open points:
  [docs/h743_logic_board.md](docs/h743_logic_board.md).
- **Simple analog front end.** The op-amp filters of the logic board are gone
  (the three `current_filters` sheets with low pass and AC high pass per phase,
  and the U701 filters for Vdc and the bridge NTC). What is left on the `analog`
  sheet:
  - Ia/Ib/Ic: 220R / 2n2 RC from the INA240 outputs (R717–R719, C713–C715)
  - Vdc: divider R701/R702 with C702, then a 4k7 / 10n RC (R705/C704)
  - bridge NTC: pull-up R703 with C701, then a 4k7 / 10n RC (R704/C703)
  - motor temperature unchanged

  The filter values are a first guess.
- **No aux bridge.** The EESM excitation and brake chopper are out of scope for
  this board; a separate module will do that.

## Production data

The production files of the PCB contain both boards. For separate production
data per board, the old KiCad 5 data is in
[`production/legacy_kicad5/`](production/legacy_kicad5) (as manufactured, with
the op-amp filters, and the 2020 logic board BOM with prices).

## Other folders

| Folder | Content |
|---|---|
| [`datasheets/`](datasheets) | Component datasheets |
| [`docs/`](docs) | Pictures of the [logic board](docs/logic_board.png) and the [power board](docs/power_board.png) (old F730 boards), [H743 logic board concept](docs/h743_logic_board.md) |
| [`mechanical/`](mechanical) | DXF exports of the power board, the cooler drawing, [`enclosure/`](mechanical/enclosure) with STEP and DXF views of the RND 455-00370 |

## Conversion notes (KiCad 5.1 → KiCad 10)

- The schematics were converted with the original KiCad 5 symbols (embedded in the
  schematic files). The ERC lists the
  embedded symbols as different from the KiCad 10 library
  (`lib_symbol_mismatch`); *Update Symbols from Library* would change their
  graphics, so this is left as is.
- The KiCad 5 schematic had other values than the PCB on the power board (the
  PCB was changed later). The schematic now follows the PCB: Q`x`01–Q`x`04
  `NCEP6080AG`, C`x`07/C`x`09 `56u`, R`x`03–R`x`10 `1R1`. Their old `Part#`
  order numbers were removed and still have to be filled in.
- Parts that KiCad 10 dropped or renamed:
  - Footprints `LFPAK56_ThermalVias-1` and `C_2220_5650Metric` are now in the
    project library, copied from the PCB.
  - The 3D model of the 2220 capacitor now points to `C_2220_5750Metric`.
  - Symbols are relinked: `Device:CP` → `Device:C_Polarized`,
    `Device:Ferrite_Bead_Small` → `Device:FerriteBead_Small`,
    `Device:Jumper_NO_Small` → `Jumper:Jumper_2_Small_Open`.
