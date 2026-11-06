# Jacobi
36 V / 45 A (battery side, 100 A peak phase current) drive hardware of the [unimoc](https://github.com/Tecnologic/unimoc)
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
| **Jacobi** | **36 V / 45 A drive (this board, H7)** | Moritz Hermann Jacobi, first practical electric motor (1834) and electric boat on the Neva (1838) |
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

## Ratings and limits

What the hardware can do and where it stops. The numbers come from the
datasheets and rough loss and thermal estimates (calculations below), not from
measurements on a test bench. The reference load is the kids' quad: an MY1020
1600 W BLDC on 3 × 12 V lead-acid, which the controller already drives with
80 A peak phase current.

| | Rating | Limited by |
|---|---|---|
| Battery | **3 × 12 V lead-acid (36 V)**, up to 44 V while charging; Li-ion up to 10S (42 V) | 60 V FETs (NCEP6080AG), see below |
| Enable input (J501 pin 3 against pin 4) | **12–40 V**, switched battery voltage; 1–4 mA through a TLP291 optocoupler, 3750 Vrms isolation | input resistor R1115 (10k, 1206): 0.19 W at 44 V, 0.25 W rating |
| Battery current | **~45 A** (1600 W at 36 V) for minutes in still air; continuous only with better cooling | housing to air: 1600 W needs about 58 A peak phase current |
| Phase current, peak | **100 A** for seconds | motor saturation, FET losses |
| Phase current, continuous | **~50 A peak** in still air; with the housing bolted to a frame or in airflow, the 100 A motor limit comes first | housing to air (about 2.5 K/W) |
| Overcurrent trip | **120–130 A** | current sensing range ±160 A |
| Not suitable for | 48 V systems (13S/14S Li-ion, 4 × 12 V lead-acid) | 60 V FET rating |

### Target motors

| Motor | Saturation (peak phase current) | Fit |
|---|---|---|
| 60 mm stator motors | ~100 A | up to the rating |
| Hoverboard hub motors | ~55 A | about a third of the current range, fine resolution |
| MY1020 1600 W, 36 V (kids' quad) | not published, estimated 80–100 A | runs today at 80 A peak |

The MY1020 has no published saturation data. It can be measured with the
controller: lock the rotor, run a DC current on the d or q axis in steps
(0, 20, 40 … 120 A) and measure L = V / (di/dt) with a small voltage pulse.
Saturation starts where L falls by 20–30 %. Above that current the motor gives
little extra torque and mostly heat, so it is the useful current limit.

### Bridge voltage: why 36 V

The bridge uses **NCEP6080AG** (NCE, LCSC `C182469`, DFN5×6-8L), two in
parallel per switch, 12 per board. They are in stock and cost much less than
an 80 V part. From the LCSC product page (the datasheet PDF was not
reachable): 60 V, 80 A, R_DS(on) < 4.0 mΩ at 10 V (3.5 mΩ typ),
< 5.0 mΩ at 4.5 V, Qg 67 nC, Coss 680 pF, 85 W, Tj up to 150 °C.

| Battery | Max voltage | Margin to 60 V |
|---|---|---|
| 3 × 12 V lead-acid | ~44 V (charging) | 16 V: **fine** |
| 10S Li-ion | 42 V | 18 V: **fine** |
| 13S Li-ion | 54.6 V | 5 V: switching overshoot alone can use that, **no** |
| 14S Li-ion / 4 × 12 V | 58.8 V / ~58 V | **no** |

For 48 V the bridge needs 80 V FETs in the same footprint, e.g. the Infineon
**BSC040N08NS5** (80 V, 4.0 mΩ max, 121 A, marking `040N08NS`), which sits on
one of the existing prototype boards. Its R_DS(on) is the same as the NCE part;
its lower gate charge (43 nC) only shortens the switching edges a little. The
rest of the board already handles 48 V: the LM5008 supply runs from the battery
up to 95 V, and the voltage dividers reach 73.8 V full scale.

### Bridge losses

Two FETs in parallel per switch, sine current, 36 V, 20 kHz PWM, about 45 ns
switching edges (LM5109B at about 1 A into 2 × 67 nC, 1R1 gate resistors).
R_DS(on) is 4.0 mΩ max × 1.6 for Tj = 125 °C ≈ 6.4 mΩ. The factor 1.6 is
taken from the BSC040N08NS5 curve because the NCE datasheet was not
available; check it once the datasheet is in `datasheets/`.

| Phase current (peak) | Loss per FET | Loss per phase | Whole bridge |
|---|---|---|---|
| 50 A | ~1.3 W | ~5 W | ~16 W |
| 80 A | ~3 W | ~12 W | ~36 W |
| 100 A | ~4.5 W | ~18 W | ~54 W |

Conduction per FET is I_rms² × R_DS(on) / 8 (the phase current splits over two
FETs, and high and low side each conduct about half the time). Switching per
phase is ½ × V × I_avg × (t_on + t_off) × f_PWM with I_avg = 2/π × I_peak.

Using one FET per switch instead of two would save 6 FETs and about 180 mm²,
but it doubles the conduction loss at the same current (about 16 W per FET at
100 A peak). In the closed housing that comes straight off the continuous
current, so the board keeps two per switch.

### PCB manufacturing

The board is made by JLCPCB: 4 layers, **1 oz copper** on all layers (outer and
inner), standard process. The design rules in `jacobi.kicad_pro` follow the
[JLCPCB 4-layer capabilities](https://jlcpcb.com/capabilities/pcb-capabilities):

| Rule | Value |
|---|---|
| Min track width / clearance | 0.1 mm / 0.1 mm |
| Min via (diameter / drill) | 0.45 mm / 0.2 mm, annular ring 0.125 mm |
| Min copper to board edge | 0.3 mm |
| Min hole to hole / hole clearance | 0.25 mm |
| Min silk text | 1.0 mm high, 0.15 mm line |

Net classes set the routing defaults (the high-current nets use pours, the track
width is only for stubs and pad entries):

| Class | Track / clearance / via | Nets |
|---|---|---|
| Power | 1.0 / 0.25 / 0.8 ⌀ 0.4 mm | +BATT, GNDPWR, phase and switch nodes |
| GateDrive | 0.5 / 0.2 / 0.6 ⌀ 0.3 mm | +12P, gate, HO/LO/HS/VSS, bootstrap |
| Dig Supply | 0.4 / 0.2 / 0.6 ⌀ 0.3 mm | +12V, +3V3, +1V2, +BATT_LOGIC, GNDD, buck nodes |
| Analog Supply | 0.4 / 0.2 / 0.6 ⌀ 0.3 mm | +3.3VA, +3.3VADC, GNDA, GND |
| Analog | 0.2 / 0.2 / 0.45 ⌀ 0.2 mm | current and voltage sense, temperature, ADC inputs |
| USB | 0.2 / 0.2 mm, pair gap 0.15 mm | USB_DP, USB_DM (impedance not yet checked) |
| Default | 0.15 / 0.15 / 0.45 ⌀ 0.2 mm | everything else |

### Cooling

The power board sits on an aluminium block the size of the board, which is
mounted to the floor of the G113T housing (115 × 90 mm). Today the bottom
copper is covered by solder mask, with thermal paste to the block and a
thermal pad to the housing.

| Step (per FET unless noted) | Rth | Note |
|---|---|---|
| Junction → case | ~1 K/W | datasheet class value |
| **Thermal vias** | **~3.3 K/W** | 38 × 0.4 mm, 25 µm plating: the largest step from FET to block |
| Solder mask + paste | ~1 K/W | 20 µm mask, 50 µm paste over about 100 mm² |
| Junction → block | **~5.5 K/W** | about 17 K at 80 A peak, about 25 K at 100 A peak |
| Block → housing (pad, whole board) | 0.05–0.1 K/W | 3–5 K at 54 W |
| **Housing → air (whole board)** | **~2–3 K/W** | 0.043 m² of housing in still air: **sets the continuous current** |

At 80 A peak the bridge loses about 36 W. In still air the housing would end up
far above any sensible temperature; it works because the peaks are short. The
block and housing hold about 600 J/K (10 mm block assumed), a time constant of
about 25 minutes, so 54 W (100 A peak) heats them by about 5 K per minute.

Continuous current for a block at ≤ 80 °C at 40 °C ambient (40 K):

| Housing to air | Allowed loss | Continuous phase current |
|---|---|---|
| Still air, ~2.5 K/W | ~16 W | ~50 A peak |
| Bolted to the frame or in airflow, ~0.5 K/W | ~80 W | ~120 A peak, so the 100 A motor limit comes first |

Improvements, biggest first:

1. **Housing to air.** Bolt the housing to the vehicle frame or a metal plate
   with paste, or add fins or airflow. This is worth more than all other steps
   together.
2. **Thermal vias.** Filled and capped vias (VIPPO) under the drain pad, as many
   as fit: about half the 3.3 K/W. The board stays 1 oz copper; the currents are
   carried by pours on all four layers, not by thicker copper.
3. **Block to housing.** Thin paste on flat surfaces instead of the thermal pad,
   screws near the FET rows.
4. **Copper spreading.** Large drain pours under each FET on the bottom and
   inner layers.

**Keep the isolation.** The bottom copper under the high-side FETs is at
+BATT, under the low-side FETs it is the phase node, and the block conducts.
The solder mask is the only insulation today. Opening the mask needs a defined
insulator instead (25 µm polyimide film or a 0.15–0.2 mm ceramic-filled pad);
thermally that is about the same as mask and paste, but the isolation is
reliable. Avoid metal-filled pastes there.

### Current sensing

One 0.5 mΩ 3920 shunt per phase (Yezhan DSLR-M-5-0.5F) in the phase output,
with an INA240A1 (gain 20):

| | |
|---|---|
| Range | 1.6 V / (20 × 0.5 mΩ) = **±160 A**, 10 mV/A |
| Overcurrent trip | 120–130 A, above the 100 A motor saturation |
| Offset | 25 µV max at the input = 0.05 A; calibrated at start, drift 0.25 µV/K |
| Resolution | about 0.08 A at 12 effective bits |
| Shunt loss | 1.6 W at 80 A peak, 2.5 W at 100 A peak (9 W part) |

Other combinations that were considered:

| Shunt + INA240 | Range | Why not |
|---|---|---|
| 0.4 mΩ + A1 | ±200 A | only needed for currents above 130 A, which the motors cannot use |
| 0.2 mΩ + A2 | ±160 A | same scaling, but 2.5× the offset in amps, and the A2 costs 1.60 € vs 0.25 € for a shunt |
| 0.2 mΩ + A1 | ±400 A | coarse at light load (about 0.2 A noise) |

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
- **PWM_EN through an optocoupler.** The PWM_EN jumper J1102 is gone. The
  enable input is a TLP291 (U1102) on the `interfaces` sheet that pulls PE15
  high. J501 (`Enable`, now 4-pin JST PH) carries, from pin 1: `+BATT_LOGIC`
  (battery +), the LM5008 supply (VIN), `PWM_EN_IN` (opto LED +, **12–40 V**)
  and `PWM_EN_RTN` (opto LED return, battery −). The LED path is 10k (R1115)
  with 10n (C1108) across the LED and a 1N4148W (D1105) against reverse
  polarity. The output has a 510R collector resistor, a 10k pulldown (R1116)
  and 10n (C1109). `PWM_EN_RTN` is not connected to `GNDD`, so the enable
  line is isolated and its current stays in its own wire pair, which keeps
  noise out on a cart with four drives. Keep the LED side clear of copper from
  the output side under U1102 (5 mm creepage). On the bench bridge pins 1–2,
  put battery + on pin 3 and battery − on pin 4. On the cart switch pin 2
  (logic) and pin 3 (phases).
- **`+48V` is now `+BATT_LOGIC`.** The board is no longer 48 V compatible
  (60 V FETs), so the logic board supply net (J101 pin 1, J501 pin 1) is named
  after the battery. It stays a separate net from `+BATT` on the power board.
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
| [`nucleo_adapter/`](nucleo_adapter) | Bench adapter: a NUCLEO-H743ZI drives the legacy 4850 power board in place of the old logic board (own KiCad project, see its [README](nucleo_adapter/README.md)) |

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
