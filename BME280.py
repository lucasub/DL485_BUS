# Device BE280

def BME280_value(value):
    """
    From bytes to value Temp, Hum, Press of BME280
    """
    bmeValue = value
    pres_raw = (bmeValue[0] << 12) | (bmeValue[1] << 4) | (bmeValue[2] >> 4)
    temp_raw = (bmeValue[3] << 12) | (bmeValue[4] << 4) | (bmeValue[5] >> 4)
    hum_raw  = (bmeValue[6] << 8)  |  bmeValue[7]
    tot = [temp_raw, hum_raw, pres_raw]
    # print("Termperatura BME280 ==>>", t, pressure, hh, tot)
    return tot