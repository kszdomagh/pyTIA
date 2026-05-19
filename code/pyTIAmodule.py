"""
FEEDBACK TIA PYTHON MODULE
"""
import numpy as np
import matplotlib.pyplot as plt

def Ao_db_to_lin(Ao_lin):
    "changes db gain to linear gain"
    return 10**(Ao_lin / 20)

def generate_f_vector(fmin, fmax, decpoints):
    "generates freq (Hz) and laplace (rad/s) vectors."
    
    num_decades = np.log10(fmax) - np.log10(fmin)
    num_points = max(int(num_decades * decpoints), 2)
    
    # Generate vectors
    f = np.logspace(np.log10(fmin), np.log10(fmax), num_points)
    s = 1j * 2 * np.pi * f
    
    return f, s

def generate_e_series_bases(series_count):
    "generates bases according to a capacitor series"
    steps = np.arange(series_count)
    bases = 10**(steps / series_count)

    sig_figs = 2 if series_count <= 24 else 3
    
    rounded = [round(b, sig_figs - int(np.floor(np.log10(b))) - 1) for b in bases]
    
    return np.unique(rounded)

def generate_capacitors(eseries_base, mincap, maxcap):
    "generates caps according to a known series in Farads"
    capacitors = []
    # 1fF (10e-15) to 100uF (10e-4)
    for exponent in range(-15, -4):
        multiplier = 10**exponent
        for base in eseries_base:
            val = base * multiplier
            if mincap <= val <= maxcap:
                capacitors.append(val)
                
    return np.unique(capacitors)


def loopgain_plots_plot(f, mag_dB_a, phase_deg_a, f0_a, Ao, GBW, Cs, Rf, Cf):
    "plots loop gain plots"
    
    plt.figure(figsize=(8,6))
    
    plt.suptitle(
    f"Stability Analysis: OA-based TIA\n"
    f"Ao: {Ao:.1e} V/V | GBW: {GBW:.1e} Hz\n"
    f"Rf: {Rf}Ω | Cin: {Cs}F | Cf: {Cf}F", 
    fontsize=14
    )
    
    # Plot 1: Loop gain plot
    plt.subplot(2,1,1)
    plt.axvline(f0_a, color='grey', linestyle='--')
    plt.axhline(0, color='grey', linestyle='-')
    plt.semilogx(f, mag_dB_a, label='Loop gain after compensation')
    plt.xlim(min(f), max(f))
    plt.ylim(-100, 150)
    plt.grid(True, which='both', ls='--')
    plt.ylabel('Loop Gain [dB]')
    plt.legend()
    
    # Plot 2: Phase plot
    plt.subplot(2,1,2)
    plt.axvline(f0_a, color='grey', linestyle='--')
    plt.axhline(-180, color='grey', linestyle='-')
    plt.semilogx(f, phase_deg_a, color='tab:red', label='Phase after compensation')
    plt.yticks(range(-200, 1, 20))
    plt.ylim(-200, 0)
    
    plt.xlim(min(f), max(f))
    plt.grid(True, which='both', ls='--')
    plt.ylabel('Phase [deg]')
    plt.xlabel('Frequency [Hz]')
    plt.tight_layout()
    plt.show()

def loopgain_before_comp(f, s, Ao, GBW, Cs, Rf):
    "Returns gain, phase and p/z locations before compensation"
    # Note: Cf is typically 0 or paracitic here
    AB_b = Ao / ((1 + s*Rf*Cs) * (1 + s*Ao/(2*np.pi*GBW)))
    mag_dB_b = 20 * np.log10(np.abs(AB_b))
    phase_deg_b = np.angle(AB_b, deg=True)
    
    p0_b = 1 / (2 * np.pi * Rf * Cs)
    p1_b = GBW / Ao
    return mag_dB_b, phase_deg_b, p0_b, p1_b

def loopgain_after_comp(f, s, Ao, GBW, Cs, Rf, Cf):
    "Returns gain, phase and p/z locations after compensation"
    AB_a = (Ao * (1 + s*Rf*Cf)) / ((1 + s*Ao/(GBW*2*np.pi)) * (1 + s*Rf*(Cs + Cf)))
    mag_dB_a = 20 * np.log10(np.abs(AB_a))
    phase_deg_a = np.angle(AB_a, deg=True)
    
    p0_a = 1 / (2 * np.pi * Rf *(Cs + Cf))
    p1_a = GBW / Ao
    z0_a = 1/ (2 * np.pi * Rf * Cf)
    return mag_dB_a, phase_deg_a, p0_a, p1_a, z0_a

def PM_calc(f, mag_dB, phase_deg):
    "calculates PM and returns PM and 0db cross point"
    idx_0dB = np.argmin(np.abs(mag_dB))
    f0 = f[idx_0dB]
    PM = 180 + phase_deg[idx_0dB]
    return PM, f0

def find_best_Cf(f, s, Ao, GBW, Cs, Rf_arr, Cf_arr, target_PM=60):
    results = {}
    Cf_arr.sort()

    for Rf_val in Rf_arr:
        print(f"\nrunning for {Rf_val} ohms")
        
        low_id = 0
        high_id = len(Cf_arr) - 1
        Cf_best = None
        best_pm = None
        final_mag, final_phase, final_f0 = None, None, None
        
        while low_id <= high_id:
            mid_id = (low_id + high_id) // 2
            test_cf = Cf_arr[mid_id]
            
            mag, phase, _, _, _ = loopgain_after_comp(f, s, Ao, GBW, Cs, Rf_val, test_cf)
            current_pm, f0 = PM_calc(f, mag, phase)
            
            if current_pm < target_PM:
                print(f"for {test_cf*1e12:.2f}pF PM={current_pm:.2f} -> UP")
                low_id = mid_id + 1
            else:
                print(f"for {test_cf*1e12:.2f}pF PM={current_pm:.2f} -> DOWN")
                Cf_best = test_cf
                best_pm = current_pm 
                final_mag, final_phase, final_f0 = mag, phase, f0
                high_id = mid_id - 1
                
        results[Rf_val] = Cf_best
        
        if Cf_best is not None:
            loopgain_plots_plot(f, final_mag, final_phase, final_f0, Ao, GBW, Cs, Rf_val, Cf_best)
            print(f"BEST: \nRf: {Rf_val} ohms   Cf: {Cf_best*1e12:.2f} pF   PM: {best_pm}deg")
        else:
            print(f"ERROR:\nno cap in range met the target PM for Rf={Rf_val}")

    return results