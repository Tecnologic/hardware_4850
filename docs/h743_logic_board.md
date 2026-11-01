# Logic Board Redesign: STM32H743VIT6

Status: concept, 2026-11-01. Nothing of this is drawn yet. The pin data comes
from ST's open pin data (`STM32H743VITx.xml`, LQFP100). The internal
connections marked *(RM0433)* are from memory of the reference manual and must
be checked in CubeMX before the schematic is drawn.

The BCC (battery case controller) is redesigned around the same MCU, so both
drives share one firmware platform. The firmware side is
`docs/system_plan.md` section 5 in the [unimoc](https://github.com/Tecnologic/unimoc)
repository.

## 1. Why the H743VIT6

| | STM32F730R8 (today) | STM32G473 | **STM32H743VIT6** |
|---|---|---|---|
| Core | M7, 216 MHz | M4, 170 MHz | **M7, 480 MHz** (revision V; revision Y runs at 400 MHz) |
| Flash | 64 KB | 512 KB | **2 MB, dual bank** |
| RAM | 256 KB | 128 KB | **1 MB** (ITCM 64 KB, DTCM 128 KB for the hot path) |
| CAN | bxCAN only | FDCAN | **FDCAN1/2** |
| ADC | 3 × 12 bit | 5 × 12 bit | **3 × 16 bit** |
| Comparators / OPAMPs | none | 7 / 6 | **2 / 2** |
| Package | LQFP64 | LQFP64 (LQFP48 with 38 I/O is too small) | **LQFP100, 82 I/O** |

- About four times the computing time of the G4 per control cycle; the
  hot-path budget is no longer the limit.
- Widely available. The same MCU on the 4850 logic board and the BCC.
- Less analog on chip than the G4: only two comparators and two OPAMPs and no
  CORDIC. The phase overcurrent therefore uses an external comparator
  (section 3.3).

## 2. Power board interface

Unchanged from the power board schematic (sheet `aux_leg.kicad_sch`, used as
`aux_a` and `aux_b`): an asymmetric H-bridge with a low-side shunt in each leg.

| Motor | Load | Operation |
|---|---|---|
| EESM | field winding between F1 (J111) and F2 (J112) | leg B low side stays on, leg A switches: the field current always flows through the leg B shunt. Fast de-excitation: A_L + B_H on, −Vdc across the winding. |
| PMSM | brake resistor between DC+ (J113) and F2 (J112) | leg B low side is the chopper, leg B high side the freewheel. Leg A may stay unpopulated. |

| Power board | Logic board | Content |
|---|---|---|
| J103 PWM (2×5) | J101 | phase PWM, +12P, GNDPWR (unchanged) |
| J104 ADC (2×5) | J102 | phase currents (INA240), DC link, NTC, +3.3VA (unchanged) |
| J110 AUX (2×5) | new | 1 PwmAH, 2 PwmAL, 3 PwmBH, 4 PwmBL, 5/6 ISenseBP/BN, 7/8 ISenseAP/AN, 9/10 GNDPWR |

## 3. Peripherals

### 3.1 Phase currents and DC link

- The INA240 inline amplifiers on the power board stay. The external op-amp
  filter stages (`current_filters`) are dropped: RC anti-alias filter only.
- Simultaneous injected sampling from TIM1: Ia on ADC1, Ib on ADC2, Ic on ADC3
  (PC2_C, a direct ADC3 pin). Second rank: Vdc on ADC3, the aux current on
  ADC1. The ADCs run at 16 bit or, for a shorter conversion, at 12 bit.
- VREF+ from +3.3VA through a filter, so the INA240 outputs (reference from
  +3.3VA) stay ratiometric to the ADC.

### 3.2 Aux bridge current

- OPAMP1 in PGA mode directly at the Kelvin pair of the leg B shunt:
  ISenseBP to OPAMP1_VINP (PB0), ISenseBN as the external bias at OPAMP1_VINM0
  (PC5). The gain is set by software: high for the field current (EESM), low
  for the chopper current (PMSM).
- OPAMP1_VOUT (PC4) is ADC1/2_INP4 (fast channel), sampled on the pin.
- The leg A shunt (ISenseAP/AN) is not measured (no ADC pin left in this
  assignment; PA5 can take it instead of the +12V monitor).

### 3.3 Protection in hardware (no CPU)

| Path | Input | Threshold | Action |
|---|---|---|---|
| External quad comparator, 3 channels | Ia, Ib, Ic (INA240 outputs, window for both signs) | DAC1_OUT1 (PA4) | open-drain wired-OR to TIM1_BKIN (PE15): phases off |
| COMP1 | Vdc (PB2, COMP1_INP) | DAC1 channel, with hysteresis *(RM0433)* | TIM1 break 2 (overvoltage, phases off) **and** TIM8 OCREF clear: chopper on (PMSM) *(RM0433)* |
| COMP2 | aux current (PE11, COMP2_INP, on the OPAMP1_VOUT net) | DAC1 channel *(RM0433)* | TIM8 break: aux bridge off |
| E-stop input | opto or switch | – | on the TIM1_BKIN line and on TIM8_BKIN (PA6) |

The sample ISR keeps its overcurrent check on the raw counts as the second
level (every 15.6 µs at 32 kHz PWM).

### 3.4 PWM

- Phases: TIM1 CH1–CH3 and CH1N–CH3N on PA8–PA10 and PB13–PB15.
- Aux bridge: TIM8, leg A on CH1/CH1N (PC6/PA7), leg B on CH3/CH3N (PC8/PB1),
  slave of TIM1 *(RM0433)*. TIM8 has its own break inputs, so a phase trip does
  not stop the chopper.
- EESM: leg A switches complementary with dead time; leg B is forced to
  "CH3N active" (B_L on). Fast de-excitation: A_L and B_H on.
- PMSM chopper without the CPU: CH3 (B_H) disabled, CH3N (B_L) enabled, CCR at
  100 % so B_L is normally off. COMP1 clears OC3REF through the OCREF clear
  input: B_L is on while the DC link is above the threshold and is released at
  the next PWM period. If the OCREF clear cannot take COMP1 on the H743, the
  HRTIM is the alternative (it takes COMP events), but its pins in LQFP100
  collide with TIM1 and USB.

### 3.5 Firmware notes

- Hot code and data in ITCM/DTCM. DMA (the duty burst of the hot path) cannot
  reach the DTCM: its buffers go to AXI or D2 SRAM, not cached (MPU).
- Flash: 2 × 1 MB banks with 128 KB sectors. Settings (ZMS) need at least two
  sectors (256 KB) and a write granularity of 32 bytes; the firmware update goes
  into bank 2.

## 4. Pin assignment (STM32H743VIT6, LQFP100)

| Pin | Port | Function | Peripheral |
|---|---|---|---|
| 1 | PE0 | LED_RUN | GPIO |
| 2 | PE1 | LED_ERROR | GPIO |
| 3 | PE2 | LED_MODE | GPIO |
| 4 | PE3 | LED_PWM | GPIO |
| 5 | PE4 | PWM_EN (driver enable to the power board) | GPIO |
| 6 | PE5 | USB VBUS sense | GPIO |
| 12 | PH0 | HSE (crystal or oscillator) | RCC_OSC_IN |
| 13 | PH1 | HSE | RCC_OSC_OUT |
| 15 | PC0 | analog input 1 (AIN_ACC) | ADC1/2/3_INP10 |
| 16 | PC1 | Vdc | ADC3_INP11 |
| 17 | PC2_C | Ic | ADC3_INP0 |
| 18 | PC3_C | analog input 2 (AIN_DCC) | ADC3_INP1 |
| 20 | VREF+ | +3.3VA through a filter | |
| 22 | PA0 | motor temperature | ADC1_INP16 |
| 23 | PA1 | bridge temperature (NTC TH101) | ADC1_INP17 |
| 24 | PA2 | Ia | ADC1_INP14 |
| 25 | PA3 | Ib | ADC2_INP15 |
| 28 | PA4 | phase overcurrent threshold | DAC1_OUT1 |
| 29 | PA5 | +12V monitor | ADC1/2_INP19 |
| 30 | PA6 | E-stop | TIM8_BKIN |
| 31 | PA7 | aux leg A low | TIM8_CH1N |
| 32 | PC4 | aux current (PGA output) | OPAMP1_VOUT = ADC1/2_INP4 |
| 33 | PC5 | aux shunt Kelvin return (ISenseBN) | OPAMP1_VINM0 |
| 34 | PB0 | aux shunt (ISenseBP) | OPAMP1_VINP |
| 35 | PB1 | aux leg B low | TIM8_CH3N |
| 36 | PB2 | Vdc (same net as PC1) | COMP1_INP |
| 41 | PE11 | aux current (same net as PC4) | COMP2_INP |
| 45 | PE15 | phase overcurrent and E-stop (wired-OR) | TIM1_BKIN |
| 52 | PB13 | PWM AL | TIM1_CH1N |
| 53 | PB14 | PWM BL | TIM1_CH2N |
| 54 | PB15 | PWM CL | TIM1_CH3N |
| 59 | PD12 | Hall A | TIM4_CH1 (or EXTI) |
| 60 | PD13 | Hall B | TIM4_CH2 |
| 61 | PD14 | Hall C | TIM4_CH3 |
| 63 | PC6 | aux leg A high | TIM8_CH1 |
| 65 | PC8 | aux leg B high | TIM8_CH3 |
| 67 | PA8 | PWM AH | TIM1_CH1 |
| 68 | PA9 | PWM BH | TIM1_CH2 |
| 69 | PA10 | PWM CH | TIM1_CH3 |
| 70 | PA11 | USB DM (DFU) | USB_OTG_FS_DM |
| 71 | PA12 | USB DP | USB_OTG_FS_DP |
| 72 | PA13 | SWDIO | SWD |
| 76 | PA14 | SWCLK | SWD |
| 77 | PA15 | angle sensor NSS | SPI3_NSS |
| 78 | PC10 | angle sensor SCK | SPI3_SCK |
| 79 | PC11 | angle sensor MISO | SPI3_MISO |
| 80 | PC12 | angle sensor MOSI | SPI3_MOSI |
| 81 | PD0 | CAN RX | FDCAN1_RX |
| 82 | PD1 | CAN TX | FDCAN1_TX |
| 83 | PD2 | CAN STB (TCAN334) | GPIO |
| 89 | PB3 | SWO | TRACESWO |
| 94 | BOOT0 | bootloader jumper | |

About 30 I/O stay free (PB4–PB12, PC7, PC9, PC13, PD3–PD11, PD15, PE6–PE10,
PE12–PE14), for example for a second CAN (FDCAN2 on PB5/PB6) or more sensors.

## 5. Parts

- **Keep:** TCAN334 (CAN FD) with split termination that can be populated, USB
  for DFU, SWD/SWO, Hall and temperature inputs, the supply topology from 48 V.
- **Check:** the 3.3 V supply. The H743 draws a few hundred mA at 480 MHz;
  the current regulator chain has to be checked against that, plus the VCAP
  capacitors of the internal regulator.
- **Drop:** 24LC04 EEPROM (settings in flash), the op-amp filter stages of the
  current channels.
- **New:** quad comparator for the phase overcurrent, AUX connector to J110,
  connector for an SPI angle sensor (SPI3).
- **Layout:** LQFP100 (14 × 14 mm) instead of LQFP64. The logic board has to be
  laid out again anyway.

## 6. Checks before the schematic

1. *(RM0433)* items: DAC1 → COMP inverting inputs, COMP1 → TIM1 break 2,
   COMP1 → TIM8 OCREF clear, COMP2 → TIM8 break, TIM8 as a slave of TIM1, ADC
   injected trigger from TIM1 for ADC1 to ADC3.
2. Silicon revision of the parts at hand (V: 480 MHz, Y: 400 MHz).
3. EESM data (field current, resistance, inductance) → shunt value, PGA gain,
   de-excitation time (≈ L_f·I_f/V_dc).
4. Brake resistor value and power → shunt power.
5. Ground offset between the boards for the millivolt Kelvin signals.
