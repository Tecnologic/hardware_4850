# Logic Board Redesign: STM32H743VIT6

Status: 2026-11-03. The MCU is drawn in the schematic (`controller.kicad_sch`,
U601) with the signals of the existing board and the phase voltages. The other
new functions (external overcurrent comparator, angle sensor) have pins
reserved but are not drawn yet. Internal connections marked *(RM0433)* must be checked
against the reference manual or in CubeMX.

The BCC (battery case controller) is redesigned around the same MCU family, so
both drives share one firmware platform. The firmware side is section 5 of
[`docs/system_plan.md`](https://github.com/Tecnologic/unimoc/blob/main/docs/system_plan.md#5-hardware-plan)
in the [unimoc](https://github.com/Tecnologic/unimoc) repository.

## 1. Why the H743VIT6

| | STM32F730R8 (old board) | **STM32H743VIT6** |
|---|---|---|
| Core | M7, 216 MHz | **M7, 480 MHz** (revision V; revision Y runs at 400 MHz) |
| Flash | 64 KB | **2 MB, dual bank** (2 × 1 MB) |
| RAM | 256 KB | **1 MB** (ITCM 64 KB, DTCM 128 KB for the hot path) |
| CAN | bxCAN only | **FDCAN1/2** |
| ADC | 3 × 12 bit | **3 × 16 bit** |
| Comparators / OPAMPs | none | **2 / 2** |
| Package | LQFP64 | **LQFP100 (14 × 14 mm), 82 I/O** |

- Part: **STM32H743VIT6**, LCSC `C114409` (Mouser `511-STM32H743VIT6`). The
  symbol carries the Mouser number in `Part#` and the LCSC number in `LCSC`.
- LQFP100 has no ports F and G. It is still enough: every analog signal gets
  its own channel, and the three phases stay sampled simultaneously, current
  and voltage of a phase on the same ADC (section 4.1). ADC3 only reaches
  PC0–PC3 in this package, so phase C uses PC2_C and PC3_C.
- 23 pins stay free (section 5).

## 2. Scope

- **Aux bridge out of scope.** The EESM excitation and brake chopper (the
  former `aux_a`/`aux_b` sheets and their connectors) are removed from the power board. A
  separate module will take care of them; nothing there is time-critical.
- **Power board** keeps the three phases, the INA240 current amplifiers and
  the bridge NTC.
- **Phase voltage sensing** (Va, Vb, Vc) is added. The dividers for Va/Vb/Vc
  **and** Vdc are on the power board (matched 47k / 2k2 0.1 %, 1 nF, referenced
  to the INA240 analog ground GND), and go over a third 2×5 connector J110/J111.
  On the logic board only an RC sits at the ADC pins.
- **Bridge NTC** TH101 has its low side on the power board GND; only the high
  side goes through J104.

## 3. Power board interface

| Power board | Logic board | Content |
|---|---|---|
| J103 PWM (2×5) | J101 | phase PWM, +12P, GNDPWR; pin 1 is +BATT, the logic board supply; pin 3 is `V12P_SNS`, +12P divided at the drivers |
| J104 ADC (2×5) | J102 | phase currents (INA240), bridge NTC high side (pin 8), +3.3VA, analog GND (pins 3, 5, 7, 9, 10) |
| J110 VSENSE (2×5) | J111 | divided voltages: pin 1 Va, 3 Vb, 5 Vc, 7 Vdc; pin 9 `PWR_DET` (GND on the power board); all even pins analog GND |

- **Phase and DC dividers:** 47k / 2k2 0.1 % (ratio 22.4, 73.8 V full scale
  at 3.3 V), 1 nF at the tap, 2.1 kΩ source impedance. At 54.6 V (13s full)
  the 47k takes 61 mW. It is an 0805 part for the voltage rating (150 V,
  0603 is often only 75 V). Part numbers of the 0.1 % parts are still to fill in.
- **+12P divider:** 10k / 2k2 (18.3 V full scale), 100 nF, referenced to
  GNDPWR. It goes over the PWM connector, so no 12 V reaches the analog part.
- **PWR_DET:** 10k pull-up R612 to +3V3 on the logic board, PE4 reads low when
  the power board is plugged in.

### 3.1 Why a third connector

The eight analog signals (3 currents, 3 phase voltages, Vdc, NTC) plus +3.3VA
and one GND would just fit J104 alone. That is not done:

- One GND pin would be the only return for all eight signals and the INA240
  supply. Every signal would sit next to another signal instead of a GND pin,
  so the phase-voltage edges couple into the current signals.
- No pin is left for PWR_DET or a later signal.

So J110/J111 stays, with signal and GND pins alternating.

### 3.2 Current measurement

Each phase has one **0.5 mΩ 3920 alloy shunt** (R201/R301/R401, Yezhan
DSLR-M-5-0.5F, LCSC `C41382689`, 9 W at 70 °C, ±1 %, ±70 ppm/K) and an
**INA240A1** (gain 20). The shunt is a 2-terminal part; the project footprint
`jacobi:R_Shunt_Yezhan_DSLR-5_3920_Kelvin` (land pattern from the datasheet:
pads 2.7 × 6.2 mm, gap 5.6 mm) adds sense pads at the inner pad edges, tied
by a net tie, so the INA240 reads the voltage right at the resistor. Route
the two sense lines as a pair from there.

The INA240 runs bidirectionally: REF1 on GND, REF2 on +3.3VA, so the output
sits at 1.65 V and can swing about ±1.6 V.

| | |
|---|---|
| Range | 1.6 V / (20 × 0.5 mΩ) = **±160 A** |
| 80 A peak phase current | ±0.8 V at the output, 50 % of the range |
| Loss at 57 A rms (80 A peak sine) | 1.6 W per shunt (9 W part) |
| Resolution | 16 bit over 3.3 V: 5 mA per LSB |

The earlier three 2 mΩ 2512 in parallel are gone: their copper between the
resistors became part of the shunt and drifted with temperature. With gain 50
the old 0.667 mΩ would have clipped at ±48 A, far below the 80 A peak phase
current the old power stage runs. The drive is rated 36 V / 45 A on the
battery side and 100 A peak phase current (where the target motors saturate),
so the overcurrent trip sits at 120–130 A within the ±160 A range. Ratings,
losses and cooling: [README, Ratings and limits](../README.md#ratings-and-limits).

## 4. Peripherals

### 4.1 Phase currents, voltages, DC link

- Op-amp filter stages removed: RC filter only (`analog` sheet).
- Simultaneous injected sampling from TIM1: Ia on ADC1 (PA2), Ib on ADC2
  (PA3), Ic on ADC3 (PC2_C). Second rank: Va on ADC1 (PB1), Vb on ADC2 (PB0),
  Vc on ADC3 (PC3_C). Vdc on PC1 (ADC1/2/3_INP11), +12P on PC5, the external
  inputs on PC0 and PC4, the temperatures on PA0/PA1 (ADC1).
- VREF+ and VDDA from +3.3VADC, so the INA240 outputs (reference from +3.3VA)
  stay ratiometric to the ADC.

### 4.2 Protection in hardware (planned, not drawn)

| Path | Input | Threshold | Action |
|---|---|---|---|
| External quad comparator, 3 channels | Ia, Ib, Ic (window for both signs) | DAC1_OUT1 (PA4) | open-drain wired-OR to TIM1_BKIN (PE15): phases off |
| COMP1 | Vdc (PB2, COMP1_INP, same net as PC1) | DAC1 channel *(RM0433)* | TIM1 break 2 *(RM0433)*: overvoltage, phases off |
| PWM_EN input (J1102) | – | – | TIM1_BKIN (PE15) |

The sample ISR keeps its overcurrent check on the raw counts as the second
level.

### 4.3 PWM

TIM1 CH1–CH3 / CH1N–CH3N on PA8–PA10 and PB13–PB15, the same pins as on the
F730. The 1R1 series resistors R606–R611 stay.

### 4.4 Firmware notes

- Hot code and data in ITCM/DTCM. DMA cannot reach the DTCM: DMA buffers go to
  AXI or D2 SRAM, not cached (MPU).
- Flash: 2 × 1 MB banks with 128 KB sectors. Settings (ZMS) need at least two
  sectors and a write granularity of 32 bytes; the firmware update goes into
  bank 2.
- HSE: the existing 20 MHz oscillator X601 on PH0 (bypass mode).

## 5. Pin assignment (STM32H743VIT6, LQFP100)

Drawn = connected in the schematic. Reserved = pin kept free for it, marked
no-connect for now.

| Pin | Port | Net / function | Peripheral | |
|---|---|---|---|---|
| 1 | PE2 | LED_MODE | GPIO | drawn |
| 2 | PE3 | LED_PWM | GPIO | drawn |
| 3 | PE4 | PWR_DET | GPIO | drawn |
| 4 | PE5 | USB_VBUS (sense) | GPIO | drawn |
| 12 | PH0 | CLK (20 MHz oscillator) | RCC_OSC_IN | drawn |
| 14 | NRST | \RESET, 100 nF (C621) |  | drawn |
| 15 | PC0 | AIN_ACC | ADC1/2/3_INP10 | drawn |
| 16 | PC1 | AIN_VDC | ADC1/2/3_INP11 | drawn |
| 17 | PC2_C | AIN_CUR_C (Ic) | ADC3_INP0 | drawn |
| 18 | PC3_C | AIN_VC (Vc) | ADC3_INP1 | drawn |
| 22 | PA0 | AIN_MOT_TEMP | ADC1_INP16 | drawn |
| 23 | PA1 | AIN_BRDG_TEMP | ADC1_INP17 | drawn |
| 24 | PA2 | AIN_CUR_A (Ia) | ADC1_INP14 | drawn |
| 25 | PA3 | AIN_CUR_B (Ib) | ADC2_INP15 | drawn |
| 28 | PA4 | phase overcurrent threshold | DAC1_OUT1 | reserved |
| 32 | PC4 | AIN_DCC | ADC1/2_INP4 | drawn |
| 33 | PC5 | AIN_V12P (+12P) | ADC1/2_INP8 | drawn |
| 34 | PB0 | AIN_VB (Vb) | ADC2_INP9 | drawn |
| 35 | PB1 | AIN_VA (Va) | ADC1_INP5 | drawn |
| 36 | PB2 | AIN_VDC | COMP1_INP | drawn |
| 45 | PE15 | PWM_EN | TIM1_BKIN | drawn |
| 52 | PB13 | PWM_AL_MCU | TIM1_CH1N | drawn |
| 53 | PB14 | PWM_BL_MCU | TIM1_CH2N | drawn |
| 54 | PB15 | PWM_CL_MCU | TIM1_CH3N | drawn |
| 59 | PD12 | HALL_A | TIM4_CH1 | drawn |
| 60 | PD13 | HALL_B | TIM4_CH2 | drawn |
| 61 | PD14 | HALL_C | TIM4_CH3 | drawn |
| 67 | PA8 | PWM_AH_MCU | TIM1_CH1 | drawn |
| 68 | PA9 | PWM_BH_MCU | TIM1_CH2 | drawn |
| 69 | PA10 | PWM_CH_MCU | TIM1_CH3 | drawn |
| 70 | PA11 | USB_DM | USB_OTG_FS_DM | drawn |
| 71 | PA12 | USB_DP | USB_OTG_FS_DP | drawn |
| 72 | PA13 | TMS-SWDIO | SWD | drawn |
| 76 | PA14 | TCK-SWCLK | SWD | drawn |
| 77 | PA15 | angle sensor NSS | SPI3_NSS | reserved |
| 78 | PC10 | angle sensor SCK | SPI3_SCK | reserved |
| 79 | PC11 | angle sensor MISO | SPI3_MISO | reserved |
| 80 | PC12 | angle sensor MOSI | SPI3_MOSI | reserved |
| 81 | PD0 | CAN_RX | FDCAN1_RX | drawn |
| 82 | PD1 | CAN_TX | FDCAN1_TX | drawn |
| 83 | PD2 | CAN STB (TCAN334) | GPIO | reserved |
| 89 | PB3 | TDO-SWO | TRACESWO | drawn |
| 94 | BOOT0 | BTLDR (jumper JP601, 11k pull-down) |  | drawn |
| 97 | PE0 | LED_RUN | GPIO | drawn |
| 98 | PE1 | LED_ERROR | GPIO | drawn |

Supply pins: VDD (5×) and VBAT on +3V3; VDDA and VREF+ on +3.3VADC; VSSA on
GNDA; VSS on GNDD; VCAP (pins 48 and 73) on the net `+1V2` with 2 × 2.2 µF
(C603, C620). The LQFP100 has no PDR_ON and no separate VDD33USB pin.

Free for later: PA5–PA7 (ADC, PA5 also DAC1_OUT2), PB4–PB12, PC6–PC9,
PC13–PC15, PD3–PD11, PD15, PE6–PE14, PH1.

## 6. Parts

- **Added with the MCU:** C620 (2.2 µF, second VCAP), C621 (100 nF, NRST),
  C622 (100 nF, VDDA). C608–C612 are the five VDD decoupling caps. C603 changed from 10 µF to 2.2 µF
  (VCAP). Order numbers of the 2.2 µF parts still to fill in.
- **Keep:** TCAN334 (CAN FD), USB for DFU, SWD/SWO, Hall and temperature
  inputs, the supply topology from the battery (LM5008, up to 95 V).
- **Removed:** the 24LC04 EEPROM with its pull-ups and WP jumper (U1102,
  R1112, R1113, R1115, C1105, JP1101). The settings live in flash.
- **New, still to draw:** quad comparator for the phase overcurrent, connector for an SPI angle sensor (SPI3), CAN STB.
- **Layout:** LQFP100 (14 × 14 mm) instead of LQFP64; the logic board is laid
  out again.

## 7. Checks

1. The 3.3 V supply: the H743 draws a few hundred mA at 480 MHz; check the
   regulator chain on `power_supply`.
2. *(RM0433)* items: DAC1 → COMP1 inverting input, COMP1 → TIM1 break 2, ADC
   injected trigger from TIM1 for ADC1 to ADC3.
3. Silicon revision of the parts at hand (V: 480 MHz, Y: 400 MHz).
4. ERC: the two VCAP pins (48 and 73) are "power output" in the KiCad symbol, so tying them
   together gives two `pin_to_pin` errors. They are correct; exclude them in
   the ERC dialog.
