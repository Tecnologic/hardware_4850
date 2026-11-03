# Jacobi
48 V / 50 A (battery side, 80 A peak phase current) drive hardware of the [unimoc](https://github.com/Tecnologic/unimoc)
project, with optimised cooling. Jacobi is the motor controller (logic board and
power board); the firmware lives in the unimoc repository.

| | |
|---|---|
| Board directory (firmware) | `boards/unimoc/jacobi/` |
| Board name | `unimoc_jacobi` |
| Cyphal node name | `org.unimoc.jacobi` |
| EESM variant | Jacobi E |

Formerly `hardware_4850`.

### Naming

The unimoc nodes are named after inventors. Moritz Hermann Jacobi built the
first practical electric motor (1834, Königsberg) and drove a boat on the Neva
with it (1838): the first electric motor put to practical use as a drive, which
is what this board is for.

**Drives**

| Name | Class | Who |
|---|---|---|
| Barlow | small drive | Peter Barlow, whose "Barlow's wheel" (1822) was one of the first electric motors: tiny but turning |
| **Jacobi** | **48 V / 50 A drive (this board, H7)** | Moritz Hermann Jacobi, first practical electric motor (1834) and electric boat on the Neva (1838) |
| Dolivo | big drive | Michail Dolivo-Dobrowolsky invented the three-phase motor and the three-phase system (AEG, 1889), the basis of every FOC drive |

**Other nodes**

| Name | Role | Who |
|---|---|---|
| Zuse | VDC | Konrad Zuse built the first working programmable computer, so he's the brain |
| Drais | Pedal generator | Karl Drais invented the Laufmaschine (1817), the ancestor of the bicycle, powered by your own feet |
| Mercator | Steering | the map maker everyone navigates by |
| Gutenberg | Display | made information visible to everyone |
| Volta | BMS / battery | invented the battery (the voltaic pile, 1800) |
| Otto | Throttle | Nikolaus Otto, of the Otto engine: the classic gas pedal |

## KiCad project

The logic board and the power board are combined in a single **KiCad 10** project:
[`jacobi.kicad_pro`](jacobi.kicad_pro).

| File | Content |
|---|---|
| [`jacobi.kicad_sch`](jacobi.kicad_sch) | Root sheet with the two board sheets |
| [`logic.kicad_sch`](logic.kicad_sch) | Logic board: sub-sheets [`power_supply`](power_supply.kicad_sch) and [`controller`](controller.kicad_sch); `controller` has the sub-sheets [`interfaces`](interfaces.kicad_sch) and [`analog`](analog.kicad_sch) |
| [`power.kicad_sch`](power.kicad_sch) | Power board: sub-sheet [`phase`](phase.kicad_sch), used three times for phase A/B/C |
| [`jacobi.kicad_pcb`](jacobi.kicad_pcb) | Both boards side by side: logic board on the left, power board on the right |
| [`footprints/jacobi.pretty`](footprints/jacobi.pretty) | Project footprint library: enclosure RND 455-00370, the Kelvin footprint of the phase shunt `R_Shunt_Yezhan_DSLR-5_3920_Kelvin`, and `LFPAK56_ThermalVias-1` and `C_2220_5650Metric`, which KiCad 10 no longer ships |

Since both boards are in one PCB file, the net names are kept apart by the
schematic hierarchy (`/logic/...`, `/power/...`). The board-to-board connectors
(J101/J102/J111 on the logic board, J103/J104/J110 on the power board) are **not** joined
electrically in the schematic, so each board keeps its own nets.

## Schematic ahead of the PCB

The schematic is ahead of the PCB. The logic board will be laid out again;
the PCB still shows the old F730 board.

- **MCU: STM32H743VIT6** (LQFP100, 2 MB flash, LCSC `C114409`) instead of the
  STM32F730R8. It sits on the `controller` sheet (now A3) and connects by net
  labels; the old wires end in labels of the same names. Added decoupling
  C613–C622; C603 is now 2.2 µF (VCAP). Pin plan and open points:
  [docs/h743_logic_board.md](docs/h743_logic_board.md).
- **Simple analog front end.** The op-amp filters of the logic board are gone
  (the three `current_filters` sheets with low pass and AC high pass per phase,
  and the U701 filters for Vdc and the bridge NTC). What is left on the `analog`
  sheet:
  - Ia/Ib/Ic: 220R / 2n2 RC from the INA240 outputs (R717–R719, C713–C715)
  - Va/Vb/Vc: 220R / 2n2 RC (R720–R722, C716–C718), the same as the currents
  - Vdc: 4k7 / 10n RC (R705/C704)
  - +12P (gate driver supply): 4k7 / 10n RC (R723/C719)
  - bridge NTC: pull-up R703 with C701, then a 4k7 / 10n RC (R704/C703)
  - motor temperature unchanged

  The filter values are a first guess.
- **Voltage sensing on the power board.** The dividers for the phase voltages
  and Vdc (47k / 2k2 0.1 %, with 1 nF; R101–R108, C101–C104) sit on the power
  board and go to the logic board over a third 2×5 connector, J110 → J111
  (VSENSE). The old Vdc divider R701/R702/C702 on the logic board is gone.
- **Gate driver supply sense.** A 10k / 2k2 divider (R109/R110, C105) on +12P
  at the drivers goes over pin 3 of the PWM connector (J103 → J101) to PC5. No
  12 V is routed to the analog part.
- **Power board present.** J110 pin 9 is GND on the power board; on the logic
  board it is pulled up (R612, 10k) to PE4 (`PWR_DET`, low = present).
- **Bridge NTC to GND on the power board.** TH101 has its low side on the power
  board GND; only the high side goes through J104 pin 8. J104 pin 10 is now GND.
- **One shunt per phase.** 0.5 mΩ 3920 (Yezhan DSLR-M-5-0.5F, LCSC
  `C41382689`) with Kelvin sense pads instead of three 2 mΩ 2512 in
  parallel, read by an INA240A1 (gain 20): ±160 A.
- **USB-C** instead of mini-B: HRO TYPE-C-31-M-12 (LCSC `C165948`, 16 pins,
  USB 2.0), 5k1 on CC1/CC2 (R613/R614) as a device. SBU not connected.
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

- All symbols are updated from the KiCad 10 library; no KiCad 5 symbol
  graphics are left. The unused `SolderJumper_2_Open` was dropped. The old
  bitmaps of the other board on the `logic` and `power` sheets are removed.
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
