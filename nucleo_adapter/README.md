# Nucleo adapter for the legacy 4850 power board

A bench adapter that lets a **NUCLEO-H743ZI** (first revision, MB1137, silicon
rev. Y) drive the **legacy 4850 power board**, the one ordered on 2019-11-20
(`production/legacy_kicad5/power`). It takes the place of the old STM32F730
logic board, so the H7 hot path of the unimoc firmware can run against the
real INA240 stage before Jacobi exists. The power stage itself is not part of
this design.

KiCad 10 project: `nucleo_adapter.kicad_pro`. Status: **draft, not routed, not
reviewed**. The schematic and the PCB are generated (see `tools/`) and pass
ERC and DRC with schematic parity. Only the 167 unrouted connections are left.

## What lines up with the power board

The PCB uses the coordinate system of the legacy power board, so you can
overlay the two files (`production/legacy_kicad5/power`, KiCad 5 PCB of commit
`d914cf3`, which matches the Gerbers exactly).

| Adapter | Power board | Position (mm) | Note |
|---|---|---|---|
| J101 PWM, SMD 2x05 pin header, bottom | J103, SMD 2x05 socket | (64.5, 120.75), rot 90 | Copied from the old logic board's J101 |
| J102 ADC, SMD 2x05 pin header, bottom | J104, SMD 2x05 socket | (125.0, 130.0), rot -90 | Copied from the old logic board's J102 |
| H101, M3 | H105 | (99.75, 106.75) | Standoff |
| H102, M3 | H104 | (70.0, 178.5) | Standoff |
| H103, M3 | H107 | (122.0, 178.5) | Standoff |
| (no hole) | H106 | (100.25, 157.5) | Heatsink bolt; outline on `User.Drawings` |

These footprints are locked. The generator checked every pad against the old
logic board and every pin against the power-board socket: all 20 pins mate
with the intended signal (table below). The power-board area keeps the old
logic board's 8 x 8 mm notches at the far corners. `User.Drawings` shows the
84 x 79 mm power-board outline.

The current Jacobi PCB keeps the holes H101-H107 where they were, but moves
J101/J102 and adds J110/J111 (VSENSE). **This adapter fits only the legacy
power board.**

### Connector pinout (from the as-ordered power board)

| Pin | J101 PWM | | J102 ADC | |
|---|---|---|---|---|
| 1 | +BATT (DC link, only sensed here) | | +3.3VA (INA240 V+ and REF2) | |
| 2 | GND (= GNDPWR) | | I_C | INA240 out, phase C |
| 3 | open on the power board | | GNDA (power-board GND) | |
| 4 | PWM_AH | LM5109B HI, phase A | I_B | |
| 5 | +12V (gate driver VDD, from the adapter) | | GNDA | |
| 6 | PWM_AL | | I_A | |
| 7 | PWM_CL | | GNDA | |
| 8 | PWM_BH | | T_BRIDGE (NTC TH101, high side) | |
| 9 | PWM_CH | | GNDA | |
| 10 | PWM_BL | | GNDA (NTC low side) | |

INA240A1 on the power board: V+ and REF2 on +3.3VA, REF1 on GND, so
`I_x = 1.65 V + 20 mV/A`. With two 2 mΩ shunts in parallel per phase that is
about ±80 A full scale. No scaling is needed for the 3.3 V ADC.

## Board

- Outline: 100 x 221 mm in total. The power-board area is x 57..141,
  y 103..182 (84 x 79). The Nucleo part is x 49..149, y -39..103.
- 4 layers, with the design rules and the default net class of Jacobi (JLCPCB
  4-layer).
- The Nucleo (`U201`, footprint `Module:ST_Morpho_Connector_144_STLink_MountingHoles`)
  sits on the top side in two **2 x 36 female morpho sockets** (CN11, CN12).
  Footprint pads 1-144 are the symbol pins. Pads 145-148 at the ST-LINK end
  are not in the symbol: leave them empty.
- The morpho pins end 19 mm before the power-board edge, so no pin points
  down into the power stage. The ST-LINK USB is at the free end. The Nucleo's
  RJ45 end overhangs the power-board area above the adapter.
- Edge connectors (placed, not locked): J601 12 V in, J401 ENABLE, J503 HALL,
  J301 MOT_TEMP, J302 VPHASE on the left; J501/J502 CAN on the right.
- All other parts are parked to the right of the board, one column per sheet.

## Schematic

All sheets are A4. Hierarchy: root overview, then `power_board`, `nucleo`
(portrait), `analog` (currents, NTCs), `voltage` (Vdc and phase voltages),
`gate`, `interfaces` (CAN FD, Hall) and `supply`.

| Function | Nucleo pin | Circuit |
|---|---|---|
| PWM A/B/C high, low | PE9, PE11, PE13 / PE8, PE10, PE12 (TIM1) | 100R series, 10k pull-down at J101 |
| Break / enable | PE15 (TIM1_BKIN) | J401: close the loop to release; open = all outputs off |
| Ia, Ib, Ic | PA6, PB1, PC2_C | 220R / 2n2 |
| Vdc | PC3_C | 47k / 2k2 0.1 %, 1n (73.8 V full scale) |
| Va, Vb, Vc | PF11, PF13, PF10 | Same dividers, from J302 (wires to the phase pads J106-J108) |
| Bridge / motor temperature | PF12 / PF14 | 10k pull-up to +3.3VA, 1k / 100n |
| Hall A/B/C | PD12, PD13, PD14 | 2k2 pull-up to +3V3, 1k / 1n, sensors on +5V |
| CAN FD | PD0 RX, PD1 TX (FDCAN1) | TCAN334, JST GH 4 (Cyphal micro), 120R on JP501 |

The pin map is the one in the unimoc firmware,
`app/boards/nucleo_h743zi.overlay` on branch `hardware/first-startup`.

Supplies:

- **+12V** for the gate drivers comes from a bench supply on J601 (SS34
  reverse protection, SMAJ15CA clamp). It does not come from the DC link,
  because the first power-on runs the DC link at 12 V / 0.5 A.
- **+3.3VA** comes from the Nucleo +3V3 (VDDA, the ADC reference) through
  FB601, so the INA240 offset tracks the ADC reference.
- **GND and GNDA** meet only at FB602, as at FB502 on the old logic board. The
  power board does not join GND (GNDPWR) and its analog GND.

## To check before layout

1. LM5109B input threshold against 3.3 V logic (VIH in the datasheet).
2. Filter values (220R / 2n2, 1k / 100n) are first guesses.
3. Clearance under the adapter: the old logic board had the same stack height
   (SMD socket on the power board, SMD header on the bottom here). The
   bottom side over the power board should stay free of tall parts.
4. Mounting-hole and standoff heights against the socket height of J103/J104.
5. Whether J101 pin 3 should carry anything. It is open on the power board.
6. Phase-voltage wires on J302: only needed for identification step I3.
7. Firmware: the Nucleo overlay has no `PWM_EN` GPIO. Here the enable is the
   break loop on PE15.

## Tools

`tools/` holds the one-shot generator that made the first version:
`design.py` (the netlist as data), `gen_sch.py`, `gen_pcb.py` (KiCad 10
pcbnew), `gen_pro.py`, `checknet.py`. The KiCad files are the source from now
on. Edit them in KiCad and do not regenerate over manual work.
