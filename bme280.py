"""
Module to return BME280 T + H + P
"""

from pprint import pprint

class BME280:
    # Device BME280 - Temperature + Humidity + Pression

    BME = {}

    def byteLSMS2uint(self, byteLS, byteMS):
        """
        Dati 2 byte (LS e MS) ritorna 1 WORD senza segno
        """
        return byteLS + (byteMS * 256)

    def byteLSMS2int(self, byteLS, byteMS):
        """
        Dati 2 byte (LS e MS) ritorna 1 WORD con segno
        """
        if byteMS > 127:
            return -32768 + (byteLS + ((byteMS - 128) * 256))
        return self.byteLSMS2uint(byteLS, byteMS)
        # return byteLS + (byteMS * 256)

    def byte2signed(self, byte):
        """
        Ritorna Byte con segno
        """
        if byte > 127:
            return -128 + byte
        return byte

    def getRawValueBME280(self, value):
        """
        From bytes to value Temp, Hum, Press of BME280
        """
        if len(value) < 5:
            return
        bmeValue = value
        pres_raw = (bmeValue[0] << 12) | (bmeValue[1] << 4) | (bmeValue[2] >> 4)
        temp_raw = (bmeValue[3] << 12) | (bmeValue[4] << 4) | (bmeValue[5] >> 4)
        hum_raw = (bmeValue[6] << 8) | bmeValue[7]
        tot = [temp_raw, hum_raw, pres_raw]
        # print("Termperatura BME280 ==>>", t, pressure, hh, tot)
        return tot

    def calibBME(self, board_id, logic_io, value):
        bme_key = '{}-{}'.format(board_id, logic_io)
        if bme_key not in self.BME:
            self.BME[bme_key] = {}

        # print("---", board_id, logic_io, value)
        if len(value) == 26:  # value from 0x88 to 0xA1
            flag_ok = True

            if self.BME[bme_key].get('dig_T1') != self.byteLSMS2uint(value[0], value[1]):
                flag_ok = False
                self.BME[bme_key]['dig_T1'] = self.byteLSMS2uint(value[0], value[1])  # 0x88

            if self.BME[bme_key].get('dig_T2') != self.byteLSMS2int(value[2], value[3]):
                flag_ok = False
                self.BME[bme_key]['dig_T2'] = self.byteLSMS2int(value[2], value[3])  # 0x8A

            if self.BME[bme_key].get('dig_T3') != self.byteLSMS2int(value[4], value[5]):
                flag_ok = False
                self.BME[bme_key]['dig_T3'] = self.byteLSMS2int(value[4], value[5])  # 0x8C

            if self.BME[bme_key].get('dig_P1') != self.byteLSMS2uint(value[6], value[7]):  # 0x8E:
                flag_ok = False
                self.BME[bme_key]['dig_P1'] = self.byteLSMS2uint(value[6], value[7])  # 0x8E

            if self.BME[bme_key].get('dig_P2') != self.byteLSMS2int(value[8], value[9]):  # 0x90
                flag_ok = False
                self.BME[bme_key]['dig_P2'] = self.byteLSMS2int(value[8], value[9])  # 0x90

            if self.BME[bme_key].get('dig_P3') != self.byteLSMS2int(value[10], value[11]):  # 0x92
                flag_ok = False
                self.BME[bme_key]['dig_P3'] = self.byteLSMS2int(value[10], value[11])  # 0x92

            if self.BME[bme_key].get('dig_P4') != self.byteLSMS2int(value[12], value[13]):  # 0x94
                flag_ok = False
                self.BME[bme_key]['dig_P4'] = self.byteLSMS2int(value[12], value[13])  # 0x94

            if self.BME[bme_key].get('dig_P5') != self.byteLSMS2int(value[14], value[15]):  # 0x96
                flag_ok = False
                self.BME[bme_key]['dig_P5'] = self.byteLSMS2int(value[14], value[15])  # 0x96

            if self.BME[bme_key].get('dig_P6') != self.byteLSMS2int(value[16], value[17]):  # 0x98
                flag_ok = False
                self.BME[bme_key]['dig_P6'] = self.byteLSMS2int(value[16], value[17])  # 0x98

            if self.BME[bme_key].get('dig_P7') != self.byteLSMS2int(value[18], value[19]):  # 0x9A
                flag_ok = False
                self.BME[bme_key]['dig_P7'] = self.byteLSMS2int(value[18], value[19])  # 0x9A

            if self.BME[bme_key].get('dig_P8') != self.byteLSMS2int(value[20], value[21]):  # 0x9C
                flag_ok = False
                self.BME[bme_key]['dig_P8'] = self.byteLSMS2int(value[20], value[21])  # 0x9C

            if self.BME[bme_key].get('dig_P9') != self.byteLSMS2int(value[22], value[23]):  # 0x9E
                flag_ok = False
                self.BME[bme_key]['dig_P9'] = self.byteLSMS2int(value[22], value[23])  # 0x9E

            if self.BME[bme_key].get('dig_H1') != value[25]:  # 0xA1
                flag_ok = False
                self.BME[bme_key]['dig_H1'] = value[25]  # 0xA1

            self.BME[bme_key]['flag26'] = flag_ok

        if len(value) == 7:  # value from 0xE1 to 0xE7

            flag_ok = True
            if self.BME[bme_key].get('dig_H2') != self.byteLSMS2int(value[0], value[1]):  # 0xE1:
                flag_ok = False
                self.BME[bme_key]['dig_H2'] = self.byteLSMS2int(value[0], value[1])  # 0xE1

            if self.BME[bme_key].get('dig_H3') != value[2]:  # 0xE3:
                flag_ok = False
                self.BME[bme_key]['dig_H3'] = value[2]  # 0xE3

            h4 = self.byte2signed(value[3])
            h4 = h4 << 4

            if self.BME[bme_key].get('dig_H4') != h4 | (value[4] & 0x0f):
                flag_ok = False
                self.BME[bme_key]['dig_H4'] = h4 | (value[4] & 0x0f)
            h5 = self.byte2signed(value[5])  # 0xE6

            if self.BME[bme_key].get('dig_H5') != (h5 << 4) | ((value[4] >> 4) & 0x0f):
                flag_ok = False
                self.BME[bme_key]['dig_H5'] = (h5 << 4) | ((value[4] >> 4) & 0x0f)

            if self.BME[bme_key].get('dig_H5') != ((value[4] >> 4) & 0x0F) | (value[5] << 4):
                flag_ok = False
                self.BME[bme_key]['dig_H5'] = ((value[4] >> 4) & 0x0F) | (value[5] << 4)

            if self.BME[bme_key].get('dig_H6') != self.byte2signed(value[6]):  # 0xE7
                flag_ok = False
                self.BME[bme_key]['dig_H6'] = self.byte2signed(value[6])  # 0xE7

            self.BME[bme_key]['flag7'] = flag_ok

        # pprint(self.BME)

    def valueBME280(self, board_id, logic_io, logic_io_calibration, T_Raw, H_Raw, P_Raw):
        # print(board_id, logic_io, logic_io_calibration, T_Raw, H_Raw, P_Raw)
        bme_key = '{}-{}'.format(board_id, logic_io_calibration)


        if (bme_key in self.BME) and self.BME[bme_key].get('flag26') and self.BME[bme_key].get('flag7'):

            v1 = (T_Raw / 16384.0 - self.BME[bme_key]['dig_T1'] / 1024.0) * self.BME[bme_key]['dig_T2']
            v2 = ((T_Raw / 131072.0 - self.BME[bme_key]['dig_T1'] / 8192.0) ** 2) * self.BME[bme_key]['dig_T3']
            T_fine = (v1 + v2)
            T = T_fine / 5120.0

            H = T_fine - 76800.0
            H = (H_Raw - (self.BME[bme_key]['dig_H4'] * 64.0 + self.BME[bme_key]['dig_H5'] / 16384.0 * H)) * \
                (self.BME[bme_key]['dig_H2'] / 65536.0 * (1.0 + self.BME[bme_key]['dig_H6'] / 67108864.0 * H *
                                                          (1.0 + self.BME[bme_key]['dig_H3'] / 67108864.0 * H)))
            H = H * (1.0 - (self.BME[bme_key]['dig_H1'] * H / 524288.0))

            v1 = T_fine / 2.0 - 64000.0
            v2 = v1 * v1 * self.BME[bme_key]['dig_P6'] / 32768.0
            v2 = v2 + v1 * self.BME[bme_key]['dig_P5'] * 2.0
            v2 = v2 / 4.0 + self.BME[bme_key]['dig_P4'] * 65536.0
            v1 = (self.BME[bme_key]['dig_P3'] * v1 * v1 / 524288.0 + self.BME[bme_key]['dig_P2'] * v1) / 524288.0
            v1 = (1.0 + v1 / 32768.0) * self.BME[bme_key]['dig_P1']

            # Prevent divide by zero
            if v1 == 0:
                P = 0

            res = 1048576.0 - P_Raw
            res = ((res - v2 / 4096.0) * 6250.0) / v1
            v1 = self.BME[bme_key]['dig_P9'] * res * res / 2147483648.0
            v2 = res * self.BME[bme_key]['dig_P8'] / 32768.0
            P = (res + (v1 + v2 + self.BME[bme_key]['dig_P7']) / 16.0) / 100

        else:
            return None

        return [T, H, P]


if __name__ == '__main__':
    """ TEST BME280 """

    """
        [1, 14, 8, ....
        1 = board_id
        8 = logic_io
        other = sensor value
    """

    bme_val = [1, 14, 8, 77, 223, 128, 124, 47, 160, 137, 160]  # Calibration list
    bme_calib1 = [1, 14, 9, 128, 108, 163, 101, 50, 0, 73, 144, 205, 213, 208, 11, 65, 32, 169, 255, 249, 255, 172, 38, 10, 216, 189, 16, 0, 75]  # Calibration list
    bme_calib2 = [1, 14, 9, 90, 1, 0, 22, 6, 0, 30]  # Data

    board_id = bme_calib1[0]
    logic_io = bme_calib1[2]

    b = BME280()
    valRaw = b.getRawValueBME280(bme_val[3:])
    print(valRaw)
    print( bme_calib2[3:])

    b.calibBME(board_id, logic_io, bme_calib2[3:])
    b.calibBME(board_id, logic_io, bme_calib1[3:])
    b.calibBME(board_id, logic_io, bme_calib2[3:])
    b.calibBME(board_id, logic_io, bme_calib1[3:])

    T, H, P = b.valueBME280(board_id, logic_io, 9, valRaw[0], valRaw[1], valRaw[2])
    print(f"T:{T} H:{H} P:{P}")