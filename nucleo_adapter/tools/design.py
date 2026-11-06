"""Netlist of the Nucleo adapter: NUCLEO-H743ZI to the legacy 4850 power board.

Pin map of the firmware: unimoc branch hardware/first-startup,
app/boards/nucleo_h743zi.overlay.  Power-board connector pinout: the as-ordered
power board (production/legacy_kicad5/power, KiCad 5 PCB of 2019-11-20).
"""

POWER_NETS = {'GND', 'GNDA', '+3V3', '+3.3VA', '+5V', '+12V', '+BATT'}
GROUNDS = {'GND', 'GNDA'}
NC = None  # pin gets a no-connect flag

R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C1206 = 'Capacitor_SMD:C_1206_3216Metric'
FB0603 = 'Inductor_SMD:L_0603_1608Metric'


def R(ref, val, a, b, fp=R0603, **kw):
    return dict(ref=ref, lib='Device:R', value=val, fp=fp, pins={'1': a, '2': b}, **kw)


def C(ref, val, a, b, fp=C0603, **kw):
    return dict(ref=ref, lib='Device:C', value=val, fp=fp, pins={'1': a, '2': b}, **kw)


SHEETS = []


def sheet(name, title, notes, parts, paper='A4', portrait=False):
    SHEETS.append(dict(name=name, title=title, notes=notes, parts=parts, portrait=portrait))


# ---------------------------------------------------------------- power board
sheet('power_board', 'Power board connectors and mounting holes', [
    'Power board connectors and mounting holes',
    'Mates with the legacy 4850 power board (as ordered 2019-11-20, production/legacy_kicad5/power).',
    'J101 and J102 are SMD pin headers on the bottom side; they plug into the power-board sockets',
    'J103 (PWM) and J104 (ADC). Position, rotation and pin 1 copied from the old logic board.',
    'H101-H103 line up with power-board holes H105, H104, H107 (standoffs). Do not move them.',
    'J101 pin 3 is open on the power board. J102 pin 10 is the low side of the bridge NTC TH101.',
    'INA240A1 on the power board: V+ and REF2 on +3.3VA, REF1 on GND, so I_x = 1.65 V + 20 mV/A',
    '(2 x 2 mOhm shunts per phase, about +-80 A full scale).',
], [
    dict(ref='J101', lib='Connector_Generic:Conn_02x05_Odd_Even', value='PWM',
         fp='Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical_SMD',
         pins={'1': '+BATT', '2': 'GND', '3': NC, '4': 'PWM_AH', '5': '+12V',
               '6': 'PWM_AL', '7': 'PWM_CL', '8': 'PWM_BH', '9': 'PWM_CH', '10': 'PWM_BL'}),
    dict(ref='J102', lib='Connector_Generic:Conn_02x05_Odd_Even', value='ADC',
         fp='Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical_SMD',
         pins={'1': '+3.3VA', '2': 'I_C', '3': 'GNDA', '4': 'I_B', '5': 'GNDA',
               '6': 'I_A', '7': 'GNDA', '8': 'T_BRIDGE', '9': 'GNDA', '10': 'GNDA'}),
    dict(ref='H101', lib='Mechanical:MountingHole_Pad', value='M3',
         fp='MountingHole:MountingHole_3.2mm_M3_Pad_Via', pins={'1': 'GND'}),
    dict(ref='H102', lib='Mechanical:MountingHole_Pad', value='M3',
         fp='MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad', pins={'1': 'GND'}),
    dict(ref='H103', lib='Mechanical:MountingHole_Pad', value='M3',
         fp='MountingHole:MountingHole_3.2mm_M3_ISO14580_Pad', pins={'1': 'GND'}),
    dict(ref='#FLG101', lib='power:PWR_FLAG', value='PWR_FLAG', fp='', pins={'1': '+BATT'}),
])

# ---------------------------------------------------------------- nucleo
NUCLEO_MAP = {
    'PE9': 'TIM1_CH1', 'PE8': 'TIM1_CH1N', 'PE11': 'TIM1_CH2', 'PE10': 'TIM1_CH2N',
    'PE13': 'TIM1_CH3', 'PE12': 'TIM1_CH3N', 'PE15': 'TIM1_BKIN',
    'PA6': 'ADC_IA', 'PB1': 'ADC_IB', 'PC2': 'ADC_IC', 'PC3': 'ADC_VDC',
    'PF11': 'ADC_VA', 'PF13': 'ADC_VB', 'PF10': 'ADC_VC',
    'PF12': 'ADC_TBRIDGE', 'PF14': 'ADC_TMOTOR',
    'PD12': 'HALL_A', 'PD13': 'HALL_B', 'PD14': 'HALL_C',
    'PD0': 'CAN_RX', 'PD1': 'CAN_TX',
    '+3V3': '+3V3', '+5V': '+5V', 'GND': 'GND', 'AGND': 'GND',
}
sheet('nucleo', 'NUCLEO-H743ZI', [
    'NUCLEO-H743ZI (MB1137, rev. Y)',
    'Plugs into two 2 x 36 morpho sockets (CN11, CN12)',
    'on the top side. Pin map: unimoc',
    'app/boards/nucleo_h743zi.overlay (hardware/first-startup).',
    'PC2/PC3 are PC2_C/PC3_C on the H743 (ADC3 direct pads).',
    'Powered from the ST-LINK USB. Its +3V3 (= VDDA, the ADC',
    'reference) also feeds +3.3VA through FB601 (sheet supply).',
    'AGND is GND on the Nucleo, so it goes to GND here;',
    'the only GND-GNDA tie is FB602.',
], [
    dict(ref='U201', lib='MCU_Module:NUCLEO144-H743ZI', value='NUCLEO-H743ZI',
         fp='Module:ST_Morpho_Connector_144_STLink_MountingHoles', pins='nucleo'),
], portrait=True)

# ---------------------------------------------------------------- analog
an = []
for k, ph in enumerate('ABC'):
    an += [R(f'R30{k + 1}', '220R', f'I_{ph}', f'ADC_I{ph}', br=(k == 0)),
           C(f'C30{k + 1}', '2n2', f'ADC_I{ph}', 'GNDA')]
an += [
    R('R304', '10k', '+3.3VA', 'T_BRIDGE', br=True),
    R('R305', '1k', 'T_BRIDGE', 'ADC_TBRIDGE'),
    C('C304', '100n', 'ADC_TBRIDGE', 'GNDA'),
    dict(ref='J301', lib='Connector_Generic:Conn_01x02', value='MOT_TEMP',
         fp='Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical',
         pins={'1': 'T_MOTOR', '2': 'GNDA'}),
    R('R306', '10k', '+3.3VA', 'T_MOTOR'),
    R('R307', '1k', 'T_MOTOR', 'ADC_TMOTOR'),
    C('C305', '100n', 'ADC_TMOTOR', 'GNDA'),
]
sheet('analog', 'Current and temperature sensing', [
    'Current and temperature sensing',
    'Phase currents: the INA240 outputs (0..3.3 V) need no scaling; 220R / 2n2 RC (330 kHz) as',
    'anti-alias filter and charge reservoir for the 2.5-cycle ADC sample time. First guess.',
    'NTCs (bridge TH101 on the power board, motor on J301): 10k pull-up to +3.3VA, 1k / 100n.',
], an)

vs = [
    R('R308', '47k 0.1%', '+BATT', 'ADC_VDC', br=False),
    R('R309', '2k2 0.1%', 'ADC_VDC', 'GNDA'),
    C('C306', '1n', 'ADC_VDC', 'GNDA'),
    dict(br=True, ref='J302', lib='Connector_Generic:Conn_01x03', value='VPHASE',
         fp='Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical',
         pins={'1': 'V_A', '2': 'V_B', '3': 'V_C'}),
]
for k, ph in enumerate('ABC'):
    vs += [R(f'R3{10 + 2 * k}', '47k 0.1%', f'V_{ph}', f'ADC_V{ph}', br=(k == 0)),
           R(f'R3{11 + 2 * k}', '2k2 0.1%', f'ADC_V{ph}', 'GNDA'),
           C(f'C30{7 + k}', '1n', f'ADC_V{ph}', 'GNDA')]
sheet('voltage', 'Voltage sensing', [
    'Voltage sensing',
    'Vdc and the phase voltages: 47k / 2k2 0.1 % (73.8 V full scale, as on Jacobi), 1n.',
    'The legacy power board has no phase-voltage taps: J302 takes three wires from the',
    'phase solder pads J106-J108 (optional, for identification I3).',
], vs)

# ---------------------------------------------------------------- gate interface
gate = []
for k, (mcu, pwr) in enumerate([('TIM1_CH1', 'PWM_AH'), ('TIM1_CH1N', 'PWM_AL'),
                                 ('TIM1_CH2', 'PWM_BH'), ('TIM1_CH2N', 'PWM_BL'),
                                 ('TIM1_CH3', 'PWM_CH'), ('TIM1_CH3N', 'PWM_CL')]):
    gate += [R(f'R4{k + 1:02d}', '100R', mcu, pwr, br=(k % 3 == 0)), R(f'R4{k + 11:02d}', '10k', pwr, 'GND')]
gate += [
    dict(br=True, ref='J401', lib='Connector_Generic:Conn_01x02', value='ENABLE',
         fp='Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical',
         pins={'1': 'EN_SUPPLY', '2': 'EN_IN'}),
    R('R421', '1k', '+3V3', 'EN_SUPPLY'),
    R('R422', '10k', 'EN_IN', 'GND'),
    R('R423', '1k', 'EN_IN', 'TIM1_BKIN'),
    C('C401', '10n', 'TIM1_BKIN', 'GND'),
]
sheet('gate', 'Gate driver interface and enable', [
    'Gate driver interface and enable',
    'TIM1 CH1..CH3 / CH1N..CH3N drive the LM5109B inputs HI/LI on the power board (TTL',
    'thresholds, 3.3 V logic is enough: check VIH in the datasheet). 100R series near the',
    'Nucleo, 10k pull-down near J101: the gates stay off while the MCU is in reset.',
    'ENABLE (J401): close the loop (switch or E-stop) to release TIM1_BKIN (PE15, active low).',
    'Open loop = break, all six outputs off. Matches the firmware (pull-down on PE15).',
], gate)

# ---------------------------------------------------------------- interfaces
itf = [
    dict(ref='U501', lib='Interface_CAN_LIN:TCAN334', value='TCAN334D',
         fp='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
         pins={'1': 'CAN_TX', '2': 'GND', '3': '+3V3', '4': 'CAN_RX', '5': 'CAN_SHDN',
               '6': 'CAN_L', '7': 'CAN_H', '8': 'CAN_STB'}),
    C('C501', '100n', '+3V3', 'GND'),
    R('R501', '10k', 'CAN_SHDN', 'GND'),
    R('R502', '10k', 'CAN_STB', 'GND'),
    R('R503', '120R', 'CAN_H', 'CAN_TERM'),
    dict(ref='JP501', lib='Jumper:SolderJumper_2_Open', value='TERM',
         fp='Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
         pins={'1': 'CAN_TERM', '2': 'CAN_L'}),
]
for k in range(2):
    itf.append(dict(ref=f'J50{k + 1}', lib='Connector_Generic_MountingPin:Conn_01x04_MountingPin',
                    value='CAN', fp='Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal',
                    pins={'1': NC, '2': 'CAN_H', '3': 'CAN_L', '4': 'GND', 'MP': 'GND'}))
itf.append(dict(br=True, ref='J503', lib='Connector_Generic:Conn_01x05', value='HALL',
                fp='Connector_JST:JST_PH_B5B-PH-K_1x05_P2.00mm_Vertical',
                pins={'1': '+5V', '2': 'HALL_A_IN', '3': 'HALL_B_IN', '4': 'HALL_C_IN', '5': 'GND'}))
itf.append(dict(ref='#FLG501', lib='power:PWR_FLAG', value='PWR_FLAG', fp='', pins={'1': '+5V'}))
for k, h in enumerate('ABC'):
    itf += [R(f'R5{11 + k}', '2k2', '+3V3', f'HALL_{h}_IN', br=(k == 0)),
            R(f'R5{21 + k}', '1k', f'HALL_{h}_IN', f'HALL_{h}'),
            C(f'C5{11 + k}', '1n', f'HALL_{h}', 'GND')]
sheet('interfaces', 'CAN FD and Hall sensors', [
    'CAN FD and Hall sensors',
    'TCAN334 (CAN FD, 3.3 V) on FDCAN1 (PD0 RX, PD1 TX). SHDN and STB pulled low: always on.',
    'J501/J502: Cyphal/UAVCAN micro connector (JST GH 4): 1 +5V (not connected here),',
    '2 CAN_H, 3 CAN_L, 4 GND. Close JP501 for the 120R termination at a bus end.',
    'HALL (J503, JST PH 5): open-collector sensors on +5V, 2k2 pull-ups to +3V3, 1k / 1n RC.',
    'PD12..PD14 are 5 V tolerant.',
], itf)

# ---------------------------------------------------------------- supply
sup = [
    dict(ref='J601', lib='Connector_Generic:Conn_01x02', value='12V_IN',
         fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal',
         pins={'1': '+12V_IN', '2': 'GND'}),
    dict(ref='D601', lib='Device:D_Schottky', value='SS34', fp='Diode_SMD:D_SMA',
         pins={'1': '+12V', '2': '+12V_IN'}, rot=180),
    dict(ref='D602', lib='Device:D_TVS', value='SMAJ15CA', fp='Diode_SMD:D_SMA',
         pins={'1': '+12V', '2': 'GND'}),
    C('C601', '22u 25V', '+12V', 'GND', fp=C1206),
    C('C602', '100n', '+12V', 'GND'),
    R('R601', '4k7', '+12V', 'LED_12V'),
    dict(ref='D603', lib='Device:LED', value='green', fp='LED_SMD:LED_0603_1608Metric',
         pins={'1': 'GND', '2': 'LED_12V'}, rot=90),
    dict(br=True, ref='FB601', lib='Device:FerriteBead_Small', value='BLM18PG221', fp=FB0603,
         pins={'1': '+3V3', '2': '+3.3VA'}),
    C('C603', '10u', '+3.3VA', 'GNDA'),
    C('C604', '100n', '+3.3VA', 'GNDA'),
    dict(ref='FB602', lib='Device:FerriteBead_Small', value='BLM18PG221', fp=FB0603,
         pins={'1': 'GND', '2': 'GNDA'}),
]
for k, net in enumerate(['+12V', '+3V3', '+3.3VA', 'GND', 'GNDA']):
    sup.append(dict(ref=f'#FLG60{k + 1}', lib='power:PWR_FLAG', value='PWR_FLAG', fp='',
                    pins={'1': net}, br=(k == 0)))
sheet('supply', 'Supplies', [
    'Supplies',
    '+12V: gate driver supply of the power board (LM5109B VDD, 8..14 V) from a bench supply on',
    'J601, not from the DC link: the first power-on runs the DC link at 12 V / 0.5 A.',
    'SS34 against reverse polarity, SMAJ15CA clamp. About 20 mA for the gate charge at 32 kHz.',
    '+3.3VA: INA240 supply, NTC pull-ups. From the Nucleo +3V3 (the ADC reference, VDDA)',
    'through FB601, so the INA240 offset (Vs/2) tracks the ADC reference.',
    'GND (Nucleo, J101 pin 2 = GNDPWR) and GNDA (J102 = INA240 ground) meet only at FB602,',
    'as FB502 on the old logic board; the power board does not join them.',
], sup)
