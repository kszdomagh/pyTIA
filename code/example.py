import pyTIAmodule as tia

# OA parameters
Ao_db = 115
GBW = 20e6

# photodiode parameters
Cs = 35e-9

# feedback parameters
Rf_arr = [20_000] # ohm
Cf_min = 470e-15  # 470fF
Cf_max = 10e-6  # 10uF

# change dB to lin gain
Ao_lin = tia.Ao_db_to_lin(Ao_db)

# generate capacitors based on the available series
# cap series: E3(20%) E6(20%) E12(10%) E24(5%) E48(2%) E96 (1%) E192(±0.5%, ±0.25%, ±0.1%)
e96_base = tia.generate_e_series_bases(96)
Cf_list = tia.generate_capacitors(e96_base, Cf_min, Cf_max)

f, s = tia.generate_f_vector(fmin=1, fmax=1e9, decpoints=20) # 1Hz to 1GHz
tia.find_best_Cf(f, s, Ao_lin, GBW, Cs, Rf_arr, Cf_list, target_PM=60)