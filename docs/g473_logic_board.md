# Logic Board Redesign: STM32G473RET6

Status: concept, 2026-10-31. Nothing of this is drawn yet. The pin data comes
from ST's open pin data (`STM32G473R(B-C-E)Tx.xml`, LQFP64; it differs from
the G474R only by the missing HRTIM). The internal
connections marked *(RM0440)* are from memory of the reference manual and must
be checked in CubeMX before the schematic is drawn.

The firmware side is `docs/system_plan.md` section 5.2 in the
[unimoc](https://github.com/Tecnologic/unimoc) repository.

## 1. Why the G473

- **CAN FD.** The F7 family only has bxCAN (classic CAN). The drive network is
  Cyphal on CAN FD (4 Mbit/s data phase with the TCAN334).
- **Flash.** 512 KB dual bank: firmware image in bank 1, bank 2 for the update
  over Cyphal. The F730R8 has 64 KB.
- **Same part as the BCC** (STM32G473CET6, here in LQFP64): one hot path for
  both boards. Parts are at hand.
- **No HRTIM** (the only difference to the G474). The aux bridge runs on
  TIM8, which has what it needs: complementary outputs with dead time, its own
  break inputs, sync with TIM1 and an OCREF clear input.
- **Analog and protection on chip,** used throughout this design instead of
  external parts (section 3).

The G473 is slower per cycle than the F7. The hot-path estimate in unimoc
(`docs/hotpath_plan.md`) is about 45 % CPU at 32 kHz PWM. Measure the real load
on the BCC (DWT cycle counter) before the order. If it is far above that
estimate, the fallback is an STM32H7 (FDCAN, up to 550 MHz) with a new
platform port.

## 2. Power board interface

The power board gets two more half bridges (sheet `aux_leg.kicad_sch`, used as
`aux_a` and `aux_b`): an asymmetric H-bridge with a low-side shunt in each leg.

| Motor | Load | Operation |
|---|---|---|
| EESM | field winding between F1 (J111) and F2 (J112) | leg B low side stays on, leg A switches: the field current always flows through the leg B shunt. Fast de-excitation: A_L + B_H on, −Vdc across the winding. |
| PMSM | brake resistor between DC+ (J113) and F2 (J112) | leg B low side is the chopper, leg B high side the freewheel. Leg A may stay unpopulated. |

Connectors to the logic board:

| Power board | Logic board | Content |
|---|---|---|
| J103 PWM (2×5) | J101 | phase PWM, +12P, GNDPWR (unchanged) |
| J104 ADC (2×5) | J102 | phase currents (INA240), DC link, NTC, +3.3VA (unchanged) |
| **J110 AUX (2×5)** | new | 1 PwmAH, 2 PwmAL, 3 PwmBH, 4 PwmBL, 5/6 ISenseBP/BN, 7/8 ISenseAP/AN, 9/10 GNDPWR |

The shunt signals are Kelvin pairs with millivolt levels. Route them as pairs
on both boards and filter them at the MCU (section 3.2).

## 3. Use of the G4 peripherals

### 3.1 Phase currents and DC link

- The INA240 inline amplifiers on the power board stay (measurement in every
  switching state). The external op-amp filter stages of the current design
  (`current_filters`, MCP6002/GS8632) are dropped: only an RC anti-alias filter
  at each ADC pin.
- Simultaneous injected sampling: Ia on ADC1, Ib on ADC2, Ic on ADC3, triggered
  by TIM1. Vdc as the second rank on ADC2.
- VREF+ = VDDA = +3.3VA, so the INA240 outputs (reference from +3.3VA) stay
  ratiometric to the ADC.

### 3.2 Aux bridge current

- OPAMP4 in PGA mode directly at the Kelvin pair of the leg B shunt:
  ISenseBP to OPAMP4_VINP (PB11), ISenseBN as the external bias at OPAMP4_VINM0
  (PB10). The gain is set by software: high for the field current (EESM), low
  for the chopper current (PMSM).
- OPAMP4_VOUT (PB12) is also ADC4_IN3, so ADC4 samples the PGA output on the
  same pin, at the same trigger as the phases.
- The leg A pair (ISenseAP/AN) goes to spare ADC pins as an option (section 4).

### 3.3 Protection in hardware (no CPU)

| Comparator | Input | Threshold | Action |
|---|---|---|---|
| COMP1 | Ia (PA1, COMP1_INP) | DAC *(RM0440)* | TIM1 break: phases off |
| COMP2 | Ib (PA7, COMP2_INP) | DAC | TIM1 break |
| COMP4 | Ic (PB0, COMP4_INP) | DAC | TIM1 break |
| COMP3 | Vdc (PC1, COMP3_INP) | DAC, with hysteresis | TIM1 break (overvoltage) **and** TIM8 OCREF clear: chopper on (PMSM); TIM8 break2 for the fast de-excitation (EESM) |
| COMP6 | aux shunt (PB11, COMP6_INP) | DAC | TIM8 break: aux bridge off |

The comparator outputs reach the TIM1 and TIM8 break inputs and the TIM8
OCREF clear internally *(RM0440)*, so no pins are used for them. The external
E-stop goes to TIM1_BKIN (PA6) and TIM8_BKIN (PD2) on the same net.

### 3.4 PWM

- Phases: TIM1 CH1–CH3 with CH1N–CH3N, the classic pins PA8–PA10 and
  PB13–PB15. The BCC uses TIM8. The timer is a devicetree property of the
  `foc0` node, so the hot path stays the same.
- Aux bridge: TIM8, leg A on CH3/CH3N, leg B on CH1/CH1N, slave of TIM1
  (trigger/reset from TIM1 TRGO through ITR0 *(RM0440)*). TIM8 has its own break
  inputs, separate from the phase break: on a phase trip, the chopper must keep
  running.
- EESM: leg A switches complementary with dead time; leg B is forced to
  "CH1N active" (B_L on). Fast de-excitation: A_L and B_H forced on (by
  software, or by the TIM8 break2 with the idle states set to A_L and B_H on).
- PMSM chopper without the CPU: CH1 (B_H) disabled, CH1N (B_L) enabled, CCR at
  100 % so B_L is normally off. COMP3 clears OC1REF through the OCREF clear
  input (OCRSEL = COMP3 *(RM0440)*): B_L turns on while the DC link is above the
  threshold and is released at the next PWM period after COMP3 drops. The
  chopper is hysteretic with one PWM period (31 µs at 32 kHz) as the time step.

### 3.5 Computation

CORDIC for sin/cos/atan2 in the control cycle and the observer. Hot code and
data in CCM SRAM (no flash wait states, no stall while a settings write is
running).

## 4. Pin assignment (STM32G473RET6, LQFP64)

| Pin | Port | Function | Peripheral |
|---|---|---|---|
| 2 | PC13 | Hall A | GPIO/EXTI13 (low-speed pin, input only) |
| 3 | PC14 | Hall B | GPIO/EXTI14 |
| 4 | PC15 | Hall C | GPIO/EXTI15 |
| 5 | PF0 | HSE input (20 MHz oscillator X601) | RCC_OSC_IN |
| 6 | PF1 | USB VBUS sense | GPIO |
| 7 | PG10 | NRST | |
| 8 | PC0 | +12V monitor | ADC1/2_IN6 |
| 9 | PC1 | Vdc | ADC2_IN7, COMP3_INP |
| 10 | PC2 | spare analog (leg A ISenseAP option) | ADC1/2_IN8 |
| 11 | PC3 | spare analog | ADC1/2_IN9 |
| 12 | PA0 | motor temperature | ADC1_IN1 |
| 13 | PA1 | Ia | ADC1_IN2, COMP1_INP |
| 14 | PA2 | LED_RUN | GPIO |
| 17 | PA3 | analog input 1 (AIN_ACC) | ADC1_IN4 |
| 18 | PA4 | angle sensor NSS | SPI3_NSS |
| 19 | PA5 | analog input 2 (AIN_DCC) | ADC2_IN13 |
| 20 | PA6 | E-stop | TIM1_BKIN |
| 21 | PA7 | Ib | ADC2_IN4, COMP2_INP |
| 22 | PC4 | LED_PWM | GPIO |
| 23 | PC5 | spare analog | ADC2_IN11 |
| 24 | PB0 | Ic | ADC3_IN12, COMP4_INP |
| 25 | PB1 | aux leg A low | TIM8_CH3N |
| 26 | PB2 | bridge temperature (NTC TH101) | ADC2_IN12 |
| 28 | VREF+ | = VDDA (+3.3VA) | |
| 30 | PB10 | aux shunt Kelvin return (ISenseBN) | OPAMP4_VINM0 |
| 33 | PB11 | aux shunt (ISenseBP) | OPAMP4_VINP, COMP6_INP |
| 34 | PB12 | aux current (PGA output, test point) | OPAMP4_VOUT = ADC4_IN3 |
| 35 | PB13 | PWM AL | TIM1_CH1N |
| 36 | PB14 | PWM BL | TIM1_CH2N |
| 37 | PB15 | PWM CL | TIM1_CH3N |
| 38 | PC6 | aux leg B high | TIM8_CH1 |
| 39 | PC7 | spare | GPIO |
| 40 | PC8 | aux leg A high | TIM8_CH3 |
| 41 | PC9 | spare | GPIO |
| 42 | PA8 | PWM AH | TIM1_CH1 |
| 43 | PA9 | PWM BH | TIM1_CH2 |
| 44 | PA10 | PWM CH | TIM1_CH3 |
| 45 | PA11 | USB DM (DFU) | USB |
| 46 | PA12 | USB DP | USB |
| 49 | PA13 | SWDIO | SWD |
| 50 | PA14 | SWCLK | SWD |
| 51 | PA15 | LED_ERROR | GPIO |
| 52 | PC10 | angle sensor SCK | SPI3_SCK |
| 53 | PC11 | angle sensor MISO | SPI3_MISO |
| 54 | PC12 | angle sensor MOSI | SPI3_MOSI |
| 55 | PD2 | E-stop (same net as PA6) | TIM8_BKIN |
| 56 | PB3 | aux leg B low | TIM8_CH1N (no SWO: the log is on RTT) |
| 57 | PB4 | PWM_EN (driver enable to the power board) | GPIO |
| 58 | PB5 | CAN RX | FDCAN2_RX |
| 59 | PB6 | CAN TX | FDCAN2_TX |
| 60 | PB7 | CAN STB (TCAN334) | GPIO |
| 61 | PB8 | BOOT0 (bootloader jumper) | BOOT0 |
| 62 | PB9 | LED_MODE | GPIO |

Free for later: PC7, PC9, PC2, PC3, PC5 (analog), and the ADC5 inputs are unused.

## 5. Parts

- **Keep:** TCAN334 (CAN FD) with split termination that can be populated, USB
  for DFU, SWD (no SWO, the log runs over RTT), Hall and temperature inputs, the supply topology from 48 V,
  the 20 MHz oscillator.
- **Drop:** 24LC04 EEPROM (settings in the G4 flash), the op-amp filter stages
  of the current channels.
- **New:** AUX connector to J110, connector for an SPI angle sensor (SPI3).
- **Power board:** parts as on the existing PCB (NCEP6080AG, 56 µF, 1R1 gate
  resistors). The aux shunt value (5 mΩ placeholder) follows from the field
  current of the EESM.

## 6. Checks before the schematic

1. CPU load of the hot path measured on the BCC (section 1).
2. *(RM0440)* items: DAC → COMP inverting input, COMP → TIM1/TIM8 break,
   COMP3 → TIM8 OCREF clear (OCRSEL), TIM8 as a slave of TIM1 (ITR0), ADC
   trigger from TIM1 for all four ADCs.
3. EESM data: field current, resistance and inductance → shunt value, PGA gain,
   de-excitation time (≈ L_f·I_f/V_dc).
4. Brake resistor value and power → shunt power (the leg B shunt carries the
   chopper current).
5. Ground offset between the boards for the millivolt Kelvin signals. If it is
   too large, put an amplifier (e.g. INA240) on the power board instead.
