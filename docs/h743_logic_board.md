# Logic Board Redesign: STM32H743ZIT6

Status: 2026-11-03. The MCU is drawn in the schematic (`controller.kicad_sch`,
U601) with the signals of the existing board. The new functions (phase
voltages, external overcurrent comparator, angle sensor) have pins reserved but
are not drawn yet. Internal connections marked *(RM0433)* must be checked
against the reference manual or in CubeMX.

The BCC (battery case controller) is redesigned around the same MCU family, so
both drives share one firmware platform. The firmware side is section 5 of
[`docs/system_plan.md`](https://github.com/Tecnologic/unimoc/blob/main/docs/system_plan.md#5-hardware-plan)
in the [unimoc](https://github.com/Tecnologic/unimoc) repository.

## 1. Why the H743ZIT6

| | STM32F730R8 (old board) | **STM32H743ZIT6** |
|---|---|---|
| Core | M7, 216 MHz | **M7, 480 MHz** (revision V; revision Y runs at 400 MHz) |
| Flash | 64 KB | **2 MB, dual bank** |
| RAM | 256 KB | **1 MB** (ITCM 64 KB, DTCM 128 KB for the hot path) |
| CAN | bxCAN only | **FDCAN1/2** |
| ADC | 3 × 12 bit | **3 × 16 bit**, many more channels on port F |
| Comparators / OPAMPs | none | **2 / 2** |
| Package | LQFP64 | **LQFP144 (20 × 20 mm), 114 I/O** |

- Order: Mouser `511-STM32H743ZIT6`, 11.73 € each at 10 pieces (2026-11-03).
  The symbol's `Part#` field holds the Mouser number, like the other parts.
- LQFP144 instead of the LQFP100 of the first concept: port F brings many
  more ADC3 inputs (PF3–PF10) plus ADC1/ADC2 inputs (PF11–PF14), so the
  phase voltages get their own channels, simultaneous with the currents.
  PG2 gives TIM8_BKIN, which leaves PA6 free.

## 2. Scope

- **Aux bridge out of scope.** The EESM excitation and brake chopper (the
  former `aux_a`/`aux_b` sheets, J110–J113) are removed from the power board. A
  separate module will take care of them; nothing there is time-critical.
- **Power board** keeps the three phases, the INA240 current amplifiers and
  the bridge NTC.
- **Phase voltage sensing** (Va, Vb, Vc) is added. Recommended: the dividers for
  Va/Vb/Vc **and** Vdc on the power board (matched, referenced to the INA240
  analog ground), J104/J102 widened from 2×5 to 2×8, and only a small RC at the
  ADC pins on the logic board. Not decided yet.

## 3. Power board interface (today)

| Power board | Logic board | Content |
|---|---|---|
| J103 PWM (2×5) | J101 | phase PWM, +12P, GNDPWR; pin 1 is +BATT, the logic board supply and the input of the Vdc divider (R701/R702 on the logic board) |
| J104 ADC (2×5) | J102 | phase currents (INA240), bridge NTC, +3.3VA, analog GND |

## 4. Peripherals

### 4.1 Phase currents, voltages, DC link

- Op-amp filter stages removed: RC filter only (`analog` sheet).
- Simultaneous injected sampling from TIM1: Ia on ADC1 (PA2), Ib on ADC2
  (PA3), Ic on ADC3 (PC2_C). Second rank: Va on ADC1 (PF11), Vb on ADC2 (PF13),
  Vc on ADC3 (PF3). Vdc on PC1 (ADC1/2/3_INP11).
- VREF+ and VDDA from +3.3VADC, so the INA240 outputs (reference from +3.3VA)
  stay ratiometric to the ADC.

### 4.2 Protection in hardware (planned, not drawn)

| Path | Input | Threshold | Action |
|---|---|---|---|
| External quad comparator, 3 channels | Ia, Ib, Ic (window for both signs) | DAC1_OUT1 (PA4) | open-drain wired-OR to TIM1_BKIN (PE15): phases off |
| COMP1 | Vdc (PB2, COMP1_INP, same net as PC1) | DAC1 channel *(RM0433)* | TIM1 break 2 *(RM0433)*: overvoltage, phases off |
| PWM_EN input (J1102) | – | – | TIM1_BKIN (PE15) and TIM8_BKIN (PG2) |

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

## 5. Pin assignment (STM32H743ZIT6, LQFP144)

Drawn = connected in the schematic. Reserved = pin kept free for it, marked
no-connect for now.

| Pin | Port | Net / function | Peripheral | |
|---|---|---|---|---|
| 1 | PE2 | LED_MODE | GPIO | drawn |
| 2 | PE3 | LED_PWM | GPIO | drawn |
| 4 | PE5 | USB_VBUS (sense) | GPIO | drawn |
| 13 | PF3 | Vc | ADC3_INP5 | reserved |
| 23 | PH0 | CLK (20 MHz oscillator) | RCC_OSC_IN | drawn |
| 25 | NRST | \RESET, 100 nF (C621) | | drawn |
| 26 | PC0 | AIN_ACC | ADC1/2/3_INP10 | drawn |
| 27 | PC1 | AIN_VDC | ADC1/2/3_INP11 | drawn |
| 28 | PC2_C | AIN_CUR_C (Ic) | ADC3_INP0 | drawn |
| 29 | PC3_C | AIN_DCC | ADC3_INP1 | drawn |
| 34 | PA0 | AIN_MOT_TEMP | ADC1_INP16 | drawn |
| 35 | PA1 | AIN_BRDG_TEMP | ADC1_INP17 | drawn |
| 36 | PA2 | AIN_CUR_A (Ia) | ADC1_INP14 | drawn |
| 37 | PA3 | AIN_CUR_B (Ib) | ADC2_INP15 | drawn |
| 40 | PA4 | phase overcurrent threshold | DAC1_OUT1 | reserved |
| 48 | PB2 | AIN_VDC | COMP1_INP | drawn |
| 49 | PF11 | Va | ADC1_INP2 | reserved |
| 53 | PF13 | Vb | ADC2_INP2 | reserved |
| 68 | PE15 | PWM_EN | TIM1_BKIN | drawn |
| 74 | PB13 | PWM_AL_MCU | TIM1_CH1N | drawn |
| 75 | PB14 | PWM_BL_MCU | TIM1_CH2N | drawn |
| 76 | PB15 | PWM_CL_MCU | TIM1_CH3N | drawn |
| 81 | PD12 | HALL_A | TIM4_CH1 | drawn |
| 82 | PD13 | HALL_B | TIM4_CH2 | drawn |
| 85 | PD14 | HALL_C | TIM4_CH3 | drawn |
| 87 | PG2 | PWM_EN | TIM8_BKIN | drawn |
| 100 | PA8 | PWM_AH_MCU | TIM1_CH1 | drawn |
| 101 | PA9 | PWM_BH_MCU | TIM1_CH2 | drawn |
| 102 | PA10 | PWM_CH_MCU | TIM1_CH3 | drawn |
| 103 | PA11 | USB_DM | USB_OTG_FS_DM | drawn |
| 104 | PA12 | USB_DP | USB_OTG_FS_DP | drawn |
| 105 | PA13 | TMS-SWDIO | SWD | drawn |
| 109 | PA14 | TCK-SWCLK | SWD | drawn |
| 110 | PA15 | angle sensor NSS | SPI3_NSS | reserved |
| 111 | PC10 | angle sensor SCK | SPI3_SCK | reserved |
| 112 | PC11 | angle sensor MISO | SPI3_MISO | reserved |
| 113 | PC12 | angle sensor MOSI | SPI3_MOSI | reserved |
| 114 | PD0 | CAN_RX | FDCAN1_RX | drawn |
| 115 | PD1 | CAN_TX | FDCAN1_TX | drawn |
| 116 | PD2 | CAN STB (TCAN334) | GPIO | reserved |
| 133 | PB3 | TDO-SWO | TRACESWO | drawn |
| 138 | BOOT0 | BTLDR (jumper JP601, 11k pull-down) | | drawn |
| 141 | PE0 | LED_RUN | GPIO | drawn |
| 142 | PE1 | LED_ERROR | GPIO | drawn |

Supply pins: VDD (11×), VBAT, PDR_ON and VDD33USB on +3V3; VDDA and VREF+ on
+3.3VADC; VSSA on GNDA; VSS on GNDD; VCAP (pins 71 and 106) on the net `+1V2`
with 2 × 2.2 µF (C603, C620).

Free for later: PF4–PF10 and PF12/PF14 (ADC), PF0–PF2, PF15, PG0–PG15 except PG2, PD3–PD11,
PD15, PE4, PE6–PE14, PB0/PB1/PB4–PB12, PC4–PC9, PC13–PC15, PA5–PA7.

## 6. Parts

- **Added with the MCU:** C613–C618 (100 nF, one per VDD pin together with
  C608–C612), C619 (100 nF, VDD33USB), C620 (2.2 µF, second VCAP), C621
  (100 nF, NRST), C622 (100 nF, VDDA). C603 changed from 10 µF to 2.2 µF
  (VCAP). Order numbers of the 2.2 µF parts still to fill in.
- **Keep:** TCAN334 (CAN FD), USB for DFU, SWD/SWO, Hall and temperature
  inputs, the supply topology from 48 V.
- **Removed:** the 24LC04 EEPROM with its pull-ups and WP jumper (U1102,
  R1112, R1113, R1115, C1105, JP1101). The settings live in flash.
- **New, still to draw:** quad comparator for the phase overcurrent, phase
  voltage inputs, connector for an SPI angle sensor (SPI3), CAN STB.
- **Layout:** LQFP144 (20 × 20 mm) instead of LQFP64; the logic board is laid
  out again.

## 7. Checks

1. The 3.3 V supply: the H743 draws a few hundred mA at 480 MHz; check the
   regulator chain on `power_supply`.
2. *(RM0433)* items: DAC1 → COMP1 inverting input, COMP1 → TIM1 break 2, ADC
   injected trigger from TIM1 for ADC1 to ADC3.
3. Silicon revision of the parts at hand (V: 480 MHz, Y: 400 MHz).
4. ERC: the two VCAP pins are "power output" in the KiCad symbol, so tying them
   together gives two `pin_to_pin` errors. They are correct; exclude them in
   the ERC dialog.
